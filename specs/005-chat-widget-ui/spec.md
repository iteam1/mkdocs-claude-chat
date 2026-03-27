# Feature Specification: Chat Widget UI

**Feature Branch**: `005-chat-widget-ui`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "implement frontend widget chat.js + chat.css i want it like a circle icon can be move around any where on screen and when i open, a chatbox on right will appear"

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Open & Close the Chat Panel (Priority: P1)

A documentation reader notices a floating circle button on the page and clicks it to open a chat panel. They can ask Claude a question about the docs and close the panel when done.

**Why this priority**: The open/close interaction is the entry point to the entire feature. Without it, nothing else is accessible.

**Independent Test**: Load any MkDocs page with the plugin enabled, click the circle button, confirm the chat panel appears on the right side of the screen and can be dismissed.

**Acceptance Scenarios**:

1. **Given** the page is loaded, **When** the user looks at the page, **Then** a circular floating button is visible in the bottom-right corner.
2. **Given** the panel is closed, **When** the user clicks the circle button, **Then** a chat panel slides in from the right side of the screen.
3. **Given** the panel is open, **When** the user clicks the circle button again or the close button inside the panel, **Then** the panel closes.
4. **Given** the panel is open, **When** the user clicks outside the panel area, **Then** the panel remains open (not dismissed accidentally).

---

### User Story 2 — Ask a Question and Receive a Streamed Answer (Priority: P1)

A reader types a question in the chat panel and sends it. They see Claude's answer stream in progressively, similar to how modern AI chat interfaces render responses.

**Why this priority**: This is the core value of the widget. If asking and receiving answers does not work, the widget serves no purpose.

**Independent Test**: With the chat panel open, type a question and press Enter. A response streams into the panel and completes without errors.

**Acceptance Scenarios**:

1. **Given** the panel is open, **When** the user types a question and presses Enter or clicks Send, **Then** a loading indicator appears and the answer begins streaming into the chat.
2. **Given** a response is streaming, **When** new text arrives, **Then** it is appended to the message in real time.
3. **Given** the stream is complete, **When** the final sentinel is received, **Then** the loading indicator disappears and the input is re-enabled.
4. **Given** the server returns an error, **When** the error is received, **Then** a human-readable error message is shown in the chat and the input is re-enabled.
5. **Given** a response is streaming, **When** the user tries to send another message, **Then** the input is disabled until the current stream finishes.

---

### User Story 3 — Drag the Circle Button to Any Position (Priority: P2)

A reader finds the default button position conflicts with a page element (sticky footer, cookie banner). They drag the circle button to a more convenient spot, where it stays for the session.

**Why this priority**: Drag-to-move is a polish feature. The chat works without it, but it prevents the widget from covering important page content.

**Independent Test**: Click and drag the circle button from its default position to another part of the screen, release, and confirm it stays at the new position. The chat panel still opens correctly from the new location.

**Acceptance Scenarios**:

1. **Given** the circle button is visible, **When** the user clicks and drags it, **Then** the button follows the cursor smoothly.
2. **Given** the user releases the drag, **Then** the button stays at the released position for the rest of the session.
3. **Given** the button is dragged near a screen edge, **Then** it stays within the viewport boundaries.
4. **Given** the button is pressed and released without dragging, **Then** the chat panel opens or closes normally (tap is not treated as a drag).

---

### Edge Cases

- What if the backend server is unavailable? → Display a clear message ("Chat is unavailable — server not running") in the panel.
- What if the user submits an empty message? → The Send button and Enter key are ignored when the input is blank.
- What if the screen is very narrow (mobile)? → The panel takes the full viewport width on screens narrower than 480 px.
- What if message history is very long? → The panel content area scrolls; the page layout is unaffected.
- What if the user rapidly toggles the panel open/closed? → Animations complete gracefully without stacking or glitching.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The widget MUST render a circular floating button on every documentation page where the plugin is enabled.
- **FR-002**: Clicking the button MUST open a chat panel anchored to the right side of the viewport.
- **FR-003**: The chat panel MUST contain a message history area, a text input field, a Send button, and a close control.
- **FR-004**: Submitting a message MUST send it to the chat backend and display the streamed response token-by-token as it arrives.
- **FR-005**: The text input MUST be disabled while a response is streaming to prevent concurrent requests.
- **FR-006**: Every chat request sent to the backend MUST include the `llmstxt_url` value injected by the plugin at page load.
- **FR-007**: The circle button MUST be draggable to any position within the viewport.
- **FR-008**: The dragged button position MUST persist within the current session (survives panel open/close cycles).
- **FR-009**: The widget MUST not shift or alter the layout of any existing page content.
- **FR-010**: The widget MUST display a human-readable error message when the backend is unreachable.
- **FR-011**: The chat panel message area MUST be independently scrollable when content overflows.
- **FR-012**: A drag gesture and a tap/click gesture MUST be distinguishable so that dragging never accidentally opens or closes the panel.

### Key Entities

- **Circle Button**: The persistent floating trigger; carries drag position state and open/closed toggle state.
- **Chat Panel**: The side panel containing message history, text input, and controls.
- **Message**: A single conversation turn — either a user question or a Claude answer; answers support progressive text append during streaming.
- **Chat Config**: Runtime values (`llmstxt_url`, `chat_title`, backend URL) injected by the MkDocs plugin into each page.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The first streamed character of a Claude response appears within 5 seconds of sending a question on a local dev server.
- **SC-002**: The panel open and close animations complete in under 300 ms.
- **SC-003**: The draggable button stays within the viewport on all screen sizes ≥ 320 px wide.
- **SC-004**: The widget introduces zero layout shift to existing page content.
- **SC-005**: An error message appears within 3 seconds when the backend is unreachable.
- **SC-006**: All configurable values (server URL, `llmstxt_url`, chat title) are sourced from the plugin-injected config — no values are hardcoded in the widget.

## Assumptions

- The MkDocs plugin injects a `window.__CLAUDE_CHAT_CONFIG__` object with `llmstxt_url`, `chat_title`, `position`, and the backend base URL before the widget script runs.
- The chat backend runs on `http://localhost:8001` during `mkdocs serve`; the widget does not manage the backend lifecycle.
- No authentication is required to reach the backend (local development use only).
- The widget is delivered as a single `chat.js` and a single `chat.css` — no build tools, no bundler, no external CDN dependencies at runtime.
- Conversation history is stored in memory only and resets on full page reload.
- The default button resting position is the bottom-right corner of the viewport.
- Markdown rendering in Claude responses is out of scope for v1; plain text output is acceptable.
