/**
 * Claw Agent — Side Panel Chat Controller
 * Streaming Ollama integration with tool calling, page context, and Claude-like UX.
 */

// ============================================================================
// State
// ============================================================================
let messages = [];
let ollamaUrl = "http://localhost:11434";
let currentModel = "openai/gpt-4o-mini"; // Default to OpenRouter model
let mode = "act"; // act | suggest | ask
let customSystemPrompt = "";
let isStreaming = false;
let abortController = null;
let totalTokens = 0;
let totalTurns = 0;
let sessionStart = Date.now();

// API Configuration — key loaded from chrome.storage (set in options page)
let OPENROUTER_API_KEY = "";
const OPENROUTER_API_BASE = "https://openrouter.ai/api/v1";
const CLAW_API_BASE = "https://clean-claw-ai.vercel.app";
const USE_CLOUD_API = true; // Set to true to use Cloud API instead of Ollama

// Load API key from storage on startup
if (typeof chrome !== 'undefined' && chrome.storage) {
  chrome.storage.sync.get(['openrouter_api_key'], (result) => {
    if (result.openrouter_api_key) OPENROUTER_API_KEY = result.openrouter_api_key;
  });
}

// Cloud models available
const CLOUD_MODELS = [
  "openai/gpt-4o-mini",
  "anthropic/claude-3-haiku-20240307",
  "google/gemini-flash-1.5",
  "qwen/qwen-2.5-coder-32b-instruct",
  "meta-llama/llama-3.3-70b-instruct",
  "deepseek/deepseek-v3",
];

const MAX_ITERATIONS = 50;
const MAX_TOOLS_PER_ITERATION = 10;   // cap tool calls per single LLM response
const MAX_TOTAL_TOOL_CALLS = 150;     // absolute cap across all iterations
const MAX_TOKENS_BEFORE_COMPACT = 50000;
const MAX_TOKENS_HARD_STOP = 100000;
const WALL_CLOCK_TIMEOUT_MS = 300000;  // 5 minutes max per user message
const COMPACT_KEEP_RECENT = 4;         // messages to keep during compaction
const PRESSURE_SOFT = 25;              // iteration to start suggesting wrap-up
const PRESSURE_HARD = 40;              // iteration to force conclusion
const PRESSURE_STRIP = 48;            // iteration to strip tools entirely
const BLOCKED_COMMANDS = ["claw", "rm -rf", "format c:", "del /s /q"];

// Detect repetitive text output (model stuck in generation loop)
function isRepetitive(text, minChunk = 40, minRepeats = 3) {
  if (text.length < minChunk * minRepeats) return false;
  const tail = text.slice(-(minChunk * (minRepeats + 1)));
  const pattern = text.slice(-minChunk);
  let count = 0;
  let idx = 0;
  while ((idx = tail.indexOf(pattern, idx)) !== -1) { count++; idx += 1; }
  return count >= minRepeats;
}

