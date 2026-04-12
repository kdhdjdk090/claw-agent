/**
 * Claw Agent — Content Script
 * Runs on every page. Extracts page content and executes actions on behalf of the agent.
 */

(function () {
  // Versioned guard — allows re-injection after extension reload
  const CLAW_VERSION = 2;
  if (window.__clawAgentVersion === CLAW_VERSION) return;
  // Remove old listener from previous version if re-injecting
  if (window.__clawAgentListener) {
    try { chrome.runtime.onMessage.removeListener(window.__clawAgentListener); } catch {}
  }
  window.__clawAgentVersion = CLAW_VERSION;

  function messageHandler(message, sender, sendResponse) {
    if (message.type === "extract-content") {
      sendResponse(extractPageContent());
      return;
    }

    if (message.type === "execute-on-page") {
      const result = executeAction(message.action, message.params);
      sendResponse(result);
      return;
    }

    if (message.type === "extract-selection") {
      const sel = window.getSelection()?.toString() || "";
      sendResponse({ selection: sel });
      return;
    }

    if (message.type === "extract-links") {
      const links = Array.from(document.querySelectorAll("a[href]"))
        .slice(0, 200)
        .map((a) => ({ text: a.textContent?.trim().substring(0, 100) || "", href: a.href }))
        .filter((l) => l.href && !l.href.startsWith("javascript:"));
      sendResponse({ links });
      return;
    }

    if (message.type === "extract-images") {
      const images = Array.from(document.querySelectorAll("img[src]"))
        .slice(0, 50)
        .map((img) => ({ src: img.src, alt: img.alt || "" }));
      sendResponse({ images });
      return;
    }

    if (message.type === "extract-forms") {
      const forms = Array.from(document.querySelectorAll("form")).slice(0, 20).map((form, i) => {
        const inputs = Array.from(form.querySelectorAll("input, textarea, select, [contenteditable='true'], [contenteditable=''], [role='textbox'], [role='combobox']")).map((el) => ({
          type: el.type || (el.isContentEditable ? "contenteditable" : el.tagName.toLowerCase()),
          name: el.name || "",
          id: el.id || "",
          placeholder: el.placeholder || el.getAttribute("data-placeholder") || el.getAttribute("aria-label") || "",
          value: (el.value || el.textContent || "")?.substring(0, 50) || "",
          contenteditable: el.isContentEditable || false,
        }));
        return { index: i, action: form.action || "", method: form.method || "GET", inputs };
      });
      // Also find standalone editable fields not inside a <form> (common in SPAs)
      const standaloneInputs = Array.from(document.querySelectorAll(
        "input:not(form input), textarea:not(form textarea), [contenteditable='true']:not(form [contenteditable]), [role='textbox']:not(form [role='textbox'])"
      )).slice(0, 30).map(el => ({
        type: el.type || (el.isContentEditable ? "contenteditable" : el.tagName.toLowerCase()),
        name: el.name || "",
        id: el.id || "",
        placeholder: el.placeholder || el.getAttribute("data-placeholder") || el.getAttribute("aria-label") || "",
        value: (el.value || el.textContent || "")?.substring(0, 50) || "",
        contenteditable: el.isContentEditable || false,
        selector: el.id ? "#" + CSS.escape(el.id) : (el.getAttribute("aria-label") ? `[aria-label="${CSS.escape(el.getAttribute("aria-label"))}"]` : el.tagName.toLowerCase()),
      }));
      sendResponse({ forms, standaloneInputs, hint: standaloneInputs.length > 0 ? `Found ${standaloneInputs.length} input fields outside of <form> elements (common in SPAs like Google Ads). Use their selectors with fill_input or type_text.` : "" });
      return;
    }

    if (message.type === "extract-code") {
      const codeBlocks = Array.from(document.querySelectorAll("pre, code")).slice(0, 30).map((el) => ({
        tag: el.tagName.toLowerCase(),
        text: el.textContent?.substring(0, 2000) || "",
        lang: el.className?.match(/language-(\w+)/)?.[1] || "",
      }));
      sendResponse({ codeBlocks });
      return;
    }

    if (message.type === "click-element") {
      try {
        const el = findElement(message.selector);
        if (el) {
          el.click();
          sendResponse({ success: true });
        } else {
          sendResponse({ error: `Element not found: ${message.selector}` });
        }
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    if (message.type === "fill-input") {
      try {
        const el = findElement(message.selector);
        if (el) {
          const isContentEditable = el.isContentEditable || el.getAttribute("contenteditable") === "true" || el.getAttribute("contenteditable") === "";
          if (isContentEditable) {
            // Route contenteditable to typeText for better SPA compatibility
            typeText(message.selector, message.value || "", true).then(sendResponse);
            return true; // async
          }
          el.value = message.value || "";
          el.dispatchEvent(new Event("input", { bubbles: true }));
          el.dispatchEvent(new Event("change", { bubbles: true }));
          sendResponse({ success: true });
        } else {
          sendResponse({ error: `Input not found: ${message.selector}` });
        }
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    if (message.type === "scroll-to") {
      // Detect if a modal/overlay/dialog is covering the page — scroll within it instead
      const scrollTarget = findScrollableContainer();
      if (scrollTarget && scrollTarget !== document.documentElement && scrollTarget !== document.body) {
        scrollTarget.scrollTo({ top: message.y || 0, left: message.x || 0, behavior: "smooth" });
      } else {
        window.scrollTo({ top: message.y || 0, left: message.x || 0, behavior: "smooth" });
      }
      sendResponse({ success: true, scrolledContainer: scrollTarget !== document.documentElement && scrollTarget !== document.body ? scrollTarget.tagName + (scrollTarget.className ? "." + scrollTarget.className.split(" ")[0] : "") : "window" });
      return;
    }

    // Detect the primary scrollable element (modal containers, overlay panels, etc.)
    if (message.type === "get-scroll-info") {
      const container = findScrollableContainer();
      const isModal = container && container !== document.documentElement && container !== document.body;
      const target = isModal ? container : document.documentElement;
      sendResponse({
        scrollY: Math.round(isModal ? target.scrollTop : window.scrollY),
        scrollHeight: target.scrollHeight,
        clientHeight: target.clientHeight || window.innerHeight,
        isModal,
        containerSelector: isModal ? (container.id ? "#" + container.id : container.tagName.toLowerCase() + (container.className ? "." + container.className.split(" ")[0] : "")) : null,
      });
      return;
    }

    if (message.type === "select-option") {
      try {
        const el = findElement(message.selector);
        if (!el || el.tagName !== "SELECT") {
          sendResponse({ error: `Select element not found: ${message.selector}` });
          return;
        }
        const val = message.value || "";
        let found = false;
        // Try matching by value first, then by text
        for (const opt of el.options) {
          if (opt.value === val || opt.textContent.trim().toLowerCase() === val.toLowerCase()) {
            el.value = opt.value;
            found = true;
            break;
          }
        }
        if (!found) {
          // Fuzzy match — partial text
          for (const opt of el.options) {
            if (opt.textContent.trim().toLowerCase().includes(val.toLowerCase())) {
              el.value = opt.value;
              found = true;
              break;
            }
          }
        }
        if (found) {
          el.dispatchEvent(new Event("change", { bubbles: true }));
          el.dispatchEvent(new Event("input", { bubbles: true }));
          sendResponse({ success: true, selected: el.value });
        } else {
          const options = Array.from(el.options).map(o => o.textContent.trim()).slice(0, 20);
          sendResponse({ error: `Option "${val}" not found. Available: ${options.join(", ")}` });
        }
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    if (message.type === "press-key") {
      try {
        let target = document.activeElement || document.body;
        if (message.selector) {
          const el = findElement(message.selector);
          if (el) { el.focus(); target = el; }
        }
        const key = message.key || "Enter";
        const eventInit = {
          key,
          code: key,
          bubbles: true,
          cancelable: true,
        };
        target.dispatchEvent(new KeyboardEvent("keydown", eventInit));
        target.dispatchEvent(new KeyboardEvent("keypress", eventInit));
        target.dispatchEvent(new KeyboardEvent("keyup", eventInit));
        // For Enter, also submit the form if inside one
        if (key === "Enter" && target.form) {
          target.form.requestSubmit ? target.form.requestSubmit() : target.form.submit();
        }
        sendResponse({ success: true, key, target: target.tagName });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    if (message.type === "wait-for-element") {
      const timeout = Math.min(message.timeout || 5000, 10000);
      const selector = message.selector || "";
      const startTime = Date.now();

      function check() {
        let el;
        if (selector.startsWith("text:")) {
          const text = selector.substring(5).toLowerCase();
          el = Array.from(document.querySelectorAll("*")).find(
            n => n.textContent?.toLowerCase().includes(text) && n.children.length === 0
          );
        } else {
          try { el = document.querySelector(selector); } catch {}
        }
        if (el) {
          sendResponse({ success: true, found: true, tag: el.tagName, text: el.textContent?.substring(0, 100) });
        } else if (Date.now() - startTime > timeout) {
          sendResponse({ success: false, found: false, timeout: true, message: `Element "${selector}" did not appear within ${timeout}ms. The page may have loaded without this element — try read_page or take_screenshot to see the current state.` });
        } else {
          setTimeout(check, 250);
        }
      }
      check();
      return true; // async sendResponse
    }

    if (message.type === "get-element-info") {
      try {
        const el = findElement(message.selector);
        if (!el) {
          sendResponse({ error: `Element not found: ${message.selector}` });
          return;
        }
        const rect = el.getBoundingClientRect();
        const style = window.getComputedStyle(el);
        sendResponse({
          tag: el.tagName,
          id: el.id || null,
          className: el.className || null,
          text: el.textContent?.substring(0, 500) || "",
          href: el.href || null,
          src: el.src || null,
          value: el.value || null,
          type: el.type || null,
          placeholder: el.placeholder || null,
          checked: el.checked || null,
          disabled: el.disabled || false,
          visible: style.display !== "none" && style.visibility !== "hidden" && rect.width > 0 && rect.height > 0,
          dimensions: { width: Math.round(rect.width), height: Math.round(rect.height), top: Math.round(rect.top), left: Math.round(rect.left) },
          attributes: Object.fromEntries(
            Array.from(el.attributes).slice(0, 20).map(a => [a.name, a.value.substring(0, 100)])
          ),
        });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    if (message.type === "extract-tables") {
      const tables = Array.from(document.querySelectorAll("table")).slice(0, 10).map((table, idx) => {
        const headers = Array.from(table.querySelectorAll("thead th, tr:first-child th"))
          .map(th => th.textContent?.trim().substring(0, 100) || "");
        const rows = Array.from(table.querySelectorAll("tbody tr, tr"))
          .slice(0, 50)
          .map(tr =>
            Array.from(tr.querySelectorAll("td, th"))
              .map(td => td.textContent?.trim().substring(0, 200) || "")
          )
          .filter(row => row.some(cell => cell.length > 0));
        return { index: idx, headers, rows, rowCount: rows.length };
      });
      sendResponse({ tables, count: tables.length });
      return;
    }

    // ---- Claude-style browser control features ----

    if (message.type === "show-control-banner") {
      showControlBanner(message.action || "controlling this browser");
      sendResponse({ success: true });
      return;
    }

    if (message.type === "hide-control-banner") {
      hideControlBanner();
      sendResponse({ success: true });
      return;
    }

    if (message.type === "update-control-banner") {
      updateControlBannerAction(message.action || "");
      sendResponse({ success: true });
      return;
    }

    if (message.type === "get-interactive-elements") {
      sendResponse(getInteractiveElements());
      return;
    }

    if (message.type === "click-at-coordinates") {
      try {
        const el = document.elementFromPoint(message.x || 0, message.y || 0);
        if (el) {
          el.focus();
          el.click();
          sendResponse({ success: true, tag: el.tagName, text: el.textContent?.substring(0, 50).trim() });
        } else {
          sendResponse({ error: `No element at coordinates (${message.x}, ${message.y})` });
        }
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    if (message.type === "type-text") {
      typeText(message.selector, message.text, message.clearFirst).then(sendResponse);
      return true; // async
    }

    if (message.type === "hover-element") {
      try {
        const el = findElement(message.selector);
        if (el) {
          el.scrollIntoView({ block: "nearest" });
          ["mouseover", "mouseenter", "mousemove"].forEach(type => {
            el.dispatchEvent(new MouseEvent(type, { bubbles: true, cancelable: true, view: window }));
          });
          sendResponse({ success: true, tag: el.tagName });
        } else {
          sendResponse({ error: `Element not found: ${message.selector}` });
        }
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    if (message.type === "check-element") {
      try {
        const el = findElement(message.selector);
        if (el && (el.type === "checkbox" || el.type === "radio")) {
          const target = message.checked !== undefined ? message.checked : !el.checked;
          if (el.checked !== target) {
            el.click(); // triggers native change events
          }
          sendResponse({ success: true, checked: el.checked });
        } else if (el) {
          sendResponse({ error: `Element is not a checkbox/radio: ${el.tagName} type=${el.type}` });
        } else {
          sendResponse({ error: `Checkbox/radio not found: ${message.selector}` });
        }
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Drag & Drop ----
    if (message.type === "drag-element") {
      try {
        const el = findElement(message.selector);
        if (!el) { sendResponse({ error: `Element not found: ${message.selector}` }); return; }
        const rect = el.getBoundingClientRect();
        const startX = rect.left + rect.width / 2;
        const startY = rect.top + rect.height / 2;
        let endX = message.toX, endY = message.toY;
        // If toSelector provided, calculate target center
        if (message.toSelector) {
          const targetEl = findElement(message.toSelector);
          if (!targetEl) { sendResponse({ error: `Drop target not found: ${message.toSelector}` }); return; }
          const targetRect = targetEl.getBoundingClientRect();
          endX = targetRect.left + targetRect.width / 2;
          endY = targetRect.top + targetRect.height / 2;
        }
        const dt = new DataTransfer();
        el.dispatchEvent(new DragEvent("dragstart", { bubbles: true, cancelable: true, clientX: startX, clientY: startY, dataTransfer: dt }));
        el.dispatchEvent(new DragEvent("drag", { bubbles: true, cancelable: true, clientX: startX, clientY: startY, dataTransfer: dt }));
        const dropTarget = document.elementFromPoint(endX, endY) || document.body;
        dropTarget.dispatchEvent(new DragEvent("dragenter", { bubbles: true, cancelable: true, clientX: endX, clientY: endY, dataTransfer: dt }));
        dropTarget.dispatchEvent(new DragEvent("dragover", { bubbles: true, cancelable: true, clientX: endX, clientY: endY, dataTransfer: dt }));
        dropTarget.dispatchEvent(new DragEvent("drop", { bubbles: true, cancelable: true, clientX: endX, clientY: endY, dataTransfer: dt }));
        el.dispatchEvent(new DragEvent("dragend", { bubbles: true, cancelable: true, clientX: endX, clientY: endY, dataTransfer: dt }));
        sendResponse({ success: true, from: { x: Math.round(startX), y: Math.round(startY) }, to: { x: Math.round(endX), y: Math.round(endY) } });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Right-Click / Context Menu ----
    if (message.type === "right-click-element") {
      try {
        const el = message.selector ? findElement(message.selector) : document.elementFromPoint(message.x || 0, message.y || 0);
        if (!el) { sendResponse({ error: `Element not found: ${message.selector || 'at coordinates'}` }); return; }
        const rect = el.getBoundingClientRect();
        const x = message.x || rect.left + rect.width / 2;
        const y = message.y || rect.top + rect.height / 2;
        const init = { bubbles: true, cancelable: true, clientX: x, clientY: y, button: 2, buttons: 2, view: window };
        el.dispatchEvent(new MouseEvent("mousedown", init));
        el.dispatchEvent(new MouseEvent("mouseup", init));
        el.dispatchEvent(new MouseEvent("contextmenu", init));
        sendResponse({ success: true, tag: el.tagName, text: el.textContent?.substring(0, 50)?.trim() });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Key Combination (Ctrl+S, Ctrl+A, etc.) ----
    if (message.type === "key-combo") {
      try {
        let target = document.activeElement || document.body;
        if (message.selector) {
          const el = findElement(message.selector);
          if (el) { el.focus(); target = el; }
        }
        const key = message.key || "";
        const mods = message.modifiers || [];
        const eventInit = {
          key,
          code: key.length === 1 ? "Key" + key.toUpperCase() : key,
          bubbles: true,
          cancelable: true,
          ctrlKey: mods.includes("ctrl") || mods.includes("Control"),
          shiftKey: mods.includes("shift") || mods.includes("Shift"),
          altKey: mods.includes("alt") || mods.includes("Alt"),
          metaKey: mods.includes("meta") || mods.includes("Meta") || mods.includes("cmd"),
        };
        target.dispatchEvent(new KeyboardEvent("keydown", eventInit));
        target.dispatchEvent(new KeyboardEvent("keypress", eventInit));
        target.dispatchEvent(new KeyboardEvent("keyup", eventInit));
        // Handle common shortcuts natively
        if (eventInit.ctrlKey || eventInit.metaKey) {
          if (key.toLowerCase() === "a" && target.select) target.select();
          if (key.toLowerCase() === "c") document.execCommand("copy");
          if (key.toLowerCase() === "v") document.execCommand("paste");
          if (key.toLowerCase() === "x") document.execCommand("cut");
        }
        sendResponse({ success: true, key, modifiers: mods, target: target.tagName });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Scroll To Element ----
    if (message.type === "scroll-to-element") {
      try {
        const el = findElement(message.selector);
        if (!el) { sendResponse({ error: `Element not found: ${message.selector}` }); return; }
        el.scrollIntoView({ behavior: "smooth", block: message.block || "center" });
        const rect = el.getBoundingClientRect();
        sendResponse({ success: true, tag: el.tagName, position: { top: Math.round(rect.top), left: Math.round(rect.left) } });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Submit Form Programmatically ----
    if (message.type === "submit-form") {
      try {
        let form;
        if (message.selector) {
          form = findElement(message.selector);
          if (form && form.tagName !== "FORM") form = form.closest("form");
        } else {
          form = document.querySelector("form");
        }
        if (!form) { sendResponse({ error: "No form found" }); return; }
        if (form.requestSubmit) {
          form.requestSubmit();
        } else {
          form.submit();
        }
        sendResponse({ success: true, action: form.action || "", method: form.method || "GET" });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Set Element Attribute ----
    if (message.type === "set-attribute") {
      try {
        const el = findElement(message.selector);
        if (!el) { sendResponse({ error: `Element not found: ${message.selector}` }); return; }
        el.setAttribute(message.attr, message.attrValue);
        sendResponse({ success: true, tag: el.tagName, attr: message.attr, value: message.attrValue });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Local/Session Storage ----
    if (message.type === "get-storage") {
      try {
        const storageType = message.storageType === "session" ? sessionStorage : localStorage;
        if (message.key) {
          sendResponse({ success: true, key: message.key, value: storageType.getItem(message.key) });
        } else {
          const data = {};
          for (let i = 0; i < Math.min(storageType.length, 100); i++) {
            const k = storageType.key(i);
            data[k] = storageType.getItem(k)?.substring(0, 500);
          }
          sendResponse({ success: true, count: storageType.length, data });
        }
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    if (message.type === "set-storage") {
      try {
        const storageType = message.storageType === "session" ? sessionStorage : localStorage;
        storageType.setItem(message.key, message.storageValue);
        sendResponse({ success: true, key: message.key });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- JavaScript Eval (sandboxed to page context) ----
    if (message.type === "javascript-eval") {
      try {
        const result = eval(message.code);
        const resultStr = typeof result === "object" ? JSON.stringify(result, null, 2)?.substring(0, 5000) : String(result)?.substring(0, 5000);
        sendResponse({ success: true, result: resultStr, type: typeof result });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Double-Click Element ----
    if (message.type === "double-click-element") {
      try {
        const el = findElement(message.selector);
        if (!el) { sendResponse({ error: `Element not found: ${message.selector}` }); return; }
        const rect = el.getBoundingClientRect();
        const x = rect.left + rect.width / 2, y = rect.top + rect.height / 2;
        const init = { bubbles: true, cancelable: true, clientX: x, clientY: y, detail: 2, view: window };
        el.dispatchEvent(new MouseEvent("mousedown", init));
        el.dispatchEvent(new MouseEvent("mouseup", init));
        el.dispatchEvent(new MouseEvent("click", init));
        el.dispatchEvent(new MouseEvent("mousedown", init));
        el.dispatchEvent(new MouseEvent("mouseup", init));
        el.dispatchEvent(new MouseEvent("click", init));
        el.dispatchEvent(new MouseEvent("dblclick", init));
        sendResponse({ success: true, tag: el.tagName, text: el.textContent?.substring(0, 50)?.trim() });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Focus Element ----
    if (message.type === "focus-element") {
      try {
        const el = findElement(message.selector);
        if (!el) { sendResponse({ error: `Element not found: ${message.selector}` }); return; }
        el.focus();
        el.scrollIntoView({ block: "nearest" });
        sendResponse({ success: true, tag: el.tagName, activeElement: document.activeElement === el });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }

    // ---- Get Clipboard ----
    if (message.type === "read-clipboard") {
      navigator.clipboard.readText().then(text => {
        sendResponse({ success: true, text: text?.substring(0, 5000) || "" });
      }).catch(e => {
        sendResponse({ error: "Clipboard read denied: " + e.message });
      });
      return true; // async
    }

    // ---- Write Clipboard ----
    if (message.type === "write-clipboard") {
      navigator.clipboard.writeText(message.text || "").then(() => {
        sendResponse({ success: true });
      }).catch(e => {
        sendResponse({ error: "Clipboard write denied: " + e.message });
      });
      return true; // async
    }

    // ---- Scroll within a specific container (not the page) ----
    if (message.type === "scroll-container") {
      try {
        const el = findElement(message.selector);
        if (!el) { sendResponse({ error: `Container not found: ${message.selector}` }); return; }
        const amount = message.amount || 300;
        if (message.direction === "up") el.scrollTop -= amount;
        else if (message.direction === "down") el.scrollTop += amount;
        else if (message.direction === "top") el.scrollTop = 0;
        else if (message.direction === "bottom") el.scrollTop = el.scrollHeight;
        sendResponse({ success: true, scrollTop: Math.round(el.scrollTop), scrollHeight: el.scrollHeight });
      } catch (e) {
        sendResponse({ error: e.message });
      }
      return;
    }
  }

  // Register the listener and store reference for future re-injection cleanup
  window.__clawAgentListener = messageHandler;
  chrome.runtime.onMessage.addListener(messageHandler);

  // ---- Control Banner ----
  function showControlBanner(action) {
    const existing = document.getElementById("__claw-control-banner__");
    if (existing) {
      const actionEl = existing.querySelector("#__claw-banner-action__");
      if (actionEl) actionEl.textContent = action;
      return;
    }
    const banner = document.createElement("div");
    banner.id = "__claw-control-banner__";
    banner.style.cssText = [
      "position:fixed", "top:0", "left:0", "right:0", "z-index:2147483647",
      "background:linear-gradient(90deg,#faf9f7 0%,#f5f3ef 50%,#ebe8e2 100%)",
      "color:#1a1a1a", "font-family:-apple-system,system-ui,sans-serif", "font-size:13px",
      "display:flex", "align-items:center", "gap:10px", "padding:8px 16px",
      "box-shadow:0 2px 10px rgba(0,0,0,0.08)", "border-bottom:2px solid #c96442",
    ].join(";");
    banner.innerHTML = `
      <span style="font-size:18px">🐾</span>
      <span style="font-weight:700;color:#c96442;letter-spacing:0.5px;">Claw</span>
      <span id="__claw-banner-action__" style="color:#1a1a1a;flex:1;">${escBanner(action)}</span>
      <span id="__claw-banner-tool__" style="color:#6b6b6b;font-size:11px;font-style:italic;max-width:200px;overflow:hidden;white-space:nowrap;text-overflow:ellipsis;"></span>
      <button id="__claw-stop-btn__" style="background:#dc2626;border:none;color:white;padding:4px 14px;border-radius:4px;cursor:pointer;font-size:12px;font-weight:700;flex-shrink:0;">Stop</button>
    `;
    document.documentElement.appendChild(banner);
    banner.querySelector("#__claw-stop-btn__").addEventListener("click", () => {
      chrome.runtime.sendMessage({ type: "stop-agent" });
      hideControlBanner();
    });
    // Push body down so banner doesn't overlap content
    const h = banner.getBoundingClientRect().height || 44;
    document.documentElement.style.setProperty("--claw-banner-h", h + "px");
    document.body.style.marginTop = "calc(" + h + "px + " + (getComputedStyle(document.body).marginTop || "0px") + ")";
    banner._origBodyMargin = getComputedStyle(document.body).marginTop;
  }

  function hideControlBanner() {
    const banner = document.getElementById("__claw-control-banner__");
    if (banner) {
      banner.remove();
      document.body.style.marginTop = "";
    }
  }

  function updateControlBannerAction(text) {
    const el = document.getElementById("__claw-banner-action__");
    if (el) el.textContent = text;
    const toolEl = document.getElementById("__claw-banner-tool__");
    if (toolEl) toolEl.textContent = "";
  }

  function updateControlBannerTool(text) {
    const toolEl = document.getElementById("__claw-banner-tool__");
    if (toolEl) toolEl.textContent = text;
  }

  function escBanner(str) {
    return String(str).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
  }

  // ---- Get All Interactive Elements ----
  function getInteractiveElements() {
    const SELECTORS = [
      "a[href]", "button", "input:not([type='hidden'])", "textarea", "select",
      "[role='button']", "[role='link']", "[role='checkbox']", "[role='radio']",
      "[role='tab']", "[role='menuitem']", "[role='option']", "[role='combobox']",
      "[role='spinbutton']", "[role='switch']", "[role='textbox']", "[role='listbox']",
      "[role='searchbox']", "[role='slider']",
      "[contenteditable='true']", "[contenteditable='']",
      "[tabindex]:not([tabindex='-1'])",
      // SPA-specific: Google Ads, Facebook, etc. use custom components
      "[data-placeholder]", "[aria-multiline]",
      "div[contenteditable]", "span[contenteditable]",
    ];
    const seen = new Set();
    const elements = [];
    let index = 0;

    // Pre-detect modal container using the same logic as scroll detection
    // If we're inside a modal/dialog/overlay, include ALL elements within it (not just viewport-visible)
    const scrollContainer = findScrollableContainer();
    const isInModal = scrollContainer && scrollContainer !== document.scrollingElement && scrollContainer !== document.documentElement && scrollContainer !== document.body;
    const modalContainer = isInModal ? scrollContainer : null;

    function processElement(el, source) {
      if (seen.has(el)) return;
      seen.add(el);

      const rect = el.getBoundingClientRect();
      const style = window.getComputedStyle(el);
      // Element must be display/visible/non-zero-size but can be off-viewport (modals may have large scrollable areas)
      const isRendered =
        style.display !== "none" &&
        style.visibility !== "hidden" &&
        style.opacity !== "0" &&
        rect.width > 0 && rect.height > 0;
      if (!isRendered) return;

      // Check if inside a modal/dialog — if so, include all rendered elements regardless of viewport position
      // Use the modal container detected by findScrollableContainer() for broader SPA compatibility
      const inModal = modalContainer ? el.closest("dialog, [role='dialog'], [role='alertdialog'], [aria-modal='true'], .cdk-overlay-pane, .mdc-dialog__surface") || modalContainer.contains(el) : false;
      // For elements outside modals, check if they're in the viewport
      if (!inModal) {
        const inViewport = rect.bottom > 0 && rect.top < window.innerHeight && rect.right > 0 && rect.left < window.innerWidth;
        if (!inViewport) return;
      }

      const text = (
        el.getAttribute("aria-label") ||
        el.getAttribute("title") ||
        el.getAttribute("data-placeholder") ||
        el.getAttribute("placeholder") ||
        el.textContent ||
        el.value ||
        el.placeholder ||
        ""
      ).trim().replace(/\s+/g, " ").substring(0, 80);

      // Build a reliable CSS selector
      let cssSelector = "";
      if (el.id) {
        cssSelector = "#" + CSS.escape(el.id);
      } else if (el.getAttribute("data-testid")) {
        cssSelector = `[data-testid="${el.getAttribute("data-testid")}"]`;
      } else if (el.getAttribute("aria-label")) {
        cssSelector = `${el.tagName.toLowerCase()}[aria-label="${CSS.escape(el.getAttribute("aria-label"))}"]`;
      } else if (el.getAttribute("name")) {
        cssSelector = `${el.tagName.toLowerCase()}[name="${CSS.escape(el.getAttribute("name"))}"]`;
      } else if (el.getAttribute("data-placeholder")) {
        cssSelector = `[data-placeholder="${CSS.escape(el.getAttribute("data-placeholder"))}"]`;
      } else if (el.className && typeof el.className === "string") {
        const cls = el.className.trim().split(/\s+/).slice(0, 2).map(c => CSS.escape(c)).join(".");
        if (cls) {
          cssSelector = `${el.tagName.toLowerCase()}.${cls}`;
        } else {
          cssSelector = el.tagName.toLowerCase();
        }
      } else {
        cssSelector = el.tagName.toLowerCase();
      }

      // Disambiguate: if multiple elements match this selector, make it unique
      try {
        const matches = document.querySelectorAll(cssSelector);
        if (matches.length > 1) {
          // Try adding value attribute for inputs
          if (el.value && (el.tagName === "INPUT" || el.tagName === "TEXTAREA")) {
            const valSel = `${cssSelector}[value="${CSS.escape(el.value)}"]`;
            try {
              if (document.querySelectorAll(valSel).length === 1) {
                cssSelector = valSel;
              }
            } catch {}
          }
          // If still not unique, find the nth index among matches
          if (document.querySelectorAll(cssSelector).length > 1) {
            const idx = Array.from(matches).indexOf(el);
            if (idx >= 0) {
              cssSelector = `${cssSelector}:nth(${idx})`;
            }
          }
        }
      } catch {}

      const isEditable = el.isContentEditable || el.getAttribute("contenteditable") === "true" || el.getAttribute("contenteditable") === "";

      elements.push({
        index: index++,
        type: el.type || (isEditable ? "contenteditable" : el.tagName.toLowerCase()),
        tag: el.tagName.toLowerCase(),
        role: el.getAttribute("role") || (isEditable ? "textbox" : null),
        text: text || "(no label)",
        selector: cssSelector,
        href: el.getAttribute("href") || null,
        checked: el.type === "checkbox" || el.type === "radio" ? el.checked : null,
        value: el.value ? String(el.value).substring(0, 80) : (isEditable ? el.textContent?.substring(0, 80) : null),
        placeholder: el.placeholder || el.getAttribute("data-placeholder") || null,
        disabled: el.disabled || el.getAttribute("aria-disabled") === "true" || false,
        contenteditable: isEditable || false,
        source: source || "main",
        position: {
          top: Math.round(rect.top),
          left: Math.round(rect.left),
          width: Math.round(rect.width),
          height: Math.round(rect.height),
          centerX: Math.round(rect.left + rect.width / 2),
          centerY: Math.round(rect.top + rect.height / 2),
        },
      });
    }

    // Scan main document
    for (const sel of SELECTORS) {
      let nodes;
      try { nodes = document.querySelectorAll(sel); } catch { continue; }
      for (const el of nodes) processElement(el, "main");
    }

    // Scan Shadow DOM roots (1 level deep — covers most frameworks)
    try {
      document.querySelectorAll("*").forEach(el => {
        if (el.shadowRoot) {
          for (const sel of SELECTORS) {
            let nodes;
            try { nodes = el.shadowRoot.querySelectorAll(sel); } catch { continue; }
            for (const shadowEl of nodes) processElement(shadowEl, "shadow:" + (el.tagName || "").toLowerCase());
          }
        }
      });
    } catch {}

    // Scan same-origin iframes (1 level deep)
    try {
      document.querySelectorAll("iframe").forEach(iframe => {
        try {
          const iframeDoc = iframe.contentDocument || iframe.contentWindow?.document;
          if (!iframeDoc) return;
          const iframeRect = iframe.getBoundingClientRect();
          for (const sel of SELECTORS) {
            let nodes;
            try { nodes = iframeDoc.querySelectorAll(sel); } catch { continue; }
            for (const el of nodes) {
              if (seen.has(el)) continue;
              seen.add(el);
              const innerRect = el.getBoundingClientRect();
              const rect = {
                top: iframeRect.top + innerRect.top,
                left: iframeRect.left + innerRect.left,
                width: innerRect.width,
                height: innerRect.height,
              };
              const style = el.ownerDocument.defaultView.getComputedStyle(el);
              if (style.display === "none" || style.visibility === "hidden" || rect.width <= 0 || rect.height <= 0) continue;
              const text = (el.getAttribute("aria-label") || el.getAttribute("title") || el.getAttribute("data-placeholder") || el.textContent || el.value || el.placeholder || "").trim().replace(/\s+/g, " ").substring(0, 80);
              let cssSelector = "";
              if (el.id) cssSelector = "#" + CSS.escape(el.id);
              else if (el.getAttribute("name")) cssSelector = `${el.tagName.toLowerCase()}[name="${CSS.escape(el.getAttribute("name"))}"]`;
              else cssSelector = el.tagName.toLowerCase();
              const isEditable = el.isContentEditable || el.getAttribute("contenteditable") === "true";
              elements.push({
                index: index++,
                type: el.type || (isEditable ? "contenteditable" : el.tagName.toLowerCase()),
                tag: el.tagName.toLowerCase(),
                role: el.getAttribute("role") || null,
                text: text || "(no label)",
                selector: cssSelector,
                source: "iframe:" + (iframe.id || iframe.name || "anonymous"),
                contenteditable: isEditable || false,
                position: { top: Math.round(rect.top), left: Math.round(rect.left), width: Math.round(rect.width), height: Math.round(rect.height), centerX: Math.round(rect.left + rect.width / 2), centerY: Math.round(rect.top + rect.height / 2) },
              });
            }
          }
        } catch {} // cross-origin iframes will throw — silently skip
      });
    } catch {}

    // Also find ALL elements on the page (not in viewport) and report a summary count
    let totalInteractive = 0;
    let belowViewport = 0;
    try {
      for (const sel of SELECTORS.slice(0, 8)) { // just core selectors for count
        const nodes = document.querySelectorAll(sel);
        for (const el of nodes) {
          totalInteractive++;
          const r = el.getBoundingClientRect();
          if (r.top > window.innerHeight) belowViewport++;
        }
      }
    } catch {}

    return {
      elements,
      count: elements.length,
      totalOnPage: totalInteractive,
      belowViewport,
      viewport: { width: window.innerWidth, height: window.innerHeight },
      scrollY: Math.round(window.scrollY),
      scrollHeight: document.documentElement.scrollHeight,
      hint: belowViewport > 0 ? `${belowViewport} more interactive elements below the viewport. Scroll down to see them.` : "All interactive elements are visible.",
    };
  }

  // ---- Natural Typing (React/Vue/Angular/contenteditable compatible) ----
  async function typeText(selector, text, clearFirst) {
    const el = findElement(selector);
    if (!el) return { error: `Element not found: ${selector}` };

    el.focus();
    el.scrollIntoView({ block: "nearest" });

    const isContentEditable = el.isContentEditable || el.getAttribute("contenteditable") === "true" || el.getAttribute("contenteditable") === "";

    if (isContentEditable) {
      // --- contenteditable path (Google Ads, rich text editors) ---
      if (clearFirst) {
        el.innerHTML = "";
        el.textContent = "";
        el.dispatchEvent(new Event("input", { bubbles: true }));
      }

      // Use execCommand for best compatibility with frameworks
      el.focus();
      for (const char of String(text)) {
        const keyInit = { key: char, charCode: char.charCodeAt(0), keyCode: char.charCodeAt(0), which: char.charCodeAt(0), bubbles: true, cancelable: true };
        el.dispatchEvent(new KeyboardEvent("keydown", keyInit));
        el.dispatchEvent(new KeyboardEvent("keypress", keyInit));

        // insertText via execCommand is the most compatible with SPAs
        document.execCommand("insertText", false, char);

        el.dispatchEvent(new InputEvent("input", { bubbles: true, data: char, inputType: "insertText" }));
        el.dispatchEvent(new KeyboardEvent("keyup", keyInit));
        await new Promise(r => setTimeout(r, 15));
      }

      el.dispatchEvent(new Event("change", { bubbles: true }));
      return { success: true, typed: text.length + " chars", finalValue: el.textContent?.substring(0, 100) || "", contenteditable: true };
    }

    // --- Standard input/textarea path ---
    if (clearFirst) {
      // Use native value setter to clear, compatible with React
      const nativeSetter =
        Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set ||
        Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set;
      if (nativeSetter) {
        nativeSetter.call(el, "");
      } else {
        el.value = "";
      }
      el.dispatchEvent(new Event("input", { bubbles: true }));
    }

    const nativeSetter =
      Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value")?.set ||
      Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, "value")?.set;

    for (const char of String(text)) {
      const code = char.charCodeAt(0);
      const keyInit = { key: char, charCode: code, keyCode: code, which: code, bubbles: true, cancelable: true };
      el.dispatchEvent(new KeyboardEvent("keydown", keyInit));
      el.dispatchEvent(new KeyboardEvent("keypress", keyInit));

      if (nativeSetter) {
        nativeSetter.call(el, el.value + char);
      } else {
        el.value += char;
      }
      el.dispatchEvent(new InputEvent("input", { bubbles: true, data: char, inputType: "insertText" }));
      el.dispatchEvent(new KeyboardEvent("keyup", keyInit));

      // Small natural delay
      await new Promise(r => setTimeout(r, 12));
    }

    el.dispatchEvent(new Event("change", { bubbles: true }));
    return { success: true, typed: text.length + " chars", finalValue: el.value.substring(0, 100) };
  }

  function extractPageContent() {
    // Get clean text content
    const bodyClone = document.body.cloneNode(true);
    // Remove scripts, styles, hidden elements
    bodyClone.querySelectorAll("script, style, noscript, svg, iframe, [hidden], [aria-hidden='true']")
      .forEach((el) => el.remove());

    let text = bodyClone.textContent || "";
    // Collapse whitespace
    text = text.replace(/\s+/g, " ").trim();
    // Cap at 15,000 chars
    if (text.length > 15000) {
      text = text.substring(0, 15000) + "\n... [truncated]";
    }

    // Get meta info
    const title = document.title || "";
    const url = document.location.href;
    const meta = {};
    document.querySelectorAll("meta[name], meta[property]").forEach((el) => {
      const key = el.getAttribute("name") || el.getAttribute("property") || "";
      const content = el.getAttribute("content") || "";
      if (key && content && key.length < 50) {
        meta[key] = content.substring(0, 200);
      }
    });

    // Headings structure
    const headings = Array.from(document.querySelectorAll("h1, h2, h3"))
      .slice(0, 30)
      .map((h) => ({ level: parseInt(h.tagName[1]), text: h.textContent?.trim().substring(0, 100) || "" }));

    return { title, url, text, meta, headings, charCount: text.length };
  }

  // Detect the primary scrollable container — modals, dialogs, overlay panels
  function findScrollableContainer() {
    // Check for open dialog/modal elements first
    const dialog = document.querySelector("dialog[open], [role='dialog'], [role='alertdialog'], .modal.show, .modal.open, [aria-modal='true']");
    if (dialog) {
      // Find the scrollable child within the dialog
      const scrollable = findScrollableChild(dialog);
      if (scrollable) return scrollable;
      if (dialog.scrollHeight > dialog.clientHeight + 10) return dialog;
    }

    // Check for overlay containers (position:fixed/absolute with overflow:auto/scroll)
    const overlays = document.querySelectorAll("[class*='overlay'], [class*='modal'], [class*='dialog'], [class*='popup'], [class*='flyout'], [class*='panel'], [class*='drawer']");
    for (const el of overlays) {
      const style = window.getComputedStyle(el);
      const pos = style.position;
      if ((pos === "fixed" || pos === "absolute") && el.scrollHeight > el.clientHeight + 10) {
        const overflow = style.overflow + style.overflowY;
        if (/auto|scroll/.test(overflow)) return el;
      }
      // Check children of overlay
      const scrollable = findScrollableChild(el);
      if (scrollable) return scrollable;
    }

    // Google Ads / Material Design specific: look for cdk-overlay, mat-dialog, mdc-dialog
    const matDialog = document.querySelector(".cdk-overlay-pane, .mdc-dialog__surface, .mat-dialog-container, .mat-mdc-dialog-surface");
    if (matDialog) {
      const scrollable = findScrollableChild(matDialog);
      if (scrollable) return scrollable;
      if (matDialog.scrollHeight > matDialog.clientHeight + 10) return matDialog;
    }

    // Fall back to the main document
    return document.scrollingElement || document.documentElement;
  }

  function findScrollableChild(parent) {
    // BFS for the first scrollable descendant with significant overflow
    const queue = [parent];
    while (queue.length) {
      const el = queue.shift();
      if (el.scrollHeight > el.clientHeight + 50 && el.clientHeight > 100) {
        const style = window.getComputedStyle(el);
        const overflow = style.overflow + style.overflowY;
        if (/auto|scroll/.test(overflow)) return el;
      }
      for (const child of el.children) {
        if (child.children.length > 0) queue.push(child);
      }
    }
    return null;
  }

  function findElement(selector) {
    // Handle our custom :nth(N) pseudo-selector for disambiguating duplicate selectors
    const nthMatch = selector.match(/^(.+):nth\((\d+)\)$/);
    if (nthMatch) {
      try {
        const matches = document.querySelectorAll(nthMatch[1]);
        const idx = parseInt(nthMatch[2], 10);
        if (matches[idx]) return matches[idx];
      } catch {}
    }

    // Try CSS selector first
    try {
      const el = document.querySelector(selector);
      if (el) return el;
    } catch {}

    // Try by text content
    if (selector.startsWith("text:")) {
      const searchText = selector.substring(5).toLowerCase();
      const all = document.querySelectorAll("a, button, input[type='submit'], [role='button']");
      for (const el of all) {
        if (el.textContent?.toLowerCase().includes(searchText)) return el;
      }
    }

    // Try by aria-label
    if (selector.startsWith("aria:")) {
      const label = selector.substring(5);
      return document.querySelector(`[aria-label="${CSS.escape(label)}"]`);
    }

    return null;
  }

  function executeAction(action, params) {
    switch (action) {
      case "highlight": {
        const el = findElement(params.selector);
        if (el) {
          el.style.outline = "3px solid #c96442";
          el.style.outlineOffset = "2px";
          setTimeout(() => { el.style.outline = ""; el.style.outlineOffset = ""; }, 3000);
          return { success: true };
        }
        return { error: "Element not found" };
      }
      case "get-computed-style": {
        const el = findElement(params.selector);
        if (el) {
          const style = window.getComputedStyle(el);
          const props = params.properties || ["color", "background", "fontSize", "display"];
          const result = {};
          props.forEach((p) => { result[p] = style.getPropertyValue(p); });
          return { style: result };
        }
        return { error: "Element not found" };
      }
      default:
        return { error: `Unknown action: ${action}` };
    }
  }
})();
