// @ts-check
const vscode = require("vscode");
const { spawn } = require("child_process");
const path = require("path");

/**
 * Claw Agent VS Code Extension
 * Claude Code-style agent chat panel inside VS Code.
 */

/** @param {vscode.ExtensionContext} context */
function activate(context) {
  console.log("Claw Agent extension activated");

  const provider = new ClawChatViewProvider(context);
  context.subscriptions.push(
    vscode.window.registerWebviewViewProvider("claw.chatView", provider, {
      webviewOptions: { retainContextWhenHidden: true },
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("claw.openChat", () => {
      vscode.commands.executeCommand("claw.chatView.focus");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("claw.prompt", async () => {
      const prompt = await vscode.window.showInputBox({
        prompt: "Ask Claw Agent...",
        placeHolder: "e.g., explain this codebase",
      });
      if (prompt) {
        provider.sendMessage(prompt);
        vscode.commands.executeCommand("claw.chatView.focus");
      }
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("claw.explainSelection", () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const sel = editor.document.getText(editor.selection);
      const file = path.basename(editor.document.fileName);
      provider.sendMessage(`Explain this code from ${file}:\n\`\`\`\n${sel}\n\`\`\``);
      vscode.commands.executeCommand("claw.chatView.focus");
    })
  );

  context.subscriptions.push(
    vscode.commands.registerCommand("claw.fixSelection", () => {
      const editor = vscode.window.activeTextEditor;
      if (!editor) return;
      const sel = editor.document.getText(editor.selection);
      const file = path.basename(editor.document.fileName);
      provider.sendMessage(`Fix any bugs in this code from ${file}:\n\`\`\`\n${sel}\n\`\`\``);
      vscode.commands.executeCommand("claw.chatView.focus");
    })
  );

  // Clean up on deactivate
  context.subscriptions.push({ dispose: () => provider.dispose() });
}

class ClawChatViewProvider {
  /** @param {vscode.ExtensionContext} context */
  constructor(context) {
    this._context = context;
    /** @type {vscode.WebviewView | undefined} */
    this._view = undefined;
    /** @type {import("child_process").ChildProcess | undefined} */
    this._process = undefined;
    this._buffer = "";
    this._spawning = false;
    this._disposed = false;
    /** @type {vscode.Disposable[]} */
    this._viewListeners = [];
  }

  dispose() {
    this._disposed = true;
    this._killProcess();
    this._disposeViewListeners();
  }

  _disposeViewListeners() {
    for (const d of this._viewListeners) d.dispose();
    this._viewListeners = [];
  }

  /** @param {vscode.WebviewView} webviewView */
  resolveWebviewView(webviewView) {
    // Dispose old listeners to prevent stacking on re-resolve
    this._disposeViewListeners();
    this._view = webviewView;

    webviewView.webview.options = { enableScripts: true };
    webviewView.webview.html = this._getHtml();

    this._viewListeners.push(
      webviewView.webview.onDidReceiveMessage((message) => {
        if (message.type === "send") this.sendMessage(message.text);
        else if (message.type === "clear") {
          this._killProcess();
          this._postToWebview({ type: "cleared" });
        } else if (message.type === "newChat") {
          this._killProcess();
          this._postToWebview({ type: "cleared" });
          this._ensureProcess();
        } else if (message.type === "openSettings") {
          vscode.commands.executeCommand("workbench.action.openSettings", "claw");
        } else if (message.type === "exportChat") {
          this._exportChat(message.html);
        } else if (message.type === "attachFile") {
          this._attachFile();
        }
      })
    );

    this._viewListeners.push(
      webviewView.onDidDispose(() => {
        this._view = undefined;
        this._killProcess();
      })
    );

    // Auto-start the bridge so user sees "Ready" immediately
    this._ensureProcess();
  }

  /** @param {string} text */
  sendMessage(text) {
    if (!this._view) return;
    this._postToWebview({ type: "user", text });
    this._ensureProcess();

    if (this._process && this._process.stdin && !this._process.stdin.destroyed) {
      try {
        this._process.stdin.write(JSON.stringify({ type: "chat", content: text }) + "\n");
      } catch {
        this._postToWebview({ type: "error", text: "Bridge not available. Type again to retry." });
      }
    }
  }

  _ensureProcess() {
    if (this._disposed || this._spawning) return;
    if (this._process && !this._process.killed && this._process.exitCode === null) return;

    this._spawning = true;
    this._process = undefined;

    const config = vscode.workspace.getConfiguration("claw");
    const model = config.get("model", "deepseek-v3.1:671b-cloud");
    const ollamaUrl = config.get("ollamaUrl", "http://localhost:11434");
    const cwd = vscode.workspace.workspaceFolders?.[0]?.uri.fsPath || process.cwd();
    const bridgePath = path.join(this._context.extensionPath, "src", "bridge.py");

    // Try full Python path first, fall back to "python"
    const pythonCandidates = [
      "C:\\Program Files\\PyManager\\python.exe",
      "python3",
      "python",
    ];

    let pythonPath = "python";
    for (const candidate of pythonCandidates) {
      try {
        const { execSync } = require("child_process");
        execSync(`"${candidate}" --version`, { stdio: "ignore", timeout: 3000 });
        pythonPath = candidate;
        break;
      } catch { continue; }
    }

    try {
      this._process = spawn(pythonPath, [bridgePath, "--model", model, "--base-url", ollamaUrl], {
        cwd,
        env: { ...process.env },
        stdio: ["pipe", "pipe", "pipe"],
      });
    } catch (e) {
      this._spawning = false;
      this._postToWebview({ type: "error", text: `Failed to start: ${e}` });
      return;
    }

    this._buffer = "";

    this._process.stdout?.on("data", (data) => {
      this._buffer += data.toString();
      const lines = this._buffer.split("\n");
      this._buffer = lines.pop() || "";
      for (const line of lines) {
        if (!line.trim()) continue;
        try { this._postToWebview(JSON.parse(line)); }
        catch { this._postToWebview({ type: "text_delta", text: line }); }
      }
    });

    this._process.stderr?.on("data", (data) => {
      const err = data.toString().trim();
      if (err) {
        console.error("Claw bridge stderr:", err);
        this._postToWebview({ type: "error", text: err.substring(0, 500) });
      }
    });

    // Do NOT auto-respawn on close — that caused the infinite loop
    this._process.on("close", (code) => {
      this._process = undefined;
      this._spawning = false;
      if (code !== 0 && code !== null) {
        this._postToWebview({ type: "status", text: `Exited (${code}) — send a message to restart` });
      }
    });

    this._process.on("error", (err) => {
      this._process = undefined;
      this._spawning = false;
      this._postToWebview({ type: "error", text: err.message });
    });

    this._spawning = false;
    this._postToWebview({ type: "status", text: model });
  }

  async _exportChat(html) {
    const uri = await vscode.window.showSaveDialog({
      filters: { "Text": ["txt"], "Markdown": ["md"] },
      defaultUri: vscode.Uri.file("claw-chat-export.md"),
    });
    if (uri) {
      // Strip HTML tags for plain text export
      const text = (html || "").replace(/<[^>]+>/g, "").replace(/&lt;/g, "<").replace(/&gt;/g, ">").replace(/&amp;/g, "&");
      await vscode.workspace.fs.writeFile(uri, Buffer.from(text, "utf-8"));
      vscode.window.showInformationMessage("Chat exported to " + uri.fsPath);
    }
  }

  async _attachFile() {
    const uris = await vscode.window.showOpenDialog({
      canSelectMany: false,
      filters: { "All Files": ["*"] },
    });
    if (uris && uris.length) {
      const uri = uris[0];
      const data = await vscode.workspace.fs.readFile(uri);
      const name = path.basename(uri.fsPath);
      const text = Buffer.from(data).toString("utf-8");
      // Truncate very large files
      const truncated = text.length > 10000 ? text.substring(0, 10000) + "\n...[truncated]" : text;
      this.sendMessage(`[Attached file: ${name}]\n\`\`\`\n${truncated}\n\`\`\``);
    }
  }

  _killProcess() {
    if (this._process) {
      try {
        this._process.stdin?.end();
        this._process.kill("SIGTERM");
        // Force kill after 2s if still alive
        const p = this._process;
        setTimeout(() => { try { p.kill("SIGKILL"); } catch {} }, 2000);
      } catch {}
      this._process = undefined;
    }
    this._spawning = false;
  }

  /** @param {any} msg */
  _postToWebview(msg) {
    this._view?.webview.postMessage(msg);
  }

  _getHtml() {
    return /* html */ `<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<style>
  :root {
    --bg: var(--vscode-editor-background);
    --fg: var(--vscode-editor-foreground);
    --input-bg: var(--vscode-input-background);
    --input-border: var(--vscode-input-border);
    --btn-bg: var(--vscode-button-background);
    --btn-fg: var(--vscode-button-foreground);
    --btn-hover: var(--vscode-button-hoverBackground);
    --tool-bg: var(--vscode-textBlockQuote-background);
    --accent: var(--vscode-textLink-foreground);
    --dim: var(--vscode-descriptionForeground);
    --badge-bg: var(--vscode-badge-background);
    --badge-fg: var(--vscode-badge-foreground);
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: var(--vscode-font-family);
    font-size: var(--vscode-font-size);
    color: var(--fg); background: var(--bg);
    display: flex; flex-direction: column; height: 100vh; overflow: hidden;
  }

  /* ── Header ── */
  .header {
    padding: 6px 10px;
    border-bottom: 1px solid var(--input-border);
    display: flex; align-items: center; gap: 6px;
    font-size: 11px; color: var(--dim);
    flex-shrink: 0;
  }
  .header .title { font-weight: 600; color: var(--accent); font-size: 13px; }
  .header .status { margin-left: auto; font-size: 11px; }
  .header-actions { display: flex; gap: 2px; margin-left: 6px; }
  .icon-btn {
    background: transparent; border: none; color: var(--dim);
    cursor: pointer; padding: 3px 6px; border-radius: 4px;
    font-size: 14px; line-height: 1; display: flex; align-items: center;
  }
  .icon-btn:hover { background: var(--tool-bg); color: var(--fg); }
  .icon-btn[title]::after { content: none; }

  /* ── Welcome ── */
  .welcome {
    text-align: center; padding: 32px 16px; color: var(--dim);
  }
  .welcome-icon { font-size: 36px; margin-bottom: 8px; }
  .welcome h2 { font-size: 16px; color: var(--fg); margin-bottom: 4px; }
  .welcome p { font-size: 12px; margin-bottom: 16px; }
  .quick-actions { display: flex; flex-wrap: wrap; gap: 6px; justify-content: center; }
  .quick-btn {
    background: var(--tool-bg); border: 1px solid var(--input-border);
    color: var(--fg); padding: 6px 12px; border-radius: 6px;
    cursor: pointer; font-size: 12px; white-space: nowrap;
  }
  .quick-btn:hover { background: var(--btn-bg); color: var(--btn-fg); }

  /* ── Messages ── */
  .messages {
    flex: 1; overflow-y: auto; padding: 12px;
    display: flex; flex-direction: column; gap: 10px;
  }
  .msg { max-width: 100%; line-height: 1.5; }
  .msg.user {
    background: var(--btn-bg); color: var(--btn-fg);
    padding: 8px 12px; border-radius: 8px;
    align-self: flex-end; max-width: 85%;
  }
  .msg.assistant { padding: 4px 0; white-space: pre-wrap; word-wrap: break-word; }
  .msg.tool-call {
    font-size: 12px; padding: 6px 10px;
    background: var(--tool-bg); border-radius: 6px;
    border-left: 3px solid var(--accent);
    font-family: var(--vscode-editor-font-family);
  }
  .tool-name { color: var(--accent); font-weight: 600; }
  .tool-time { color: var(--dim); font-size: 11px; }
  .tool-result { color: var(--dim); font-size: 11px; margin-top: 4px; max-height: 80px; overflow: hidden; }
  .msg.error { color: var(--vscode-errorForeground); font-size: 12px; padding: 4px 0; }
  .msg.system { color: var(--dim); font-size: 12px; padding: 4px 0; font-style: italic; }
  .msg.thinking { color: var(--dim); font-style: italic; display: flex; align-items: center; gap: 6px; }
  .spinner {
    display: inline-block; width: 12px; height: 12px;
    border: 2px solid var(--dim); border-top-color: var(--accent);
    border-radius: 50%; animation: spin 0.8s linear infinite;
  }
  @keyframes spin { to { transform: rotate(360deg); } }

  /* ── Cost bar ── */
  .cost-bar { padding: 4px 12px; font-size: 11px; color: var(--dim); border-top: 1px solid var(--input-border); flex-shrink: 0; }

  /* ── Risk banner ── */
  .risk-banner {
    padding: 4px 12px; font-size: 10px; color: var(--dim);
    background: var(--tool-bg); text-align: center; flex-shrink: 0;
  }

  /* ── Input ── */
  .input-area { padding: 8px 10px; border-top: 1px solid var(--input-border); flex-shrink: 0; }
  .input-row { display: flex; gap: 6px; align-items: flex-end; }
  .input-row textarea {
    flex: 1; background: var(--input-bg); color: var(--fg);
    border: 1px solid var(--input-border); border-radius: 6px;
    padding: 8px 10px; font-family: var(--vscode-font-family);
    font-size: var(--vscode-font-size); resize: none;
    min-height: 36px; max-height: 120px; outline: none;
  }
  .input-row textarea:focus { border-color: var(--accent); }
  .send-btn {
    background: var(--btn-bg); color: var(--btn-fg);
    border: none; border-radius: 6px; width: 34px; height: 34px;
    cursor: pointer; font-size: 16px; font-weight: 700;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
  }
  .send-btn:hover { background: var(--btn-hover); }
  .input-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 4px; }
  .input-actions { display: flex; gap: 2px; }
  .action-btn {
    background: transparent; border: none; color: var(--dim);
    cursor: pointer; padding: 2px 6px; border-radius: 4px; font-size: 14px;
  }
  .action-btn:hover { background: var(--tool-bg); color: var(--fg); }
  .mode-indicator {
    font-size: 11px; color: var(--dim); display: flex; align-items: center; gap: 4px;
  }

  /* ── Disclaimer ── */
  .disclaimer { padding: 3px 12px; font-size: 10px; color: var(--dim); text-align: center; flex-shrink: 0; }

  /* ── Code blocks ── */
  pre { background: var(--tool-bg); padding: 8px; border-radius: 6px; overflow-x: auto; margin: 4px 0; }
  code { background: var(--tool-bg); padding: 1px 4px; border-radius: 3px; }
</style>
</head>
<body>
  <!-- Header -->
  <div class="header">
    <span class="title">⚡ Claw Agent</span>
    <span class="status" id="status">Starting...</span>
    <div class="header-actions">
      <button class="icon-btn" id="newChatBtn" title="New Chat">✚</button>
      <button class="icon-btn" id="exportBtn" title="Export Chat">⤓</button>
      <button class="icon-btn" id="settingsBtn" title="Settings">⚙</button>
    </div>
  </div>

  <!-- Messages -->
  <div class="messages" id="messages">
    <div class="welcome" id="welcome">
      <div class="welcome-icon">⚡</div>
      <h2>Claw Agent</h2>
      <p>Local AI assistant powered by Ollama</p>
      <div class="quick-actions">
        <button class="quick-btn" data-prompt="Explain the current workspace structure">📁 Explain workspace</button>
        <button class="quick-btn" data-prompt="Show me a summary of recent git changes">📝 Git summary</button>
        <button class="quick-btn" data-prompt="Find and fix any bugs in the open file">🐛 Fix bugs</button>
        <button class="quick-btn" data-prompt="Write tests for the current project">🧪 Write tests</button>
      </div>
    </div>
  </div>

  <!-- Cost bar -->
  <div class="cost-bar" id="costBar"></div>

  <!-- Risk banner -->
  <div class="risk-banner">🔒 <strong>LOCAL MODE</strong> — Runs entirely on your machine via Ollama. No data leaves your computer.</div>

  <!-- Input area -->
  <div class="input-area">
    <div class="input-row">
      <textarea id="input" rows="1" placeholder="Ask Claw anything... (Enter to send, / for commands)"></textarea>
      <button class="send-btn" id="sendBtn" title="Send">↑</button>
    </div>
    <div class="input-footer">
      <div class="mode-indicator">
        <span>▷▷</span>
        <span>Act without asking</span>
      </div>
      <div class="input-actions">
        <button class="action-btn" id="attachBtn" title="Attach file">📎</button>
        <button class="action-btn" id="clearBtn" title="Clear conversation">🗑</button>
      </div>
    </div>
  </div>

  <div class="disclaimer">Claw is AI and can make mistakes. Verify important information.</div>

<script>
  const vscode = acquireVsCodeApi();
  const messagesEl = document.getElementById("messages");
  const inputEl = document.getElementById("input");
  const statusEl = document.getElementById("status");
  const costBar = document.getElementById("costBar");
  const welcomeEl = document.getElementById("welcome");

  let curEl = null, curText = "", thinkEl = null;

  function scroll() { messagesEl.scrollTop = messagesEl.scrollHeight; }
  function esc(t) { const d = document.createElement("div"); d.textContent = t; return d.innerHTML; }
  function hideWelcome() { if (welcomeEl) welcomeEl.style.display = "none"; }
  function showWelcome() { if (welcomeEl) welcomeEl.style.display = ""; }

  function addMsg(cls, html) {
    hideWelcome();
    const d = document.createElement("div");
    d.className = "msg " + cls;
    d.innerHTML = html;
    messagesEl.appendChild(d);
    scroll();
    return d;
  }
  function rmThink() { if (thinkEl) { thinkEl.remove(); thinkEl = null; } }

  // Simple markdown rendering
  function renderMd(text) {
    let h = esc(text);
    h = h.replace(/\`\`\`(\\w*)\\n([\\s\\S]*?)\`\`\`/g, '<pre><code>$2</code></pre>');
    h = h.replace(/\`([^\`]+)\`/g, '<code>$1</code>');
    h = h.replace(/\\*\\*(.+?)\\*\\*/g, '<strong>$1</strong>');
    h = h.replace(/\\n/g, '<br>');
    return h;
  }

  // Slash commands handled inside webview
  const SLASH = {
    "/clear": () => { vscode.postMessage({ type: "clear" }); },
    "/new": () => { vscode.postMessage({ type: "newChat" }); },
    "/help": () => {
      addMsg("assistant",
        "<strong>Commands:</strong><br>" +
        "/clear — Clear conversation<br>" +
        "/new — Start new chat (restarts agent)<br>" +
        "/help — Show this help<br>" +
        "/cost — Show token stats<br>" +
        "/compact — Compress context<br>" +
        "/model — Show current model<br>" +
        "/version — Show version<br>" +
        "/save — Save session (sent to agent)<br>" +
        "/sessions — List sessions (sent to agent)<br>" +
        "/resume &lt;id&gt; — Resume session (sent to agent)<br>" +
        "/diff — Show git diff (sent to agent)<br>" +
        "/status — Workspace status (sent to agent)<br>" +
        "Any other text is sent to the agent."
      );
    },
    "/cost": () => { addMsg("assistant", costBar.textContent || "No stats yet."); },
    "/version": () => { addMsg("assistant", "<strong>Claw Agent</strong> v0.1.0 — VS Code Extension"); },
  };

  function send() {
    const t = inputEl.value.trim();
    if (!t) return;
    inputEl.value = ""; inputEl.style.height = "36px";

    // Handle slash commands locally
    const cmd = t.split(" ")[0].toLowerCase();
    if (SLASH[cmd]) { SLASH[cmd](); return; }

    vscode.postMessage({ type: "send", text: t });
  }

  // ── Button handlers ──
  document.getElementById("sendBtn").onclick = send;
  document.getElementById("newChatBtn").onclick = () => { vscode.postMessage({ type: "newChat" }); };
  document.getElementById("clearBtn").onclick = () => { vscode.postMessage({ type: "clear" }); };
  document.getElementById("settingsBtn").onclick = () => { vscode.postMessage({ type: "openSettings" }); };
  document.getElementById("attachBtn").onclick = () => { vscode.postMessage({ type: "attachFile" }); };
  document.getElementById("exportBtn").onclick = () => {
    vscode.postMessage({ type: "exportChat", html: messagesEl.innerText });
  };

  // Quick action buttons
  document.querySelectorAll(".quick-btn").forEach(btn => {
    btn.onclick = () => {
      const prompt = btn.getAttribute("data-prompt");
      if (prompt) {
        inputEl.value = prompt;
        send();
      }
    };
  });

  // ── Keyboard ──
  inputEl.onkeydown = e => { if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); } };
  inputEl.oninput = () => { inputEl.style.height = "36px"; inputEl.style.height = Math.min(inputEl.scrollHeight, 120) + "px"; };

  // ── Message handler ──
  window.addEventListener("message", ev => {
    const m = ev.data;
    switch (m.type) {
      case "user":
        curEl = null; curText = "";
        addMsg("user", esc(m.text));
        thinkEl = addMsg("thinking", '<span class="spinner"></span> Thinking...');
        break;
      case "text_delta":
        rmThink();
        if (!curEl) curEl = addMsg("assistant", "");
        curText += m.text;
        curEl.innerHTML = renderMd(curText);
        scroll();
        break;
      case "tool_start":
        rmThink();
        addMsg("tool-call",
          '<span class="spinner"></span> <span class="tool-name">' + esc(m.name) +
          '</span> <span style="color:var(--dim)">' + esc(m.args || "") + '</span>');
        break;
      case "tool_end": {
        const els = messagesEl.querySelectorAll(".tool-call");
        if (els.length) {
          const last = els[els.length - 1];
          const p = (m.result || "").substring(0, 200);
          last.innerHTML = '✓ <span class="tool-name">' + esc(m.name) + '</span> ' +
            '<span class="tool-time">' + (m.duration_ms||0).toFixed(0) + 'ms</span>' +
            (p ? '<div class="tool-result">' + esc(p) + '</div>' : '');
        }
        scroll(); break;
      }
      case "done":
        rmThink();
        if (m.text && m.text.startsWith("[")) addMsg("system", esc(m.text));
        curEl = null; curText = "";
        break;
      case "cost": costBar.textContent = m.text || ""; break;
      case "status": statusEl.textContent = m.text || ""; break;
      case "error": rmThink(); addMsg("error", "⚠ " + esc(m.text)); break;
      case "cleared":
        // Remove all messages except welcome
        Array.from(messagesEl.children).forEach(c => {
          if (c !== welcomeEl) c.remove();
        });
        curEl = null; curText = "";
        costBar.textContent = ""; statusEl.textContent = "Ready";
        showWelcome();
        break;
    }
  });
  inputEl.focus();
</script>
</body>
</html>`;
  }
}

function deactivate() {}
module.exports = { activate, deactivate };