// ============================================================================
// Tool Definitions for Ollama
// ============================================================================
const TOOL_DEFINITIONS = [
  {
    type: "function",
    function: {
      name: "read_page",
      description: "Read the content of the current browser tab/page. Returns title, URL, text content, headings.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "extract_links",
      description: "Extract all links from the current page.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "extract_code",
      description: "Extract code blocks from the current page.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "extract_forms",
      description: "Extract forms and their inputs from the current page.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "click_element",
      description: "Click an element on the page by CSS selector or text content (prefix with 'text:').",
      parameters: {
        type: "object",
        properties: { selector: { type: "string", description: "CSS selector or 'text:Button Text'" } },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "fill_input",
      description: "Fill a text input on the page.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector of the input" },
          value: { type: "string", description: "Value to fill in" },
        },
        required: ["selector", "value"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "get_tab_info",
      description: "Get the current tab URL, title, and tab ID.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "web_search",
      description: "Search the web using DuckDuckGo and return results.",
      parameters: {
        type: "object",
        properties: { query: { type: "string", description: "Search query" } },
        required: ["query"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "fetch_url",
      description: "Fetch and read the text content of a URL.",
      parameters: {
        type: "object",
        properties: { url: { type: "string", description: "URL to fetch" } },
        required: ["url"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "scroll_page",
      description: "Scroll the page to a specific position.",
      parameters: {
        type: "object",
        properties: {
          direction: { type: "string", description: "'up', 'down', 'top', or 'bottom'" },
        },
        required: ["direction"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "highlight_element",
      description: "Highlight an element on the page with a colored outline.",
      parameters: {
        type: "object",
        properties: { selector: { type: "string", description: "CSS selector" } },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "navigate_to",
      description: "Navigate the current tab to a URL. Use when you need to go to a specific page.",
      parameters: {
        type: "object",
        properties: { url: { type: "string", description: "Full URL to navigate to" } },
        required: ["url"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "navigate_back",
      description: "Go back in browser history (like pressing the back button).",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "navigate_forward",
      description: "Go forward in browser history.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "take_screenshot",
      description: "Take a screenshot of the visible area of the current tab. Returns a description of the visual state.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "select_option",
      description: "Select an option in a <select> dropdown element.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector of the <select> element" },
          value: { type: "string", description: "Value or visible text of the option to select" },
        },
        required: ["selector", "value"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "press_key",
      description: "Press a keyboard key on the page or a focused element. Useful for Enter, Escape, Tab, ArrowDown, etc.",
      parameters: {
        type: "object",
        properties: {
          key: { type: "string", description: "Key to press: Enter, Escape, Tab, ArrowUp, ArrowDown, Backspace, etc." },
          selector: { type: "string", description: "Optional CSS selector to focus before pressing the key" },
        },
        required: ["key"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "wait_for_element",
      description: "Wait for an element to appear on the page (up to 10 seconds). Use after navigation or clicks that trigger loading. If it times out, the page likely loaded anyway — use read_page or take_screenshot instead of retrying. Use specific selectors, not generic ones like 'h2, h3'.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector or 'text:...' to wait for" },
          timeout: { type: "integer", description: "Max wait time in ms (default 5000, max 10000)" },
        },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "get_element_info",
      description: "Get detailed info about a specific element: text, attributes, dimensions, visibility.",
      parameters: {
        type: "object",
        properties: { selector: { type: "string", description: "CSS selector of the element" } },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "extract_tables",
      description: "Extract all table data from the current page as structured arrays. Very useful for dashboards and data pages.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  // ---- Claude-style precision browser control ----
  {
    type: "function",
    function: {
      name: "get_interactive_elements",
      description: "Get ALL interactive elements on the page (buttons, links, inputs, selects, checkboxes, roles). Returns indexed list with CSS selectors, text labels, types, and positions. Use 'filter' to narrow results on complex pages (searches text, type, selector, role, placeholder). Use this FIRST before clicking or filling.",
      parameters: {
        type: "object",
        properties: {
          filter: { type: "string", description: "Optional text to filter elements by (searches label, type, selector, role, placeholder). E.g. 'headline', 'input', 'submit', 'save'" },
        },
        required: [],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "type_text",
      description: "Type text into an input naturally, character by character with proper keyboard events. Compatible with React, Angular, and Vue. Use instead of fill_input when fill_input doesn't trigger the page's event handlers.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector or 'text:...' of the input element" },
          text: { type: "string", description: "Text to type" },
          clearFirst: { type: "boolean", description: "If true, clear the field before typing (default false)" },
        },
        required: ["selector", "text"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "hover_element",
      description: "Hover over an element to trigger hover menus, tooltips, or reveal hidden controls.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector or 'text:...' of the element to hover" },
        },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "check_element",
      description: "Toggle or set a checkbox or radio button. Fires all native browser events.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector of the checkbox or radio input" },
          checked: { type: "boolean", description: "Set to true to check, false to uncheck. Omit to toggle." },
        },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "click_at_coordinates",
      description: "Click at specific (x, y) pixel coordinates on the page. Use when you have exact pixel positions (e.g., from get_interactive_elements position.centerX/centerY) and CSS selectors are ambiguous.",
      parameters: {
        type: "object",
        properties: {
          x: { type: "number", description: "X coordinate (pixels from left)" },
          y: { type: "number", description: "Y coordinate (pixels from top)" },
        },
        required: ["x", "y"],
      },
    },
  },
  // ---- Extended Capabilities ----
  {
    type: "function",
    function: {
      name: "drag_element",
      description: "Drag an element to a new position or onto another element. Fires full HTML5 drag & drop events.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector of the element to drag" },
          toX: { type: "number", description: "Target X coordinate (pixels from left)" },
          toY: { type: "number", description: "Target Y coordinate (pixels from top)" },
          toSelector: { type: "string", description: "CSS selector of the drop target (alternative to toX/toY)" },
        },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "right_click",
      description: "Right-click (context menu) on an element or at coordinates. Triggers contextmenu event.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector or 'text:...' of the element to right-click" },
          x: { type: "number", description: "X coordinate (alternative to selector)" },
          y: { type: "number", description: "Y coordinate (alternative to selector)" },
        },
        required: [],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "double_click",
      description: "Double-click an element. Useful for selecting text, opening items, or triggering edit mode.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector or 'text:...' of the element" },
        },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "key_combo",
      description: "Press a keyboard shortcut/combination (e.g. Ctrl+S, Ctrl+A, Ctrl+C, Ctrl+V, Shift+Tab). Executes copy/paste/select-all natively.",
      parameters: {
        type: "object",
        properties: {
          modifiers: { type: "array", items: { type: "string" }, description: "Modifier keys: 'ctrl', 'shift', 'alt', 'meta'" },
          key: { type: "string", description: "The key to press with the modifiers (e.g. 'a', 's', 'c', 'v', 'Enter')" },
          selector: { type: "string", description: "Optional CSS selector to focus first" },
        },
        required: ["modifiers", "key"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "scroll_to_element",
      description: "Scroll a specific element into view. More precise than scroll_page — goes directly to the element.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector or 'text:...' of the element to scroll to" },
          block: { type: "string", description: "'center' (default), 'start', 'end', or 'nearest'" },
        },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "submit_form",
      description: "Submit a form programmatically. Use when pressing Enter doesn't trigger the form submission.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector of the form or an element inside the form" },
        },
        required: [],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "set_attribute",
      description: "Set an HTML attribute on an element. Useful for enabling disabled buttons, changing input types, or modifying element state.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector of the element" },
          attr: { type: "string", description: "Attribute name (e.g. 'disabled', 'value', 'class')" },
          attrValue: { type: "string", description: "Attribute value to set" },
        },
        required: ["selector", "attr", "attrValue"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "focus_element",
      description: "Focus an element (input, button, etc.) and scroll it into view. Use before typing or pressing keys.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector of the element to focus" },
        },
        required: ["selector"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "javascript_eval",
      description: "Execute JavaScript code on the page. Use for complex interactions that other tools can't handle — DOM manipulation, reading JS variables, triggering custom events, etc. Returns the result as a string.",
      parameters: {
        type: "object",
        properties: {
          code: { type: "string", description: "JavaScript code to execute on the page. Keep it short and targeted." },
        },
        required: ["code"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "read_clipboard",
      description: "Read text from the system clipboard.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "write_clipboard",
      description: "Write text to the system clipboard.",
      parameters: {
        type: "object",
        properties: {
          text: { type: "string", description: "Text to write to the clipboard" },
        },
        required: ["text"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "get_storage",
      description: "Read localStorage or sessionStorage from the current page. Without a key, returns all stored key-value pairs.",
      parameters: {
        type: "object",
        properties: {
          key: { type: "string", description: "Specific storage key to read (omit to get all)" },
          storageType: { type: "string", description: "'local' (default) or 'session'" },
        },
        required: [],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "set_storage",
      description: "Write a key-value pair to localStorage or sessionStorage on the current page.",
      parameters: {
        type: "object",
        properties: {
          key: { type: "string", description: "Storage key" },
          storageValue: { type: "string", description: "Value to store" },
          storageType: { type: "string", description: "'local' (default) or 'session'" },
        },
        required: ["key", "storageValue"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "get_cookies",
      description: "Get cookies for the current page's domain.",
      parameters: { type: "object", properties: {}, required: [] },
    },
  },
  {
    type: "function",
    function: {
      name: "manage_tabs",
      description: "Open, close, switch, or list browser tabs.",
      parameters: {
        type: "object",
        properties: {
          action: { type: "string", description: "'list', 'open', 'close', 'switch'" },
          url: { type: "string", description: "URL to open (for 'open' action)" },
          tabId: { type: "number", description: "Tab ID to switch to or close (for 'switch'/'close' actions)" },
        },
        required: ["action"],
      },
    },
  },
  {
    type: "function",
    function: {
      name: "scroll_container",
      description: "Scroll within a specific scrollable container/div (not the main page). Use for scrollable panels, menus, or sidebars.",
      parameters: {
        type: "object",
        properties: {
          selector: { type: "string", description: "CSS selector of the scrollable container" },
          direction: { type: "string", description: "'up', 'down', 'top', or 'bottom'" },
          amount: { type: "number", description: "Pixels to scroll (default 300)" },
        },
        required: ["selector", "direction"],
      },
    },
  },
];

// ============================================================================
// System Prompt
// ============================================================================
function getSystemPrompt() {
  const backend = USE_CLOUD_API ? 'Cloud API' : 'local Ollama';
  let prompt = `You are Claw, an elite autonomous AI browser agent running "${currentModel}" via ${backend}. You think strategically, act precisely, and PERSIST until the task is done.

TOOLS (40):
  Page: read_page, extract_links, extract_code, extract_forms, extract_tables
  Navigate: navigate_to, navigate_back, navigate_forward
  Interact: click_element, fill_input, select_option, press_key, scroll_page, double_click, right_click, drag_element
  Precision: get_interactive_elements, type_text, hover_element, check_element, click_at_coordinates, focus_element, scroll_to_element, scroll_container
  Keyboard: key_combo (Ctrl+S, Ctrl+C, Ctrl+V, etc.)
  Forms: submit_form, set_attribute
  Inspect: get_tab_info, get_element_info, highlight_element, take_screenshot
  Wait: wait_for_element
  Web: web_search, fetch_url
  Clipboard: read_clipboard, write_clipboard
  Storage: get_storage, set_storage, get_cookies
  Tabs: manage_tabs (list/open/close/switch tabs)
  Code: javascript_eval (execute JS on the page for anything tools can't do)

CORE PRINCIPLES:
1. THINK BEFORE ACTING. Plan your approach in 1-2 sentences, then execute.
2. COMPLETE THE TASK. If the user asks you to DO something (click, fill, change, edit, submit), you MUST keep going until the action is actually performed. Do NOT stop to give instructions — perform the steps yourself.
3. PERSIST THROUGH SPAs. Modern web apps (Google Ads, Facebook, dashboards) are SPAs — after clicking a button or navigating, the page content changes but the URL may stay similar. ALWAYS re-read the page with read_page after any click or navigation to see the new state. Previous reads are outdated after interactions.
4. NEVER GO IN CIRCLES. If you've tried the same approach 3+ times with no progress, try a DIFFERENT approach.
5. EFFICIENCY. Use the minimum tool calls needed, but don't sacrifice task completion for brevity.

STRATEGIC WORKFLOW:
- Start with read_page to understand the current page
- For clicking/filling: use get_interactive_elements FIRST — it finds ALL clickable/fillable elements including those in Shadow DOM, iframes, contenteditable divs, modals/dialogs, and custom SPA components
- On complex pages with many elements, use get_interactive_elements(filter="keyword") to search for specific elements by text/type/role. Example: get_interactive_elements(filter="headline") or get_interactive_elements(filter="input")
- DO NOT scroll repeatedly to find elements. get_interactive_elements already finds elements in modals AND below the viewport. If you need a specific element, use the filter parameter FIRST
- MODALS & DIALOGS: scroll_page automatically detects modals/dialogs and scrolls within them. If you're in a modal, use get_interactive_elements(filter="...") to find elements — it scans inside modals too
- After ANY click_element, fill_input, select_option, or navigation: call read_page again to see the updated page
- For SPAs (Google Ads, Facebook, dashboards): form fields are often contenteditable divs, not standard inputs. Look for type="contenteditable" or role="textbox" in get_interactive_elements results. Use type_text (not fill_input) for these
- For jumping to a specific element: use scroll_to_element(selector) — more precise than scroll_page
- For data analysis: extract_tables first. If empty, the data is in read_page text — analyze THAT
- If javascript_eval is blocked by CSP, use get_interactive_elements(filter=...), read_page, or other specialized tools
- If a tool fails, try a different selector or approach. If stuck after 3 attempts, explain what blocked you
- For multi-step tasks: work through each step sequentially, confirming each step succeeded before moving on

ACTION vs INFORMATION:
- If the user asks "summarize", "what is", "tell me about" → gather info and respond (information task)
- If the user asks "do it", "change", "click", "fill", "submit", "edit", "create", "delete" → KEEP USING TOOLS until the action is complete (action task). Do NOT just explain how to do it — ACTUALLY DO IT
- On action tasks, only stop when: (a) the action succeeded, (b) you hit an insurmountable blocker, or (c) you run out of turns

INTERACTION STYLE:
- Be concise and direct. No filler words.
- When reporting findings, structure them clearly with bullet points
- If you can't complete a task, explain exactly what blocked you, not generic summaries
- NEVER fabricate content — only report what tools actually returned
- When asked what model you are, say Claw running "${currentModel}" via ${backend}

HARD LIMITS:
- You have ~50 turns maximum. Budget them wisely but don't stop early if the task isn't done.
- If a tool says "SYSTEM: ... STOP", respond with text only.`;

  if (customSystemPrompt) {
    prompt += `\n\nUSER INSTRUCTIONS:\n${customSystemPrompt}`;
  }
  return prompt;
}

// ============================================================================
// Tool Execution
// ============================================================================
async function executeTool(name, args) {
  switch (name) {
    case "read_page":
      return await sendToBackground("get-page-content");

    case "extract_links":
      return await sendToTab("extract-links");

    case "extract_code":
      return await sendToTab("extract-code");

    case "extract_forms":
      return await sendToTab("extract-forms");

    case "get_tab_info":
      return await sendToBackground("get-tab-info");

    case "click_element":
      return await sendToTab("click-element", { selector: args.selector });

    case "fill_input":
      return await sendToTab("fill-input", { selector: args.selector, value: args.value });

    case "scroll_page": {
      // Get scroll info — detects modals/dialogs and scrolls within them
      const scrollInfo = await sendToTab("get-scroll-info");
      const prevScrollY = scrollInfo.scrollY || 0;
      const scrollHeight = scrollInfo.scrollHeight || 99999;
      const clientHeight = scrollInfo.clientHeight || 800;

      const y = args.direction === "top" ? 0 : args.direction === "bottom" ? 99999 :
        (args.direction === "up" ? Math.max(0, prevScrollY - clientHeight * 0.75) : prevScrollY + clientHeight * 0.75);
      await sendToTab("scroll-to", { x: 0, y });

      // Wait for scroll to settle
      await new Promise(r => setTimeout(r, 350));
      const postInfo = await sendToTab("get-scroll-info");
      const newScrollY = postInfo.scrollY || 0;
      const atBottom = newScrollY + clientHeight >= scrollHeight - 50;
      const atTop = newScrollY <= 0;
      const didMove = Math.abs(newScrollY - prevScrollY) > 10;

      // Quick count of interactive elements
      const postScroll = await sendToTab("get-interactive-elements");
      const inputEls = (postScroll.elements || []).filter(e =>
        ["input", "textarea", "select", "contenteditable"].includes(e.type) ||
        e.role === "textbox" || e.role === "combobox" || e.contenteditable
      );
      const buttonEls = (postScroll.elements || []).filter(e =>
        e.tag === "button" || e.role === "button"
      );

      return {
        success: true,
        scrolledTo: newScrollY,
        didMove,
        atTop,
        atBottom,
        isModal: scrollInfo.isModal || false,
        containerSelector: scrollInfo.containerSelector || null,
        visibleInputs: inputEls.length,
        visibleButtons: buttonEls.length,
        totalVisible: postScroll.count || 0,
        belowViewport: postScroll.belowViewport || 0,
        hint: !didMove ? (scrollInfo.isModal
            ? "Inside a modal/dialog. Content did not scroll — try get_interactive_elements(filter='...') to search for specific elements, or scroll_to_element to jump directly to an element."
            : "Page did not scroll — you may already be at the edge. Try get_interactive_elements or read_page instead.")
          : inputEls.length > 0 ? `Found ${inputEls.length} input field(s) now visible. Use get_interactive_elements to get their selectors.`
          : atBottom ? "Reached bottom. No more content below."
          : `Scrolled to ${newScrollY}px. ${postScroll.count} interactive elements visible, ${postScroll.belowViewport} more below.`,
      };
    }

    case "highlight_element":
      return await sendToBackground("execute-on-page", {
        action: "highlight",
        params: { selector: args.selector },
      });

    case "navigate_to": {
      const url = args.url || "";
      if (!/^https?:\/\//i.test(url)) {
        return { error: "Invalid URL. Must start with http:// or https://" };
      }
      return new Promise((resolve) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (!tabs[0]) { resolve({ error: "No active tab" }); return; }
          chrome.tabs.update(tabs[0].id, { url }, () => {
            // Wait for page to start loading
            setTimeout(() => resolve({ success: true, navigated_to: url }), 1500);
          });
        });
      });
    }

    case "web_search":
      return await webSearch(args.query);

    case "fetch_url":
      return await fetchUrl(args.url);

    case "navigate_back":
      return new Promise((resolve) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (!tabs[0]) { resolve({ error: "No active tab" }); return; }
          chrome.tabs.goBack(tabs[0].id, () => {
            setTimeout(async () => {
              const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
              resolve({ success: true, url: tab?.url || "unknown", title: tab?.title || "" });
            }, 1500);
          });
        });
      });

    case "navigate_forward":
      return new Promise((resolve) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (!tabs[0]) { resolve({ error: "No active tab" }); return; }
          chrome.tabs.goForward(tabs[0].id, () => {
            setTimeout(async () => {
              const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
              resolve({ success: true, url: tab?.url || "unknown", title: tab?.title || "" });
            }, 1500);
          });
        });
      });

    case "take_screenshot":
      return new Promise((resolve) => {
        chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
          if (!tabs[0]) { resolve({ error: "No active tab" }); return; }
          try {
            const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: "png" });
            const sizeKB = Math.round(dataUrl.length * 3 / 4 / 1024);
            resolve({
              success: true,
              description: `Screenshot captured of "${tabs[0].title}" (${tabs[0].url}). Image: ${sizeKB}KB PNG.`,
              url: tabs[0].url,
              title: tabs[0].title,
              _imageData: dataUrl,
            });
          } catch (e) {
            resolve({ error: "Screenshot failed: " + e.message });
          }
        });
      });

    case "select_option":
      return await sendToTab("select-option", { selector: args.selector, value: args.value });

    case "press_key":
      return await sendToTab("press-key", { key: args.key, selector: args.selector || null });

    case "wait_for_element":
      return await sendToTab("wait-for-element", {
        selector: args.selector,
        timeout: Math.min(args.timeout || 5000, 10000),
      });

    case "get_element_info":
      return await sendToTab("get-element-info", { selector: args.selector });

    case "extract_tables":
      return await sendToTab("extract-tables");

    case "get_interactive_elements": {
      const raw = await sendToTab("get-interactive-elements");
      if (args.filter && raw.elements) {
        const f = args.filter.toLowerCase();
        raw.elements = raw.elements.filter(el =>
          (el.text || "").toLowerCase().includes(f) ||
          (el.type || "").toLowerCase().includes(f) ||
          (el.selector || "").toLowerCase().includes(f) ||
          (el.role || "").toLowerCase().includes(f) ||
          (el.placeholder || "").toLowerCase().includes(f) ||
          (el.value || "").toLowerCase().includes(f) ||
          (el.tag || "").toLowerCase().includes(f)
        );
        raw.count = raw.elements.length;
        raw.filtered = true;
        raw.filterTerm = args.filter;
      }
      return raw;
    }

    case "type_text":
      return await sendToTab("type-text", {
        selector: args.selector,
        text: args.text,
        clearFirst: args.clearFirst || false,
      });

    case "hover_element":
      return await sendToTab("hover-element", { selector: args.selector });

    case "check_element":
      return await sendToTab("check-element", {
        selector: args.selector,
        checked: args.checked,
      });

    case "click_at_coordinates":
      return await sendToTab("click-at-coordinates", { x: args.x, y: args.y });

    // ---- Extended Capabilities ----
    case "drag_element":
      return await sendToTab("drag-element", {
        selector: args.selector,
        toX: args.toX,
        toY: args.toY,
        toSelector: args.toSelector,
      });

    case "right_click":
      return await sendToTab("right-click-element", {
        selector: args.selector,
        x: args.x,
        y: args.y,
      });

    case "double_click":
      return await sendToTab("double-click-element", { selector: args.selector });

    case "key_combo":
      return await sendToTab("key-combo", {
        modifiers: args.modifiers || [],
        key: args.key,
        selector: args.selector,
      });

    case "scroll_to_element":
      return await sendToTab("scroll-to-element", {
        selector: args.selector,
        block: args.block || "center",
      });

    case "submit_form":
      return await sendToTab("submit-form", { selector: args.selector });

    case "set_attribute":
      return await sendToTab("set-attribute", {
        selector: args.selector,
        attr: args.attr,
        attrValue: args.attrValue,
      });

    case "focus_element":
      return await sendToTab("focus-element", { selector: args.selector });

    case "javascript_eval":
      // Execute JS on the page via chrome.scripting
      // First try MAIN world, fall back to ISOLATED world for DOM queries
      return new Promise((resolve) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (!tabs[0]) { resolve({ error: "No active tab" }); return; }
          const tabId = tabs[0].id;
          // Try MAIN world first (has page JS access but may be CSP-blocked)
          chrome.scripting.executeScript({
            target: { tabId },
            world: "MAIN",
            func: (code) => {
              try {
                const result = (0, eval)(code);
                const resultStr = typeof result === "object" ? JSON.stringify(result, null, 2) : String(result);
                return { success: true, result: resultStr?.substring(0, 5000), type: typeof result };
              } catch (e) {
                return { error: e.message, csp: /unsafe-eval|content.security/i.test(e.message) };
              }
            },
            args: [args.code],
          }).then((results) => {
            const r = results?.[0]?.result;
            if (r && r.csp) {
              // CSP blocked eval in MAIN world — retry in ISOLATED world (can access DOM but not page JS)
              chrome.scripting.executeScript({
                target: { tabId },
                world: "ISOLATED",
                func: (code) => {
                  try {
                    // In isolated world, we can't eval but can run DOM operations directly
                    // Support common patterns: document.querySelector, querySelectorAll, etc.
                    const result = (0, eval)(code);
                    const resultStr = typeof result === "object" ? JSON.stringify(result, null, 2) : String(result);
                    return { success: true, result: resultStr?.substring(0, 5000), type: typeof result, world: "isolated" };
                  } catch (e2) {
                    return { error: `CSP blocks JavaScript eval on this site. Use get_interactive_elements(filter='...') to search for elements, read_page for content, or other specialized tools instead.` };
                  }
                },
                args: [args.code],
              }).then((r2) => {
                resolve(r2?.[0]?.result || { error: "CSP blocks eval. Use get_interactive_elements(filter='...') or read_page." });
              }).catch(() => {
                resolve({ error: "CSP blocks eval on this site. Use get_interactive_elements(filter='...') or read_page instead." });
              });
            } else {
              resolve(r || { error: "No result" });
            }
          }).catch((err) => {
            resolve({ error: err.message });
          });
        });
      });

    case "read_clipboard":
      return await sendToTab("read-clipboard");

    case "write_clipboard":
      return await sendToTab("write-clipboard", { text: args.text });

    case "get_storage":
      return await sendToTab("get-storage", {
        key: args.key,
        storageType: args.storageType || "local",
      });

    case "set_storage":
      return await sendToTab("set-storage", {
        key: args.key,
        storageValue: args.storageValue,
        storageType: args.storageType || "local",
      });

    case "get_cookies":
      return new Promise((resolve) => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
          if (!tabs[0]?.url) { resolve({ error: "No active tab" }); return; }
          try {
            const url = new URL(tabs[0].url);
            chrome.cookies.getAll({ domain: url.hostname }, (cookies) => {
              if (chrome.runtime.lastError) {
                resolve({ error: chrome.runtime.lastError.message });
                return;
              }
              resolve({
                success: true,
                domain: url.hostname,
                count: cookies.length,
                cookies: cookies.slice(0, 50).map(c => ({
                  name: c.name,
                  value: c.value?.substring(0, 200),
                  domain: c.domain,
                  path: c.path,
                  secure: c.secure,
                  httpOnly: c.httpOnly,
                  expirationDate: c.expirationDate,
                })),
              });
            });
          } catch (e) {
            resolve({ error: e.message });
          }
        });
      });

    case "manage_tabs": {
      const action = args.action || "list";
      if (action === "list") {
        return new Promise((resolve) => {
          chrome.tabs.query({ currentWindow: true }, (tabs) => {
            resolve({
              success: true,
              tabs: tabs.map(t => ({ id: t.id, title: t.title?.substring(0, 100), url: t.url, active: t.active, index: t.index })),
            });
          });
        });
      }
      if (action === "open") {
        const url = args.url || "about:blank";
        if (!/^https?:\/\//i.test(url) && url !== "about:blank") {
          return { error: "Invalid URL. Must start with http:// or https://" };
        }
        return new Promise((resolve) => {
          chrome.tabs.create({ url }, (tab) => {
            setTimeout(() => resolve({ success: true, tabId: tab.id, url }), 1500);
          });
        });
      }
      if (action === "close") {
        return new Promise((resolve) => {
          chrome.tabs.remove(args.tabId, () => {
            if (chrome.runtime.lastError) resolve({ error: chrome.runtime.lastError.message });
            else resolve({ success: true, closed: args.tabId });
          });
        });
      }
      if (action === "switch") {
        return new Promise((resolve) => {
          chrome.tabs.update(args.tabId, { active: true }, (tab) => {
            if (chrome.runtime.lastError) resolve({ error: chrome.runtime.lastError.message });
            else setTimeout(() => resolve({ success: true, tabId: tab.id, url: tab.url, title: tab.title }), 500);
          });
        });
      }
      return { error: `Unknown tab action: ${action}. Use 'list', 'open', 'close', or 'switch'.` };
    }

    case "scroll_container":
      return await sendToTab("scroll-container", {
        selector: args.selector,
        direction: args.direction,
        amount: args.amount || 300,
      });

    default:
      return { error: `Unknown tool: ${name}` };
  }
}

