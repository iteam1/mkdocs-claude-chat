# Research: Chat Widget UI

**Branch**: `005-chat-widget-ui` | **Date**: 2026-03-27

## Findings

| Decision | Choice | Rationale |
|---|---|---|
| JS approach | Vanilla ES2020+, no build tools | Spec §Assumptions: single file, no bundler; constitution requires no new packages; reduces setup friction for MkDocs users |
| SSE consumption | `fetch` + `ReadableStream` + `TextDecoder` | Backend uses `POST /chat` — `EventSource` only supports GET. `fetch` streams work in all modern browsers |
| Drag implementation | Pointer Events API (`pointerdown/move/up`) | Unified mouse + touch in one API; `setPointerCapture` makes drag reliable even when cursor leaves element |
| Drag vs click distinction | Distance threshold ≥ 5 px | If `pointerup` occurs within 5 px of `pointerdown`, treat as click; otherwise treat as drag. Simple, reliable, no timeout needed |
| Config injection | `on_post_page` hook injects `<script>window.__CLAUDE_CHAT_CONFIG__ = {...};</script>` before `</body>` | Works with any MkDocs theme — no template override required. Plugin inserts it programmatically |
| Panel animation | CSS `transform: translateX()` + `transition` | GPU-composited, zero layout shift. Avoids `width` animation which causes reflow |
| Panel side | Right side, full height, fixed position | Spec FR-002: anchored to the right side of the viewport; does not shift page content |
| Mobile breakpoint | `@media (max-width: 480px)` → panel = 100vw | Spec edge case: full width on narrow screens |
| Viewport clamping for drag | `Math.max/min` on `pointerup` | Clamp button center to `[buttonRadius, viewport - buttonRadius]` on both axes |
| Session persistence of position | JS module-level variable | In-memory only; no `localStorage` (keeps it simple, matches spec "session persistence") |
| Chat history storage | Array in JS module scope | In-memory, resets on reload, matches constitution §XIV |
| Input disable during stream | Set `disabled` attribute | Standard approach; prevents concurrent requests per FR-005 |
| Error display | Error message appended as a chat bubble | Consistent UX — errors appear inline in the conversation |
| Backend URL | Read from `window.__CLAUDE_CHAT_CONFIG__.backendUrl` | Defaults to `http://localhost:8001` when running `mkdocs serve` |

## Alternatives Considered

- **`EventSource`** — rejected because backend requires `POST` (question in body); EventSource is GET-only
- **Dragging via `mousedown/mousemove/mouseup`** — rejected in favor of Pointer Events which handle both mouse and touch in one API without duplicating handlers
- **`localStorage` for drag position** — rejected; spec says session persistence only; localStorage would persist across all documentation sites and could cause surprising behavior
- **CSS `width` transition for panel** — rejected because animating width causes layout reflow; `translateX` is composited and does not affect surrounding content
- **Template override (`overrides/main.html`)** — rejected; requires users to configure `custom_dir` in their `mkdocs.yml`, adding friction; `on_post_page` string injection works universally
- **React/Vue/Lit** — rejected; adds build tooling dependency, contradicts spec assumption of single static file
