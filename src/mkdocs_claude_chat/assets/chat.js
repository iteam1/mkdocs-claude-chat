/* mkdocs-claude-chat widget */
(function () {
  "use strict";

  // ── Config ────────────────────────────────────────────────────────
  const cfg = Object.assign(
    { backendUrl: "http://localhost:8001", llmstxtUrl: "", chatTitle: "Ask Claude", position: "bottom-right" },
    window.__CLAUDE_CHAT_CONFIG__ || {}
  );

  // ── Constants ─────────────────────────────────────────────────────
  const PANEL_MIN_W = 260;
  const PANEL_MAX_W = () => Math.round(window.innerWidth * 0.85);
  const STORAGE_KEY = "cc-panel-width";

  // ── State ─────────────────────────────────────────────────────────
  let panelOpen = false;
  let panelWidth = parseInt(localStorage.getItem(STORAGE_KEY) || "360", 10);

  // Button drag state
  let buttonX = window.innerWidth - 28 - 16;   // center X (28 = half of 56px btn)
  let buttonY = window.innerHeight - 28 - 16;  // center Y
  let isDragging = false;
  let dragStartX = 0;
  let dragStartY = 0;
  let dragMoved = false;

  // Panel resize state
  let isResizing = false;
  let resizeStartX = 0;
  let resizeStartW = 0;

  // DOM refs (set in init)
  let btn, panel, resizeHandle, messagesEl, inputEl, sendEl, loadingEl;

  // ── Helpers ───────────────────────────────────────────────────────
  function clampPosition(x, y) {
    const half = 28; // half of btn size
    return [
      Math.max(half, Math.min(window.innerWidth - half, x)),
      Math.max(half, Math.min(window.innerHeight - half, y)),
    ];
  }

  function applyButtonPosition() {
    btn.style.left = (buttonX - 28) + "px";
    btn.style.top  = (buttonY - 28) + "px";
    // Remove default bottom/right once we use absolute positioning
    btn.style.bottom = "";
    btn.style.right  = "";
  }

  function scrollToBottom() {
    messagesEl.scrollTop = messagesEl.scrollHeight;
  }

  function applyPanelWidth(w, animate) {
    panelWidth = Math.max(PANEL_MIN_W, Math.min(PANEL_MAX_W(), w));
    if (!animate) {
      panel.style.transition = "none";
      document.body.style.transition = "none";
    }
    document.documentElement.style.setProperty("--cc-panel-width", panelWidth + "px");
    if (!animate) {
      // force reflow then restore transitions
      void panel.offsetWidth;
      panel.style.transition = "";
      document.body.style.transition = "";
    }
    localStorage.setItem(STORAGE_KEY, panelWidth);
  }

  // ── DOM builders ──────────────────────────────────────────────────
  function createButton() {
    const el = document.createElement("button");
    el.id = "claude-chat-btn";
    el.setAttribute("aria-label", "Open chat");
    el.innerHTML = `
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/>
      </svg>`;
    return el;
  }

  function createPanel() {
    const el = document.createElement("div");
    el.id = "claude-chat-panel";
    el.setAttribute("role", "dialog");
    el.setAttribute("aria-label", cfg.chatTitle);
    el.innerHTML = `
      <div id="claude-chat-resize" aria-hidden="true"></div>
      <div class="cc-header">
        <span class="cc-title">${escapeHtml(cfg.chatTitle)}</span>
        <button class="cc-close" aria-label="Close chat">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/>
          </svg>
        </button>
      </div>
      <div class="cc-messages">
        <p class="cc-welcome">Ask a question about this documentation. Claude will answer using the docs as context.</p>
      </div>
      <div class="cc-input-row">
        <input class="cc-input" type="text" placeholder="Ask a question…" autocomplete="off" />
        <button class="cc-send">Send</button>
      </div>`;
    return el;
  }

  function escapeHtml(str) {
    return str.replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  // ── Panel toggle ──────────────────────────────────────────────────
  function togglePanel() {
    panelOpen = !panelOpen;
    if (panelOpen) {
      panel.classList.add("open");
      document.body.classList.add("cc-panel-open");
      btn.setAttribute("aria-label", "Close chat");
      inputEl.focus();
    } else {
      panel.classList.remove("open");
      document.body.classList.remove("cc-panel-open");
      btn.setAttribute("aria-label", "Open chat");
    }
  }

  // ── Message rendering ─────────────────────────────────────────────
  function appendMessage(role, text) {
    const bubble = document.createElement("div");
    bubble.className = role === "user" ? "cc-bubble-user" : "cc-bubble-assistant";
    bubble.textContent = text;
    messagesEl.appendChild(bubble);
    scrollToBottom();
    return bubble;
  }

  function appendChunk(text) {
    let last = messagesEl.querySelector(".cc-bubble-assistant:last-of-type");
    if (!last || last.classList.contains("cc-bubble-error")) {
      last = document.createElement("div");
      last.className = "cc-bubble-assistant";
      messagesEl.appendChild(last);
    }
    last.textContent += text;
    scrollToBottom();
  }

  function appendError(text) {
    const bubble = document.createElement("div");
    bubble.className = "cc-bubble-error";
    bubble.textContent = "⚠ " + text;
    messagesEl.appendChild(bubble);
    scrollToBottom();
  }

  function showLoading() {
    loadingEl = document.createElement("div");
    loadingEl.className = "cc-loading";
    loadingEl.innerHTML = "<span></span><span></span><span></span>";
    messagesEl.appendChild(loadingEl);
    scrollToBottom();
  }

  function hideLoading() {
    if (loadingEl && loadingEl.parentNode) {
      loadingEl.parentNode.removeChild(loadingEl);
      loadingEl = null;
    }
  }

  // ── SSE streaming ─────────────────────────────────────────────────
  async function* streamResponse(question) {
    const res = await fetch(cfg.backendUrl + "/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question, llmstxt_url: cfg.llmstxtUrl }),
    });
    if (!res.ok) {
      throw new Error("Server error: " + res.status);
    }
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buf = "";
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buf += decoder.decode(value, { stream: true });
      const lines = buf.split("\n");
      buf = lines.pop(); // keep incomplete line
      for (const line of lines) {
        const trimmed = line.trim();
        if (trimmed.startsWith("data: ")) {
          yield trimmed.slice(6).trim();
        }
      }
    }
  }

  // ── Send message ──────────────────────────────────────────────────
  async function sendMessage() {
    const question = inputEl.value.trim();
    if (!question) return;

    inputEl.value = "";
    inputEl.disabled = true;
    sendEl.disabled = true;

    appendMessage("user", question);
    showLoading();

    try {
      for await (const payload of streamResponse(question)) {
        if (payload === "[DONE]") {
          break;
        }
        try {
          const data = JSON.parse(payload);
          if (data.text) {
            hideLoading();
            appendChunk(data.text);
          } else if (data.error) {
            hideLoading();
            appendError(data.error);
            break;
          }
        } catch (_) {
          // non-JSON line, ignore
        }
      }
    } catch (err) {
      hideLoading();
      appendError("Chat unavailable — " + (err.message || "server not running"));
    } finally {
      hideLoading();
      inputEl.disabled = false;
      sendEl.disabled = false;
      inputEl.focus();
    }
  }

  // ── Drag handlers ─────────────────────────────────────────────────
  function onPointerDown(e) {
    isDragging = true;
    dragMoved = false;
    dragStartX = e.clientX;
    dragStartY = e.clientY;
    btn.setPointerCapture(e.pointerId);
    btn.classList.add("dragging");
  }

  function onPointerMove(e) {
    if (!isDragging) return;
    const dx = e.clientX - dragStartX;
    const dy = e.clientY - dragStartY;
    if (Math.hypot(dx, dy) >= 5) {
      dragMoved = true;
    }
    const [cx, cy] = clampPosition(buttonX + dx, buttonY + dy);
    btn.style.left = (cx - 28) + "px";
    btn.style.top  = (cy - 28) + "px";
    btn.style.bottom = "";
    btn.style.right  = "";
  }

  function onPointerUp(e) {
    if (!isDragging) return;
    isDragging = false;
    btn.classList.remove("dragging");
    btn.releasePointerCapture(e.pointerId);

    const dx = e.clientX - dragStartX;
    const dy = e.clientY - dragStartY;
    [buttonX, buttonY] = clampPosition(buttonX + dx, buttonY + dy);
    btn.style.left = (buttonX - 28) + "px";
    btn.style.top  = (buttonY - 28) + "px";

    if (!dragMoved) {
      togglePanel();
    }
  }

  // ── Resize handlers ───────────────────────────────────────────────
  function onResizeDown(e) {
    e.preventDefault();
    isResizing = true;
    resizeStartX = e.clientX;
    resizeStartW = panelWidth;
    resizeHandle.classList.add("resizing");
    document.body.classList.add("cc-resizing");
    resizeHandle.setPointerCapture(e.pointerId);
  }

  function onResizeMove(e) {
    if (!isResizing) return;
    const dx = resizeStartX - e.clientX;   // dragging left → panel grows
    applyPanelWidth(resizeStartW + dx, false);
  }

  function onResizeUp(e) {
    if (!isResizing) return;
    isResizing = false;
    resizeHandle.classList.remove("resizing");
    document.body.classList.remove("cc-resizing");
    resizeHandle.releasePointerCapture(e.pointerId);
  }

  // ── Init ──────────────────────────────────────────────────────────
  function init() {
    btn = createButton();
    panel = createPanel();

    document.body.appendChild(btn);
    document.body.appendChild(panel);

    messagesEl    = panel.querySelector(".cc-messages");
    inputEl       = panel.querySelector(".cc-input");
    sendEl        = panel.querySelector(".cc-send");
    resizeHandle  = panel.querySelector("#claude-chat-resize");

    // Apply initial button position
    applyButtonPosition();

    // Apply saved panel width
    applyPanelWidth(panelWidth, false);

    // Pointer events for button drag + tap
    btn.addEventListener("pointerdown", onPointerDown);
    btn.addEventListener("pointermove", onPointerMove);
    btn.addEventListener("pointerup",   onPointerUp);

    // Pointer events for panel resize
    resizeHandle.addEventListener("pointerdown", onResizeDown);
    resizeHandle.addEventListener("pointermove", onResizeMove);
    resizeHandle.addEventListener("pointerup",   onResizeUp);

    // Close button
    panel.querySelector(".cc-close").addEventListener("click", togglePanel);

    // Send on button click
    sendEl.addEventListener("click", sendMessage);

    // Send on Enter (not Shift+Enter)
    inputEl.addEventListener("keydown", function (e) {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
      }
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