function sendToBackground(type, extra = {}) {
  return new Promise((resolve) => {
    chrome.runtime.sendMessage({ type, ...extra }, (response) => {
      resolve(response || { error: "No response" });
    });
  });
}

function sendToTab(type, extra = {}) {
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) {
        resolve({ error: "No active tab" });
        return;
      }
      chrome.tabs.sendMessage(tabs[0].id, { type, ...extra }, (response) => {
        if (chrome.runtime.lastError) {
          // Try injecting content script first
          chrome.scripting.executeScript({
            target: { tabId: tabs[0].id },
            files: ["content.js"],
          }).then(() => {
            chrome.tabs.sendMessage(tabs[0].id, { type, ...extra }, (resp) => {
              resolve(resp || { error: "No response after injection" });
            });
          }).catch((err) => resolve({ error: err.message }));
        } else {
          resolve(response || { error: "No response" });
        }
      });
    });
  });
}

async function webSearch(query) {
  try {
    const url = `https://html.duckduckgo.com/html/?q=${encodeURIComponent(query)}`;
    const resp = await fetch(url);
    const html = await resp.text();
    // Parse results from DDG HTML
    const parser = new DOMParser();
    const doc = parser.parseFromString(html, "text/html");
    const results = Array.from(doc.querySelectorAll(".result__body")).slice(0, 8).map((el) => {
      const titleEl = el.querySelector(".result__title a, .result__a");
      const snippetEl = el.querySelector(".result__snippet");
      return {
        title: titleEl?.textContent?.trim() || "",
        url: titleEl?.href || "",
        snippet: snippetEl?.textContent?.trim() || "",
      };
    });
    return { results, query };
  } catch (e) {
    return { error: `Search failed: ${e.message}` };
  }
}

async function fetchUrl(url) {
  try {
    // Basic URL validation
    const parsed = new URL(url);
    if (!["http:", "https:"].includes(parsed.protocol)) {
      return { error: "Only HTTP/HTTPS URLs allowed" };
    }
    const resp = await fetch(url);
    const contentType = resp.headers.get("content-type") || "";
    if (contentType.includes("text/html")) {
      const html = await resp.text();
      const parser = new DOMParser();
      const doc = parser.parseFromString(html, "text/html");
      doc.querySelectorAll("script, style, noscript, svg, iframe").forEach((el) => el.remove());
      let text = doc.body?.textContent || "";
      text = text.replace(/\s+/g, " ").trim();
      if (text.length > 10000) text = text.substring(0, 10000) + "\n... [truncated]";
      return { url, title: doc.title, text };
    } else {
      const text = await resp.text();
      return { url, text: text.substring(0, 10000) };
    }
  } catch (e) {
    return { error: `Fetch failed: ${e.message}` };
  }
}

