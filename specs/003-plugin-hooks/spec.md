# Feature Specification: Plugin Hooks

**Feature Branch**: `003-plugin-hooks`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "implement plugin.py"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Assets are injected into every built page (Priority: P1)

A documentation author adds the plugin to `mkdocs.yml`, runs `mkdocs build`, and every generated HTML page automatically includes the chat widget's CSS and JS — without any manual configuration of extra files.

**Why this priority**: This is the primary visible outcome of the plugin. Without it, the widget cannot load on any page.

**Independent Test**: Run `mkdocs build` with the plugin enabled; verify `site/assets/chat.css` and `site/assets/chat.js` exist and each HTML page references them.

**Acceptance Scenarios**:

1. **Given** the plugin is enabled in `mkdocs.yml`, **When** `mkdocs build` completes, **Then** `site/assets/chat.css` and `site/assets/chat.js` exist
2. **Given** the plugin is enabled, **When** any HTML page is opened, **Then** it contains references to both asset files
3. **Given** the plugin is disabled (`enabled: false`), **When** `mkdocs build` completes, **Then** no chat assets are added and no chat config is injected

---

### User Story 2 - Chat configuration is available on every page (Priority: P2)

Every page in the built site carries the chat widget's configuration (model, title, position, llmstxt URL) so the frontend widget can initialise itself correctly without any additional requests.

**Why this priority**: The widget needs config at page-load time to know which Claude model to use, where to position itself, and where to find the documentation index.

**Independent Test**: Run `mkdocs build`; open any HTML file and confirm `window.__CLAUDE_CHAT_CONFIG__` is present with the expected keys.

**Acceptance Scenarios**:

1. **Given** the plugin is enabled, **When** a page is built, **Then** its HTML contains `window.__CLAUDE_CHAT_CONFIG__` with keys: `model`, `chat_title`, `position`, `llmstxt_url`, `system_prompt`
2. **Given** `llmstxt_url` is not set in config, **When** `on_config` runs, **Then** the URL is automatically derived from `site_url` as `<site_url>/llms.txt`
3. **Given** `llmstxt_url` is explicitly set, **When** `on_config` runs, **Then** the explicit value is used unchanged

---

### Edge Cases

- What if `site_url` is empty or not set — how is `llmstxt_url` derived?
- What if the plugin is disabled mid-build — are partial assets cleaned up?
- What happens if `on_page_context` is called before `on_config` completes?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plugin MUST register chat CSS and JS with MkDocs during initialisation
- **FR-002**: The plugin MUST copy bundled assets to the site directory after the build completes
- **FR-003**: The plugin MUST resolve `llmstxt_url` from config or auto-derive it from `site_url`
- **FR-004**: The plugin MUST inject chat configuration into every page's template context
- **FR-005**: All hooks MUST short-circuit immediately when `enabled` is `false`
- **FR-006**: All hook signatures MUST accept `**kwargs` for forward compatibility with future MkDocs versions

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every HTML page in the built site contains a reference to both chat asset files
- **SC-002**: Every HTML page contains the `window.__CLAUDE_CHAT_CONFIG__` object with all required keys
- **SC-003**: When `enabled: false`, zero chat-related content appears in the built site
- **SC-004**: The plugin works correctly across all MkDocs versions `>= 1.5`

## Assumptions

- `logger.py` and `assets.py` are already implemented and tested (features 001 and 002)
- MkDocs calls `on_config` before `on_page_context` and `on_post_build` — hooks run in the documented order
- If `site_url` is empty, `llmstxt_url` is set to an empty string (the widget handles missing URL gracefully)
- The template context dict from `on_page_context` is rendered into the page HTML by the MkDocs theme