async function evalOnPage(code) {
  // Safety check — block dangerous operations
  const dangerous = ["document.cookie", "localStorage.clear", "eval(", "Function("];
  for (const d of dangerous) {
    if (code.includes(d)) {
      return { error: `Blocked: ${d} not allowed` };
    }
  }
  return new Promise((resolve) => {
    chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
      if (!tabs[0]) { resolve({ error: "No active tab" }); return; }
      chrome.scripting.executeScript({
        target: { tabId: tabs[0].id },
        func: (expr) => {
          try { return { result: String(eval(expr)).substring(0, 5000) }; }
          catch (e) { return { error: e.message }; }
        },
        args: [code],
      }).then((results) => {
        const r = results[0]?.result || { error: "No result" };
        // Detect CSP blocking eval and give a clear message
        if (r.error && /content.security.policy|unsafe-eval|CSP/i.test(r.error)) {
          resolve({
            error: "BLOCKED by Content Security Policy — this site does not allow javascript_eval. " +
                   "Use read_page, extract_links, extract_forms, or click_element instead. Do NOT retry javascript_eval."
          });
        } else {
          resolve(r);
        }
      }).catch((err) => {
        if (/content.security.policy|unsafe-eval|CSP/i.test(err.message)) {
          resolve({
            error: "BLOCKED by Content Security Policy — this site does not allow javascript_eval. " +
                   "Use read_page, extract_links, extract_forms, or click_element instead. Do NOT retry javascript_eval."
          });
        } else {
          resolve({ error: err.message });
        }
      });
    });
  });
}

// ============================================================================
// Ollama Streaming
// ============================================================================
async function streamChat(userMessage) {
  if (isStreaming) return;
  isStreaming = true;
  sendBtn.disabled = true;
  stopBtn.style.display = "inline-flex";

  // Add user message
  messages.push({ role: "user", content: userMessage });
  addUserBubble(userMessage);

  // Show thinking indicator
  const thinkEl = addThinkingBubble();

  // Show the page-injected control banner
  sendToTab("show-control-banner", { action: "started controlling this browser" }).catch(() => {});

  try {
    if (USE_CLOUD_API) {
      await cloudAgentLoop(thinkEl);
    } else {
      await agentLoop(thinkEl);
    }
  } catch (e) {
    removeEl(thinkEl);
    if (e.name !== "AbortError") {
      addErrorBubble(e.message);
    }
  }

  // Hide the page banner once done
  sendToTab("hide-control-banner").catch(() => {});

  stopBtn.style.display = "none";
  isStreaming = false;
  sendBtn.disabled = false;
  updateCostBar();
}

// Cloud API: convert thinking bubble to streaming output
function updateThinkingText(el, text) {
  if (!el) return;
  el.className = 'msg assistant';
  el.innerHTML = renderMarkdown(text);
  scrollToBottom();
}

// Cloud API Agent Loop (OpenRouter)
async function cloudAgentLoop(thinkEl) {
  const systemMsg = { role: "system", content: getSystemPrompt().replace(/via local Ollama/g, "via Cloud API") };
  
  for (let iteration = 0; iteration < MAX_ITERATIONS; iteration++) {
    const apiMessages = [systemMsg, ...messages.slice(-20)];
    
    const payload = {
      model: currentModel,
      messages: apiMessages,
      tools: TOOL_DEFINITIONS,
      stream: true,
      temperature: 0.7,
      max_tokens: 4096,
    };

    try {
      const response = await fetch(`${OPENROUTER_API_BASE}/chat/completions`, {
        method: "POST",
        headers: {
          "Authorization": `Bearer ${OPENROUTER_API_KEY}`,
          "Content-Type": "application/json",
          "HTTP-Referer": "https://github.com/claw-agent",
          "X-Title": "Claw Agent Chrome Extension",
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let buffer = "";
      let assistantContent = "";
      let toolCalls = [];
      let currentToolCall = null;

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split("\n");
        buffer = lines.pop() || "";

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed || trimmed === "data: [DONE]") continue;
          if (!trimmed.startsWith("data: ")) continue;

          try {
            const json = JSON.parse(trimmed.slice(6));
            const choice = json.choices?.[0];
            if (!choice) continue;

            const delta = choice.delta;
            if (delta?.content) {
              assistantContent += delta.content;
              updateThinkingText(thinkEl, assistantContent);
            }

            if (delta?.tool_calls) {
              for (const tc of delta.tool_calls) {
                if (tc.id) {
                  currentToolCall = { id: tc.id, function: { name: tc.function?.name || "", arguments: tc.function?.arguments || "" } };
                  toolCalls.push(currentToolCall);
                } else if (currentToolCall && tc.function?.arguments) {
                  currentToolCall.function.arguments += tc.function.arguments;
                }
              }
            }

            if (choice.finish_reason === "stop" || choice.finish_reason === "tool_calls") {
              break;
            }
          } catch (e) { /* skip parse errors */ }
        }
      }

      // Build assistant message
      const assistantMsg = { role: "assistant", content: assistantContent };
      if (toolCalls.length > 0) {
        assistantMsg.tool_calls = toolCalls.map(tc => ({
          id: tc.id,
          type: "function",
          function: {
            name: tc.function.name,
            arguments: tc.function.arguments,
          },
        }));
      }
      messages.push(assistantMsg);
      updateThinkingText(thinkEl, assistantContent);

      // Execute tool calls
      if (toolCalls.length > 0) {
        for (const tc of toolCalls) {
          try {
            const args = JSON.parse(tc.function.arguments || "{}");
            const result = await executeTool(tc.function.name, args);
            messages.push({ role: "tool", content: String(result).substring(0, 8000), tool_call_id: tc.id });
          } catch (e) {
            messages.push({ role: "tool", content: `Error: ${e.message}`, tool_call_id: tc.id });
          }
        }
        // Continue loop to let model process tool results
        removeEl(thinkEl);
        thinkEl = addThinkingBubble();
        continue;
      } else {
        // No tool calls — we're done
        removeEl(thinkEl);
        if (assistantContent) {
          const el = addAssistantBubble();
          el.innerHTML = renderMarkdown(assistantContent);
          scrollToBottom();
        }
        return;
      }
    } catch (e) {
      if (e.name === "AbortError") throw e;
      throw new Error(`Cloud API error: ${e.message}. Check your internet connection.`);
    }
  }

  removeEl(thinkEl);
  addErrorBubble("Max iterations reached. The model may be stuck.");
}

async function agentLoop(thinkEl) {
  // ---- Loop protection state (fresh per user message) ----
  let totalErrors = 0;          // ALL errors across entire loop
  let consecutiveErrors = 0;    // errors in a row (never resets)
  let notFoundCount = 0;        // "not found" errors across all tools
  let emptyResults = 0;         // tools returning empty / no useful content
  const failedTools = {};       // { "tool_name": count }
  const toolCallCounts = {};    // { "tool_name": total_calls } — per-tool budget
  let totalToolCalls = 0;       // absolute cap across all iterations
  const startTokens = totalTokens;
  let cspBlocked = false;       // instant kill on CSP
  const loopStartTime = Date.now(); // wall-clock timeout
  const readPages = new Map();     // URL -> timestamp of last read
  const visitedUrls = new Set();   // URLs navigated to via navigate_to
  const domainVisits = {};         // { domain: count } — detect domain loops
  let waitTimeouts = 0;            // wait_for_element timeouts — soft budget
  const recentToolCalls = [];      // last N tool calls for exact-duplicate detection
  let compactedOnce = false;       // track if we already compacted
  let pageDirty = true;            // true when page state may have changed (click/fill/navigate); allows re-reads
  let scrollEdge = null;            // "top" or "bottom" when scroll has reached that edge
  let scrollStuckCount = 0;         // consecutive scroll_page calls where didMove:false
  const INTERACTION_TOOLS = new Set(["click_element", "fill_input", "select_option", "press_key", "scroll_page", "type_text", "hover_element", "check_element", "click_at_coordinates", "navigate_to", "navigate_back", "navigate_forward", "drag_element", "right_click", "double_click", "key_combo", "submit_form", "set_attribute", "focus_element", "javascript_eval", "scroll_container"]);

  for (let iteration = 0; iteration < MAX_ITERATIONS; iteration++) {

    // Wall-clock timeout
    if (Date.now() - loopStartTime > WALL_CLOCK_TIMEOUT_MS) {
      addErrorBubble("Time limit reached (5 min). Stopping.");
      return;
    }

    // Hard token cap
    if (totalTokens - startTokens > MAX_TOKENS_HARD_STOP) {
      addErrorBubble("Token budget exceeded for this request. Stopping.");
      return;
    }

    // ---- Progressive pressure: steer the model to conclude ----
    if (iteration === PRESSURE_SOFT) {
      messages.push({ role: "system", content: "SYSTEM: You have used 25 turns. If this is an information task, summarize now. If this is an action task and you're still making progress, continue — but be more targeted with your tool calls." });
    }
    if (iteration === PRESSURE_HARD) {
      messages.push({ role: "system", content: "SYSTEM: 40 turns used. You MUST finish within a few more turns. Complete the current action or give your final answer." });
    }

    // ---- Aggressive auto-compaction ----
    const estTokens = messages.reduce((s, m) => s + ((m.content || "").length / 3.5), 0);
    if ((totalTokens > MAX_TOKENS_BEFORE_COMPACT || estTokens > 15000) && messages.length > 6) {
      const keep = compactedOnce ? 2 : COMPACT_KEEP_RECENT;
      const recent = messages.slice(-keep);
      const oldMsgs = messages.slice(0, -keep);
      // Summarize non-tool messages; discard tool results entirely (they're the bloat)
      const summary = oldMsgs
        .filter((m) => m.role !== "tool")
        .map((m) => `${m.role}: ${(m.content || "").substring(0, 60)}`)
        .join("\n");
      messages = [
        { role: "system", content: `[Context compacted — ${oldMsgs.length} messages summarized]\n${summary}` },
        ...recent,
      ];
      compactedOnce = true;
      // Reset token counter after compaction so we don't immediately hit it again
      totalTokens = Math.round(totalTokens * 0.4);
    }

    const startTime = Date.now();

    // Build request — strip tools at PRESSURE_STRIP to force text-only
    const useTools = iteration < PRESSURE_STRIP;
    const payload = {
      model: currentModel,
      messages: [{ role: "system", content: getSystemPrompt() }, ...messages],
      stream: true,
    };
    if (useTools) payload.tools = TOOL_DEFINITIONS;

    abortController = new AbortController();

    const response = await fetch(`${ollamaUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      signal: abortController.signal,
    });

    if (!response.ok) {
      throw new Error(`Ollama error: ${response.status} ${response.statusText}`);
    }

    // Remove thinking indicator on first response
    removeEl(thinkEl);
    thinkEl = null;

    // Stream the response
    let collectedContent = "";
    let toolCalls = [];
    let promptTokens = 0;
    let completionTokens = 0;
    let assistantEl = null;

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = "";

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split("\n");
      buffer = lines.pop() || "";

      for (const line of lines) {
        if (!line.trim()) continue;
        let chunk;
        try { chunk = JSON.parse(line); } catch { continue; }

        const msg = chunk.message || {};

        // Stream text deltas
        if (msg.content) {
          collectedContent += msg.content;
          if (!assistantEl) assistantEl = addAssistantBubble();
          assistantEl.innerHTML = renderMarkdown(collectedContent);
          scrollToBottom();

          // Detect repetitive text (model stuck in generation loop)
          if (isRepetitive(collectedContent)) {
            collectedContent = collectedContent.substring(0, collectedContent.length - 80);
            assistantEl.innerHTML = renderMarkdown(collectedContent);
            try { reader.cancel(); } catch {}
            break;
          }
        }

        // Accumulate tool calls
        if (msg.tool_calls) {
          toolCalls.push(...msg.tool_calls);
        }

        // Final chunk
        if (chunk.done) {
          promptTokens = chunk.prompt_eval_count || 0;
          completionTokens = chunk.eval_count || 0;
        }
      }
    }

    const duration = Date.now() - startTime;
    totalTokens += promptTokens + completionTokens;
    totalTurns++;

    // --- Cap tool calls BEFORE building history ---
    if (toolCalls.length > MAX_TOOLS_PER_ITERATION) {
      toolCalls = toolCalls.slice(0, MAX_TOOLS_PER_ITERATION);
    }
    const remaining = MAX_TOTAL_TOOL_CALLS - totalToolCalls;
    if (remaining <= 0 && toolCalls.length > 0) {
      messages.push({ role: "assistant", content: collectedContent || "(tool budget exhausted)" });
      addErrorBubble("Tool call budget exhausted. Stopping.");
      return;
    }
    if (toolCalls.length > remaining) {
      toolCalls = toolCalls.slice(0, remaining);
    }
    totalToolCalls += toolCalls.length;

    // Save assistant message (with CAPPED tool_calls only)
    const assistantMsg = { role: "assistant", content: collectedContent };
    if (toolCalls.length) assistantMsg.tool_calls = toolCalls;
    messages.push(assistantMsg);

    // Execute tool calls if any
    if (toolCalls.length) {
      for (const tc of toolCalls) {
        const fn = tc.function || {};
        const name = fn.name || "";
        let args = fn.arguments || {};
        if (typeof args === "string") {
          try { args = JSON.parse(args); } catch { args = {}; }
        }

        // Show tool call UI
        const toolEl = addToolBubble(name, args);

        // Update the page banner with what tool is running
        const bannerLabel = Object.values(args || {}).filter(v => typeof v === "string").slice(0, 1)[0] || "";
        sendToTab("update-control-banner", {
          action: `running ${name}${bannerLabel ? ": " + bannerLabel.substring(0, 50) : ""}`,
        }).catch(() => {});

        const toolStart = Date.now();
        let result;

        // --- Duplicate call detection + URL tracking ---
        const callSig = `${name}:${JSON.stringify(args)}`;
        const isDuplicate = recentToolCalls.includes(callSig);
        recentToolCalls.push(callSig);
        if (recentToolCalls.length > 30) recentToolCalls.shift();

        // --- Block scroll_page when we already know we're at the edge ---
        if (name === "scroll_page" && scrollEdge) {
          const dir = args.direction || "down";
          const blocked = (scrollEdge === "bottom" && (dir === "down" || dir === "bottom")) ||
                          (scrollEdge === "top" && (dir === "up" || dir === "top"));
          if (blocked) {
            const edgeMsg = `SYSTEM: Already at ${scrollEdge} of page. STOP scrolling. Use get_interactive_elements (finds ALL elements including below viewport) or read_page instead. Do NOT call scroll_page again.`;
            messages.push({ role: "tool", content: edgeMsg });
            updateToolBubble(toolEl, name, { skipped: true, message: `blocked — already at ${scrollEdge}` }, Date.now() - toolStart);
            addErrorBubble(`Already at ${scrollEdge} of page. No more content in that direction.`);
            break;
          }
        }

        // --- Consecutive-same-tool detection ---
        // If the model calls the same tool 3+ times in a row, block execution and inject a hard nudge
        // For scroll_page: only count non-productive scrolls (didMove:false) via scrollStuckCount
        const lastN = recentToolCalls.slice(-3);
        const allSameTool = lastN.length >= 3 && lastN.every(sig => sig.startsWith(name + ":"));
        if (allSameTool && ["wait_for_element", "click_element"].includes(name)) {
          const nudge = `SYSTEM: "${name}" called 3+ times consecutively. Try a completely different approach.`;
          messages.push({ role: "tool", content: nudge });
          updateToolBubble(toolEl, name, { skipped: true, message: "blocked — consecutive loop" }, Date.now() - toolStart);
          addErrorBubble(`Stopped: "${name}" called 3+ times consecutively. Try a different approach.`);
          break;
        }

        // Smart URL-based duplicate detection for read_page (respects SPA state changes)
        if (name === "read_page") {
          const tabInfo = await sendToBackground("get-tab-info").catch(() => ({}));
          const currentUrl = tabInfo.url || "";
          const urlKey = currentUrl.split("?")[0]; // strip query params for comparison
          const lastRead = readPages.get(urlKey);
          const staleMs = 30000; // allow re-read after 30 seconds
          if (lastRead && !pageDirty && (Date.now() - lastRead < staleMs)) {
            result = { skipped: true, message: `Already read this page (${urlKey}) and nothing has changed. Use the previous content.` };
          } else {
            try { result = await executeTool(name, args); } catch (e) { result = { error: e.message }; }
            if (!result.error && !result.skipped) { readPages.set(urlKey, Date.now()); pageDirty = false; }
          }
        }
        // Smart navigation loop detection
        else if (name === "navigate_to") {
          const navUrl = args.url || "";
          const navKey = navUrl.split("?")[0];
          let navDomain;
          try { navDomain = new URL(navUrl).hostname; } catch { navDomain = navUrl; }

          if (visitedUrls.has(navKey)) {
            result = { skipped: true, message: `Already navigated to ${navKey}. Try a different page or approach.` };
          } else {
            domainVisits[navDomain] = (domainVisits[navDomain] || 0) + 1;
            if (domainVisits[navDomain] > 8) {
              result = { skipped: true, message: `SYSTEM: Navigated to ${navDomain} ${domainVisits[navDomain]} times. You are going in circles. Try a different approach.` };
            } else {
              visitedUrls.add(navKey);
              try { result = await executeTool(name, args); } catch (e) { result = { error: e.message }; }
              if (!result.error && !result.skipped) pageDirty = true;
            }
          }
        }
        // Standard duplicate detection for content-extraction tools (respects SPA state changes)
        // NOTE: get_interactive_elements is NOT deduped — the agent needs its data to avoid blind scrolling
        else if (isDuplicate && !pageDirty && ["extract_tables", "extract_links", "extract_forms", "extract_code"].includes(name)) {
          result = { skipped: true, message: `Already called ${name} with these args and page hasn't changed. Use the previous result.` };
        } else {
          try {
            result = await executeTool(name, args);
          } catch (e) {
            result = { error: e.message };
          }
          // Mark page as dirty after any interaction tool
          // scroll_page with didMove:false didn't change anything — don't mark dirty
          if (INTERACTION_TOOLS.has(name) && !result.error && !result.skipped) {
            if (name === "scroll_page" && result && result.didMove === false) {
              // no-op: scroll didn't actually move — count toward stuck budget
              scrollStuckCount++;
              if (scrollStuckCount >= 3) {
                const stuckMsg = "SYSTEM: scroll_page failed to move 3 times. STOP scrolling. Use get_interactive_elements (with filter param to find specific elements) or read_page instead. Do NOT call scroll_page again.";
                messages.push({ role: "tool", content: stuckMsg });
                updateToolBubble(toolEl, name, { skipped: true, message: "blocked — scroll stuck" }, Date.now() - toolStart);
                addErrorBubble(`Stopped: \"scroll_page\" called 3 times without moving. Try a different approach.`);
                break;
              }
            } else {
              pageDirty = true;
              if (name === "scroll_page") scrollStuckCount = 0; // reset on successful scroll
            }
          }
        }
        const toolDur = Date.now() - toolStart;

        // --- Error tracking (multi-layer) ---
        // Strip _imageData before converting to string (too large for context)
        let resultForContext = result;
        if (typeof result === "object" && result !== null && result._imageData) {
          const { _imageData, ...rest } = result;
          resultForContext = rest;
        }
        const resultStr = typeof resultForContext === "string" ? resultForContext : JSON.stringify(resultForContext);
        // Precise error detection — avoid false positives on normal content containing "error" or "not found"
        const isError = (/^Error:|"error":\s*"|\berror"?\s*:/i.test(resultStr) || (result && result.error)) && !(result && result.timeout);
        const isTimeout = result && result.timeout === true;
        const isCSP = (typeof result === "object" && result !== null && result.csp === true) || (/content.security.policy|unsafe-eval/i.test(resultStr) && !/"csp"\s*:\s*false/i.test(resultStr));
        const isNotFound = /^not found|"not_found"|no element found|no matching element/i.test(resultStr) && !isTimeout;
        const isEmpty = !resultStr.trim() || ["null","undefined","{}","(no output)","no output"].includes(resultStr.trim());

        // Track per-tool call counts (skip doesn't count)
        const isSkipped = result && result.skipped === true;
        if (!isSkipped) toolCallCounts[name] = (toolCallCounts[name] || 0) + 1;

        // Update tool bubble with result
        updateToolBubble(toolEl, name, result, toolDur);

        // ===== CSP error: disable javascript_eval but continue session =====
        if (isCSP && name === "javascript_eval") {
          cspBlocked = true;
          messages.push({ role: "tool", content: "SYSTEM: javascript_eval is blocked by Content Security Policy on this site. Do NOT call javascript_eval again. Use get_interactive_elements (with filter param), read_page, extract_links, or extract_forms instead. All other tools still work normally." });
          addErrorBubble("javascript_eval blocked by CSP. Other tools still work.");
          // Don't return — continue processing other tools in this batch
          continue;
        }

        if (isError) {
          totalErrors++;
          consecutiveErrors++;
          failedTools[name] = (failedTools[name] || 0) + 1;
          if (isNotFound) notFoundCount++;

          // Inject stop signal for the model
          const stopMsg = `SYSTEM: Tool "${name}" failed: ${resultStr.substring(0, 200)}. ` +
            (failedTools[name] >= 3 ? "Do NOT call it again. STOP using tools." : "Try a different approach or STOP.");
          messages.push({ role: "tool", content: stopMsg });
        } else if (isTimeout) {
          // Timeouts are soft — don't count as hard errors but have their own budget
          waitTimeouts++;
          consecutiveErrors = 0;
          if (waitTimeouts >= 3) {
            messages.push({ role: "tool", content: `SYSTEM: wait_for_element has timed out ${waitTimeouts} times. The page is a SPA — do NOT use wait_for_element. Use read_page or get_interactive_elements to see the current page state, then act on what you find.` });
          } else {
            messages.push({ role: "tool", content: resultStr });
          }
        } else if (isEmpty) {
          emptyResults++;
          consecutiveErrors = 0;  // reset on non-error
          messages.push({ role: "tool", content: resultStr || "(no output)" });
        } else {
          // Success — reset consecutive errors
          consecutiveErrors = 0;
          // Smart truncation: different limits per tool type to prevent context bloat
          let maxLen = 2000; // default
          if (name === "read_page") maxLen = 6000;
          else if (name === "get_interactive_elements") maxLen = 6000;
          else if (["extract_links", "extract_tables", "extract_forms", "extract_code"].includes(name)) maxLen = 2000;
          else if (["click_element", "fill_input", "press_key", "select_option", "check_element", "hover_element", "click_at_coordinates", "type_text", "drag_element", "right_click", "double_click", "key_combo", "submit_form", "set_attribute", "focus_element"].includes(name)) maxLen = 300;
          else if (["navigate_to", "navigate_back", "navigate_forward", "scroll_page", "highlight_element", "scroll_to_element", "scroll_container"].includes(name)) maxLen = 200;
          else if (name === "javascript_eval") maxLen = 4000;
          else if (["get_storage", "get_cookies"].includes(name)) maxLen = 3000;
          const truncated = resultStr.length > maxLen ? resultStr.substring(0, maxLen) + "\n...[truncated]" : resultStr;
          messages.push({ role: "tool", content: truncated });
        }

        // --- Circuit breakers (any one triggers = hard stop) ---
        if (consecutiveErrors >= 6) {
          addErrorBubble("Stopped: multiple consecutive tool errors. The page may not support this action.");
          return;
        }
        if (totalErrors >= 10) {
          addErrorBubble("Stopped: too many errors. Try a simpler request.");
          return;
        }
        if (notFoundCount >= 6) {
          addErrorBubble("Stopped: element not found after multiple attempts. Check the page manually.");
          return;
        }
        if (failedTools[name] >= 6) {
          addErrorBubble(`Stopped: "${name}" failed 6 times. This action is not available on this page.`);
          return;
        }
        if (emptyResults >= 5) {
          addErrorBubble("Stopped: tools returning empty results. Try a different approach.");
          return;
        }
        // Per-tool budget: tool-specific limits (read_page needs more on SPAs)
        const PER_TOOL_LIMITS = {
          read_page: 30,
          get_interactive_elements: 25,
          scroll_page: 10,        // allow enough scrolls for long modal forms
          wait_for_element: 4,
          highlight_element: 5,
        };
        const perToolLimit = PER_TOOL_LIMITS[name] || 15;
        if (toolCallCounts[name] >= perToolLimit) {
          const hint = name === "scroll_page"
            ? " Use get_interactive_elements (finds ALL page elements including below viewport) or read_page instead."
            : "";
          addErrorBubble(`Stopped: "${name}" called ${toolCallCounts[name]} times. Try a different approach.${hint}`);
          messages.push({ role: "tool", content: `SYSTEM: "${name}" called ${toolCallCounts[name]} times — BUDGET EXHAUSTED.${hint} Respond with text only.` });
          return;
        }
        // Wait timeout budget: after 4 timeouts, hard stop the wait loop
        if (waitTimeouts >= 4) {
          messages.push({ role: "tool", content: "SYSTEM: Too many wait timeouts. Use read_page or get_interactive_elements instead." });
          break;  // break out of tool loop, let model generate final response
        }
      }

      // Continue the loop — let the model process tool results
      thinkEl = addThinkingBubble();
      continue;
    }

    // No tool calls — agent is done
    return;
  }

  // Iteration limit reached — give model one last chance to summarize WITHOUT tools
  messages.push({ role: "system", content: "SYSTEM: Tool call limit reached. Summarize your findings and respond to the user now. Do NOT call any more tools." });
  try {
    const summaryPayload = {
      model: currentModel,
      messages: [{ role: "system", content: getSystemPrompt() }, ...messages],
      stream: true,
      // NO tools — force text-only response
    };
    const summaryResp = await fetch(`${ollamaUrl}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(summaryPayload),
    });
    if (summaryResp.ok) {
      const reader2 = summaryResp.body.getReader();
      const decoder2 = new TextDecoder();
      let buf2 = "";
      let summaryText = "";
      const summEl = addAssistantBubble();
      while (true) {
        const { done, value } = await reader2.read();
        if (done) break;
        buf2 += decoder2.decode(value, { stream: true });
        const lines = buf2.split("\n");
        buf2 = lines.pop() || "";
        for (const line of lines) {
          if (!line.trim()) continue;
          let chunk;
          try { chunk = JSON.parse(line); } catch { continue; }
          if (chunk.message?.content) {
            summaryText += chunk.message.content;
            summEl.innerHTML = renderMarkdown(summaryText);
            scrollToBottom();
            if (isRepetitive(summaryText)) { try { reader2.cancel(); } catch {} break; }
          }
        }
      }
      messages.push({ role: "assistant", content: summaryText });
    }
  } catch {
    addErrorBubble("Iteration limit reached (" + MAX_ITERATIONS + " turns). Stopping.");
  }
}

// ============================================================================
// UI Helpers
// ============================================================================
const messagesEl = document.getElementById("messages");
const inputEl = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");
const stopBtn = document.getElementById("stopBtn");
const costBar = document.getElementById("costBar");
const statusEl = document.getElementById("modelSelect");

function scrollToBottom() {
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function esc(text) {
  const d = document.createElement("div");
  d.textContent = text;
  return d.innerHTML;
}

function removeEl(el) {
  if (el && el.parentNode) el.parentNode.removeChild(el);
}

function clearWelcome() {
  const welcome = messagesEl.querySelector(".welcome");
  if (welcome) welcome.remove();
}

function addUserBubble(text) {
  clearWelcome();
  const d = document.createElement("div");
  d.className = "msg user";
  d.textContent = text;
  messagesEl.appendChild(d);
  scrollToBottom();
  return d;
}

function addAssistantBubble() {
  const d = document.createElement("div");
  d.className = "msg assistant";
  messagesEl.appendChild(d);
  scrollToBottom();
  return d;
}

function addThinkingBubble() {
  const d = document.createElement("div");
  d.className = "msg thinking";
  d.innerHTML = '<span class="spinner"></span> Thinking...';
  messagesEl.appendChild(d);
  scrollToBottom();
  return d;
}

// Per-tool icons for nicer display
const TOOL_ICONS = {
  read_page: "📄", extract_links: "🔗", extract_code: "💻", extract_forms: "📝",
  extract_tables: "📊", click_element: "👆", fill_input: "✏️", select_option: "📋",
  press_key: "⌨️", scroll_page: "↕️", highlight_element: "🔍", navigate_to: "🧭",
  navigate_back: "◀️", navigate_forward: "▶️", take_screenshot: "📷", get_tab_info: "ℹ️",
  get_element_info: "🏷️", wait_for_element: "⏳", web_search: "🔎", fetch_url: "🌐",
  get_interactive_elements: "🗺️", type_text: "🖊️", hover_element: "🖱️",
  check_element: "☑️", click_at_coordinates: "🎯",
  drag_element: "🤏", right_click: "🖱️", double_click: "👆👆", key_combo: "⌨️",
  scroll_to_element: "📍", submit_form: "📤", set_attribute: "🔧", focus_element: "🎯",
  javascript_eval: "⚡", read_clipboard: "📋", write_clipboard: "📋",
  get_storage: "💾", set_storage: "💾", get_cookies: "🍪", manage_tabs: "📑",
  scroll_container: "↕️",
};

function addToolBubble(name, args) {
  const icon = TOOL_ICONS[name] || "⚙️";
  const argsStr = Object.entries(args || {})
    .filter(([k]) => k !== "_imageData")
    .map(([k, v]) => `${k}=${String(v).substring(0, 40)}`)
    .join(", ");
  const d = document.createElement("div");
  d.className = "msg tool-call";
  d.innerHTML =
    `<span class="spinner"></span> ${icon} <span class="tool-name">${esc(name)}</span>` +
    (argsStr ? ` <span class="tool-args">${esc(argsStr)}</span>` : "");
  messagesEl.appendChild(d);
  scrollToBottom();
  return d;
}

function updateToolBubble(el, name, result, durationMs) {
  const icon = TOOL_ICONS[name] || "⚙️";
  const resultObj = typeof result === "object" ? result : {};
  const preview = typeof result === "string" ? result : JSON.stringify(result);
  const short = preview.substring(0, 200);

  let extra = "";
  // Show screenshot inline
  if (name === "take_screenshot" && resultObj._imageData) {
    extra = `<div style="margin-top:6px;"><img src="${resultObj._imageData}" style="max-width:100%;border-radius:6px;border:1px solid #e5e2dd;" /></div>`;
  }

  el.innerHTML =
    `✓ ${icon} <span class="tool-name">${esc(name)}</span>` +
    ` <span class="tool-time">${durationMs}ms</span>` +
    (short ? `<div class="tool-result">${esc(short)}</div>` : "") +
    extra;
  scrollToBottom();
}

function addErrorBubble(text) {
  const d = document.createElement("div");
  d.className = "msg error";
  d.textContent = "⚠ " + text;
  messagesEl.appendChild(d);
  scrollToBottom();
}

function addPageContextBubble(info) {
  const d = document.createElement("div");
  d.className = "msg page-context";
  d.textContent = `📄 Page: ${info.title || info.url} (${(info.charCount || 0).toLocaleString()} chars)`;
  messagesEl.appendChild(d);
  scrollToBottom();
}

function renderMarkdown(text) {
  // Simple markdown rendering
  let html = esc(text);

  // Code blocks
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (_, lang, code) => {
    return `<pre><code class="lang-${lang}">${code}</code></pre>`;
  });

  // Inline code
  html = html.replace(/`([^`]+)`/g, "<code>$1</code>");

  // Bold
  html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

  // Italic
  html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");

  // Headers
  html = html.replace(/^### (.*$)/gm, "<h3>$1</h3>");
  html = html.replace(/^## (.*$)/gm, "<h2>$1</h2>");
  html = html.replace(/^# (.*$)/gm, "<h1>$1</h1>");

  // Links
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank">$1</a>');

  // Line breaks
  html = html.replace(/\n/g, "<br>");

  return html;
}

function updateCostBar() {
  const elapsed = ((Date.now() - sessionStart) / 1000).toFixed(1);
  costBar.textContent = `Turns: ${totalTurns} | Tokens: ${totalTokens.toLocaleString()} | Time: ${elapsed}s | Cost: FREE` + (USE_CLOUD_API ? ' (Cloud)' : ' (Ollama)');
}

// ============================================================================
// Slash Commands
// ============================================================================
const SLASH_COMMANDS = {
  "/clear": () => {
    messages = [];
    messagesEl.innerHTML = "";
    totalTokens = 0;
    totalTurns = 0;
    consecutiveErrors = 0;
    sessionStart = Date.now();
    costBar.textContent = "";
    messagesEl.innerHTML = `
      <div class="welcome">
        <div class="welcome-icon">🦞</div>
        <h2>Claw Agent</h2>
        <p>AI browser agent · 40 tools</p>
      </div>`;
  },
  "/models": async () => {
    if (USE_CLOUD_API) {
      const list = CLOUD_MODELS.map((m) =>
        m === currentModel ? `**${m}** ← current` : m
      ).join("\n  ");
      addAssistantBubble().innerHTML = renderMarkdown(`**Cloud Models (${CLOUD_MODELS.length}):**\n  ${list}`);
    } else {
      try {
        const resp = await fetch(`${ollamaUrl}/api/tags`);
        const data = await resp.json();
        const names = (data.models || []).map((m) =>
          m.name === currentModel ? `**${m.name}** ← current` : m.name
        ).join("\n  ");
        addAssistantBubble().innerHTML = renderMarkdown(`**Available models:**\n  ${names}`);
      } catch (e) {
        addErrorBubble(`Cannot reach Ollama: ${e.message}`);
      }
    }
  },
  "/model": () => {
    addAssistantBubble().innerHTML = renderMarkdown(`Current model: **${currentModel}**`);
  },
  "/help": () => {
    addAssistantBubble().innerHTML = renderMarkdown(
      `**Claw Agent Commands:**
/clear — New conversation
/models — List available models
/model — Show current model
/page — Read current page into context
/links — Extract page links
/code — Extract code from page
/forms — Extract forms from page
/compact — Compress conversation context
/cost — Show token usage stats
/stop — Cancel current generation
/save — Save current session
/sessions — List saved sessions
/resume <id> — Resume a saved session
/delete <id> — Delete a saved session
/version — Show version info
/help — Show this help`
    );
  },
  "/page": async () => {
    const content = await sendToBackground("get-page-content");
    if (content.error) {
      addErrorBubble(content.error);
    } else {
      addPageContextBubble(content);
      messages.push({
        role: "user",
        content: `[Page content from ${content.url}]\nTitle: ${content.title}\n${content.text}`,
      });
    }
  },
  "/links": async () => {
    const data = await sendToTab("extract-links");
    if (data.error) {
      addErrorBubble(data.error);
    } else {
      const list = (data.links || []).slice(0, 30).map((l) => `- [${l.text}](${l.href})`).join("\n");
      addAssistantBubble().innerHTML = renderMarkdown(`**Links found:**\n${list || "None"}`);
    }
  },
  "/code": async () => {
    const data = await sendToTab("extract-code");
    if (data.error) {
      addErrorBubble(data.error);
    } else {
      const blocks = (data.codeBlocks || []).slice(0, 10);
      let md = `**Code blocks found: ${blocks.length}**\n`;
      blocks.forEach((b, i) => {
        md += `\n\`\`\`${b.lang}\n${b.text.substring(0, 500)}\n\`\`\`\n`;
      });
      addAssistantBubble().innerHTML = renderMarkdown(md);
    }
  },
  "/forms": async () => {
    const data = await sendToTab("extract-forms");
    if (data.error) {
      addErrorBubble(data.error);
    } else {
      const forms = data.forms || [];
      let md = `**Forms found: ${forms.length}**\n`;
      forms.forEach((f, i) => {
        md += `\n**Form ${i + 1}** (action: ${f.action || "none"})\n`;
        (f.inputs || []).forEach((inp) => {
          md += `  - ${inp.type || "text"}: ${inp.name || inp.id || "unnamed"}\n`;
        });
      });
      addAssistantBubble().innerHTML = renderMarkdown(md);
    }
  },
  "/compact": () => {
    if (messages.length <= 4) {
      addAssistantBubble().textContent = "Conversation too short to compact.";
      return;
    }
    const recent = messages.slice(-4);
    const old = messages.slice(0, -4);
    const summary = old
      .filter((m) => m.role !== "tool")
      .map((m) => `${m.role}: ${(m.content || "").substring(0, 80)}`)
      .join("\n");
    messages = [
      { role: "system", content: `[Compacted earlier context]\n${summary}` },
      ...recent,
    ];
    addAssistantBubble().innerHTML = renderMarkdown(
      `**Compacted** ${old.length} messages → summary. Recent ${recent.length} messages kept.`
    );
  },
  "/cost": () => {
    const elapsed = ((Date.now() - sessionStart) / 1000).toFixed(1);
    addAssistantBubble().innerHTML = renderMarkdown(
      `**Session Stats:**
- Turns: ${totalTurns}
- Tokens: ${totalTokens.toLocaleString()}
- Messages in context: ${messages.length}
- Elapsed: ${elapsed}s
- Cost: FREE` + (USE_CLOUD_API ? ' (Cloud)' : ' (Ollama)') + `
- Model: ${currentModel}`
    );
  },
  "/stop": () => {
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    isStreaming = false;
    sendBtn.disabled = false;
    addAssistantBubble().textContent = "Stopped.";
  },
  "/version": () => {
    addAssistantBubble().innerHTML = renderMarkdown(
      `**Claw Agent** v2.0.0\nChrome Extension (MV3)\nModel: ${currentModel}\n` + (USE_CLOUD_API ? `Cloud: ${OPENROUTER_API_BASE}` : `Ollama: ${ollamaUrl}`)
    );
  },
  "/save": async () => {
    if (messages.length < 2) {
      addAssistantBubble().textContent = "Nothing to save yet.";
      return;
    }
    const id = Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
    const firstUser = messages.find(m => m.role === "user");
    const title = firstUser ? (firstUser.content || "").substring(0, 60) : "Untitled";
    const session = { id, title, model: currentModel, messages, totalTokens, totalTurns, savedAt: Date.now() };
    const stored = (await chrome.storage.local.get("sessions")).sessions || {};
    stored[id] = session;
    await chrome.storage.local.set({ sessions: stored });
    addAssistantBubble().innerHTML = renderMarkdown(`**Session saved** as \`${id}\`\nTitle: ${title}`);
  },
  "/sessions": async () => {
    const stored = (await chrome.storage.local.get("sessions")).sessions || {};
    const keys = Object.keys(stored);
    if (!keys.length) {
      addAssistantBubble().textContent = "No saved sessions.";
      return;
    }
    let md = "**Saved Sessions:**\n";
    keys.sort((a, b) => (stored[b].savedAt || 0) - (stored[a].savedAt || 0));
    for (const k of keys.slice(0, 20)) {
      const s = stored[k];
      const date = new Date(s.savedAt || 0).toLocaleDateString();
      md += `- \`${k}\` — ${s.title || "Untitled"} (${s.totalTurns || 0} turns, ${date})\n`;
    }
    md += "\nUse `/resume <id>` to restore.";
    addAssistantBubble().innerHTML = renderMarkdown(md);
  },
  "/resume": async () => {
    const arg = inputEl.dataset.lastCmd?.split(" ").slice(1).join(" ").trim();
    const stored = (await chrome.storage.local.get("sessions")).sessions || {};
    const keys = Object.keys(stored);

    // No arg — list available sessions to help the user pick
    if (!arg) {
      if (!keys.length) {
        addAssistantBubble().textContent = "No saved sessions. Use /save first.";
        return;
      }
      let md = "**Pick a session to resume:**\n";
      keys.sort((a, b) => (stored[b].savedAt || 0) - (stored[a].savedAt || 0));
      for (const k of keys.slice(0, 10)) {
        const s = stored[k];
        const date = new Date(s.savedAt || 0).toLocaleDateString();
        md += `- \`${k}\` — ${s.title || "Untitled"} (${s.totalTurns || 0} turns, ${date})\n`;
      }
      md += "\nType `/resume <id>` with the first few chars of the ID.";
      addAssistantBubble().innerHTML = renderMarkdown(md);
      return;
    }

    const match = keys.find(k => k.startsWith(arg));
    if (!match) {
      addAssistantBubble().textContent = `No session found matching "${arg}".`;
      return;
    }
    const s = stored[match];
    messages = s.messages || [];
    totalTokens = s.totalTokens || 0;
    totalTurns = s.totalTurns || 0;
    currentModel = s.model || currentModel;
    sessionStart = Date.now();
    // Replay messages to UI
    messagesEl.innerHTML = "";
    for (const m of messages) {
      if (m.role === "user") addUserBubble(m.content || "");
      else if (m.role === "assistant" && m.content) {
        addAssistantBubble().innerHTML = renderMarkdown(m.content);
      }
    }
    addAssistantBubble().innerHTML = renderMarkdown(`**Session restored:** ${s.title || match}\n${messages.length} messages, ${totalTurns} turns`);
  },
  "/delete": async () => {
    const arg = inputEl.dataset.lastCmd?.split(" ").slice(1).join(" ").trim();
    if (!arg) {
      addAssistantBubble().textContent = "Usage: /delete <session-id>";
      return;
    }
    const stored = (await chrome.storage.local.get("sessions")).sessions || {};
    const match = Object.keys(stored).find(k => k.startsWith(arg));
    if (!match) {
      addAssistantBubble().textContent = `No session found matching "${arg}".`;
      return;
    }
    delete stored[match];
    await chrome.storage.local.set({ sessions: stored });
    addAssistantBubble().textContent = `Session "${match}" deleted.`;
  },
};

// ============================================================================
// Event Handlers
// ============================================================================
function send() {
  const text = inputEl.value.trim();
  if (!text || isStreaming) return;
  inputEl.value = "";
  inputEl.style.height = "40px";

  // Check slash commands
  const cmd = text.split(" ")[0].toLowerCase();
  if (SLASH_COMMANDS[cmd]) {
    inputEl.dataset.lastCmd = text;  // Store full command for /resume, /delete args
    SLASH_COMMANDS[cmd]();
    return;
  }

  streamChat(text);
}

sendBtn.onclick = send;
inputEl.onkeydown = (e) => {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    send();
  }
};

// Stop button — abort running agent and hide page banner
stopBtn.onclick = () => {
  if (abortController) {
    abortController.abort();
    abortController = null;
  }
  isStreaming = false;
  sendBtn.disabled = false;
  stopBtn.style.display = "none";
  sendToTab("hide-control-banner").catch(() => {});
  addAssistantBubble().textContent = "Stopped.";
};
inputEl.oninput = () => {
  inputEl.style.height = "40px";
  inputEl.style.height = Math.min(inputEl.scrollHeight, 150) + "px";
};

// Quick action buttons
document.querySelectorAll(".quick-btn").forEach((btn) => {
  btn.onclick = () => {
    const prompt = btn.dataset.prompt;
    if (prompt) streamChat(prompt);
  };
});

// New chat button
document.getElementById("newChatBtn").onclick = () => SLASH_COMMANDS["/clear"]();

// Settings toggle
document.getElementById("settingsBtn").onclick = () => {
  document.getElementById("settingsPanel").classList.toggle("hidden");
};

// Save settings
document.getElementById("saveSettingsBtn").onclick = () => {
  ollamaUrl = document.getElementById("ollamaUrl").value.replace(/\/$/, "");
  customSystemPrompt = document.getElementById("systemPrompt").value;
  mode = document.getElementById("modeSelect").value;
  document.getElementById("modeLabel").textContent =
    mode === "act" ? "Act without asking" : mode === "suggest" ? "Suggest only" : "Ask before acting";

  // Save to storage
  chrome.storage.local.set({ ollamaUrl, customSystemPrompt, mode, currentModel });
  document.getElementById("settingsPanel").classList.add("hidden");
};

// Add custom model
document.getElementById("addModelBtn").onclick = () => {
  const name = document.getElementById("customModel").value.trim();
  if (!name) return;
  const select = document.getElementById("modelSelect");
  const opt = document.createElement("option");
  opt.value = name;
  opt.textContent = name;
  select.appendChild(opt);
  select.value = name;
  currentModel = name;
  document.getElementById("customModel").value = "";
  chrome.storage.local.set({ currentModel });
};

// Model change
document.getElementById("modelSelect").onchange = (e) => {
  currentModel = e.target.value;
  chrome.storage.local.set({ currentModel });
};

// Fetch available models
document.getElementById("fetchModelsBtn").onclick = async () => {
  if (USE_CLOUD_API) {
    const select = document.getElementById("modelSelect");
    const current = currentModel;
    select.innerHTML = "";
    CLOUD_MODELS.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m;
      const short = m.split("/").pop();
      opt.textContent = short.length > 25 ? short.substring(0, 22) + "..." : short;
      select.appendChild(opt);
    });
    if (select.querySelector(`option[value="${current}"]`)) {
      select.value = current;
    }
    addAssistantBubble().innerHTML = renderMarkdown(`**Models refreshed** — ${CLOUD_MODELS.length} cloud models available.`);
    return;
  }
  try {
    const resp = await fetch(`${ollamaUrl}/api/tags`);
    const data = await resp.json();
    const select = document.getElementById("modelSelect");
    const current = select.value;
    select.innerHTML = "";
    (data.models || []).forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m.name;
      opt.textContent = m.name.length > 25 ? m.name.substring(0, 22) + "..." : m.name;
      select.appendChild(opt);
    });
    // Restore selection
    if (select.querySelector(`option[value="${current}"]`)) {
      select.value = current;
    }
  } catch (e) {
    addErrorBubble(`Cannot reach Ollama at ${ollamaUrl}: ${e.message}`);
  }
};

// Read page button
document.getElementById("readPageBtn").onclick = async () => {
  const content = await sendToBackground("get-page-content");
  if (content.error) {
    addErrorBubble(content.error);
  } else {
    clearWelcome();
    addPageContextBubble(content);
    messages.push({
      role: "user",
      content: `[Page content from ${content.url}]\nTitle: ${content.title}\n${content.text.substring(0, 10000)}`,
    });
  }
};

// Attach context button (+) — file picker for images/text + screenshot
document.getElementById("screenshotBtn").onclick = () => {
  // Show a small action menu
  let menu = document.getElementById("_attachMenu");
  if (menu) { menu.remove(); return; } // toggle off
  menu = document.createElement("div");
  menu.id = "_attachMenu";
  menu.style.cssText = "position:absolute;bottom:70px;right:12px;background:#ffffff;border:1px solid #e5e2dd;border-radius:8px;padding:4px 0;z-index:100;min-width:160px;box-shadow:0 4px 12px rgba(0,0,0,.12);";
  const items = [
    { label: "📷 Screenshot page", action: "screenshot" },
    { label: "📎 Attach file", action: "file" },
  ];
  for (const item of items) {
    const btn = document.createElement("div");
    btn.textContent = item.label;
    btn.style.cssText = "padding:8px 14px;cursor:pointer;color:#1a1a1a;font-size:13px;";
    btn.onmouseenter = () => btn.style.background = "#f0ede8";
    btn.onmouseleave = () => btn.style.background = "none";
    btn.onclick = async () => {
      menu.remove();
      if (item.action === "screenshot") {
        try {
          const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
          if (!tab) { addErrorBubble("No active tab"); return; }
          const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: "png" });
          clearWelcome();
          const d = document.createElement("div");
          d.className = "msg user";
          d.innerHTML = `<div style="font-size:12px;color:rgba(255,255,255,.75);margin-bottom:4px;">📷 Screenshot attached</div><img src="${dataUrl}" style="max-width:100%;border-radius:6px;" />`;
          messagesEl.appendChild(d);
          scrollToBottom();
          messages.push({ role: "user", content: `[Screenshot of tab: ${tab.title || tab.url}]\n(Image data attached as base64 PNG — ${Math.round(dataUrl.length / 1024)}KB)` });
        } catch (e) {
          addErrorBubble("Screenshot failed: " + e.message);
        }
      } else if (item.action === "file") {
        const input = document.createElement("input");
        input.type = "file";
        input.accept = "image/*,.txt,.md,.json,.csv,.js,.py,.html,.css,.log";
        input.onchange = async () => {
          const file = input.files[0];
          if (!file) return;
          clearWelcome();
          if (file.type.startsWith("image/")) {
            const reader = new FileReader();
            reader.onload = () => {
              const d = document.createElement("div");
              d.className = "msg user";
              d.innerHTML = `<div style="font-size:12px;color:rgba(255,255,255,.75);margin-bottom:4px;">📎 ${esc(file.name)}</div><img src="${reader.result}" style="max-width:100%;border-radius:6px;" />`;
              messagesEl.appendChild(d);
              scrollToBottom();
              messages.push({ role: "user", content: `[Attached image: ${file.name}, ${Math.round(file.size / 1024)}KB]` });
            };
            reader.readAsDataURL(file);
          } else {
            const text = await file.text();
            const preview = text.substring(0, 8000);
            const d = document.createElement("div");
            d.className = "msg user";
            d.innerHTML = `<div style="font-size:12px;color:rgba(255,255,255,.75);margin-bottom:4px;">📎 ${esc(file.name)} (${Math.round(file.size / 1024)}KB)</div><pre style="max-height:200px;overflow:auto;font-size:11px;">${esc(preview)}</pre>`;
            messagesEl.appendChild(d);
            scrollToBottom();
            messages.push({ role: "user", content: `[Attached file: ${file.name}]\n${preview}` });
          }
        };
        input.click();
      }
    };
    menu.appendChild(btn);
  }
  document.body.appendChild(menu);
  // Close on click outside
  const closeMenu = (e) => { if (!menu.contains(e.target)) { menu.remove(); document.removeEventListener("click", closeMenu); } };
  setTimeout(() => document.addEventListener("click", closeMenu), 0);
};

// Mode indicator click
document.getElementById("modeIndicator").onclick = () => {
  const modes = ["act", "suggest", "ask"];
  const labels = { act: "Act without asking", suggest: "Suggest only", ask: "Ask before acting" };
  const idx = modes.indexOf(mode);
  mode = modes[(idx + 1) % modes.length];
  document.getElementById("modeLabel").textContent = labels[mode];
  chrome.storage.local.set({ mode });
};

// Listen for context menu / background messages (including stop-agent from page banner)
chrome.runtime.onMessage.addListener((message) => {
  if (message.type === "stop-agent") {
    // Page banner "Stop" button was clicked — abort the running agent
    if (abortController) {
      abortController.abort();
      abortController = null;
    }
    isStreaming = false;
    sendBtn.disabled = false;
    stopBtn.style.display = "none";
    addAssistantBubble().textContent = "Stopped by page control.";
    return;
  }

  if (message.type === "context-prompt") {
    if (message.readPage) {
      // Read page first, then send prompt
      sendToBackground("get-page-content").then((content) => {
        if (!content.error) {
          messages.push({
            role: "user",
            content: `[Page: ${content.title}]\n${content.text.substring(0, 10000)}`,
          });
        }
        streamChat(message.prompt);
      });
    } else {
      streamChat(message.prompt);
    }
  }
});

// ============================================================================
// Init — Load saved settings
// ============================================================================
chrome.storage.local.get(["ollamaUrl", "customSystemPrompt", "mode", "currentModel"], (data) => {
  if (data.ollamaUrl) {
    ollamaUrl = data.ollamaUrl;
    document.getElementById("ollamaUrl").value = ollamaUrl;
  }
  if (data.customSystemPrompt) {
    customSystemPrompt = data.customSystemPrompt;
    document.getElementById("systemPrompt").value = customSystemPrompt;
  }
  if (data.mode) {
    mode = data.mode;
    const labels = { act: "Act without asking", suggest: "Suggest only", ask: "Ask before acting" };
    document.getElementById("modeLabel").textContent = labels[mode] || mode;
    document.getElementById("modeSelect").value = mode;
  }
  if (data.currentModel) {
    currentModel = data.currentModel;
    const select = document.getElementById("modelSelect");
    if (!select.querySelector(`option[value="${data.currentModel}"]`)) {
      const opt = document.createElement("option");
      opt.value = data.currentModel;
      opt.textContent = data.currentModel;
      select.appendChild(opt);
    }
    select.value = data.currentModel;
  }
});

// Check connectivity on load
(async () => {
  if (USE_CLOUD_API) {
    // Cloud mode — populate model dropdown with cloud models
    const select = document.getElementById("modelSelect");
    const current = currentModel;
    select.innerHTML = "";
    CLOUD_MODELS.forEach((m) => {
      const opt = document.createElement("option");
      opt.value = m;
      const short = m.split("/").pop();
      opt.textContent = short.length > 25 ? short.substring(0, 22) + "..." : short;
      select.appendChild(opt);
    });
    if (select.querySelector(`option[value="${current}"]`)) {
      select.value = current;
    } else if (select.options.length) {
      currentModel = select.options[0].value;
      select.value = currentModel;
    }
    // Update UI for cloud mode
    const banner = document.getElementById("riskBanner");
    if (banner) banner.innerHTML = '<strong>CLOUD MODE:</strong> Connected to Claw AI council via OpenRouter. 14 models available.';
  } else {
    // Local Ollama mode
    try {
      const resp = await fetch(`${ollamaUrl}/api/tags`, { signal: AbortSignal.timeout(3000) });
      if (resp.ok) {
        const data = await resp.json();
        const select = document.getElementById("modelSelect");
        const current = currentModel;
        select.innerHTML = "";
        (data.models || []).forEach((m) => {
          const opt = document.createElement("option");
          opt.value = m.name;
          opt.textContent = m.name.length > 25 ? m.name.substring(0, 22) + "..." : m.name;
          select.appendChild(opt);
        });
        if (select.querySelector(`option[value="${current}"]`)) {
          select.value = current;
        } else if (select.options.length) {
          currentModel = select.options[0].value;
        }
      }
    } catch {
      addErrorBubble("Cannot connect to Ollama. Make sure it's running at " + ollamaUrl);
    }
  }
})();

// ============================================================================
// Auto-save session on panel close / navigate away
// ============================================================================
window.addEventListener("beforeunload", () => {
  if (messages.length >= 2) {
    const firstUser = messages.find(m => m.role === "user");
    const title = firstUser ? (firstUser.content || "").substring(0, 60) : "Auto-saved";
    chrome.storage.local.set({
      _autosave: {
        messages,
        totalTokens,
        totalTurns,
        model: currentModel,
        title,
        savedAt: Date.now(),
      }
    });
  }
});

// Auto-restore last session on load (if panel was closed with an active conversation)
chrome.storage.local.get("_autosave", (data) => {
  if (data._autosave && data._autosave.messages && data._autosave.messages.length >= 2) {
    const s = data._autosave;
    // Only restore if it's recent (< 1 hour old)
    if (Date.now() - (s.savedAt || 0) < 3600000) {
      messages = s.messages;
      totalTokens = s.totalTokens || 0;
      totalTurns = s.totalTurns || 0;
      if (s.model) currentModel = s.model;
      // Replay to UI
      for (const m of messages) {
        if (m.role === "user") addUserBubble(m.content || "");
        else if (m.role === "assistant" && m.content) {
          addAssistantBubble().innerHTML = renderMarkdown(m.content);
        }
      }
      addAssistantBubble().innerHTML = renderMarkdown(
        `*Session auto-restored (${messages.length} messages, ${totalTurns} turns)*\nType /clear to start fresh.`
      );
    }
    // Clear autosave after restore attempt
    chrome.storage.local.remove("_autosave");
  }
});

inputEl.focus();
