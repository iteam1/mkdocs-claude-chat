# Feature Specification: Assets Injection

**Feature Branch**: `002-assets-injection`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "implement assets.py"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - CSS and JS are available on every built page (Priority: P1)

A documentation site visitor loads any page and the chat widget's stylesheet and script are present, enabling the widget to initialise correctly.

**Why this priority**: Without the assets reaching the built site, nothing else in the plugin works. This is the most foundational user-facing outcome.

**Independent Test**: Run `mkdocs build`, then verify `site/assets/chat.css` and `site/assets/chat.js` both exist and are non-empty.

**Acceptance Scenarios**:

1. **Given** the plugin is enabled, **When** `mkdocs build` completes, **Then** `site/assets/chat.css` and `site/assets/chat.js` exist in the output directory
2. **Given** the plugin is enabled, **When** any page is loaded in a browser, **Then** the browser fetches `chat.css` and `chat.js` without 404 errors
3. **Given** the plugin is disabled (`enabled: false`), **When** `mkdocs build` completes, **Then** no chat assets are added to the site

---

### User Story 2 - Assets are registered with MkDocs at config time (Priority: P2)

When the plugin initialises, MkDocs is informed about the CSS and JS files so they are linked in every page's `<head>` automatically.

**Why this priority**: MkDocs must know about the assets at config time to inject the correct `<link>` and `<script>` tags — this enables the browser to load them.

**Independent Test**: After `on_config` runs, inspect `config["extra_css"]` and `config["extra_javascript"]` and confirm the chat asset paths are present.

**Acceptance Scenarios**:

1. **Given** the plugin is enabled, **When** `on_config` runs, **Then** `assets/chat.css` is appended to `extra_css`
2. **Given** the plugin is enabled, **When** `on_config` runs, **Then** `assets/chat.js` is appended to `extra_javascript`
3. **Given** assets are already registered (duplicate call), **When** `on_config` runs again, **Then** no duplicate entries appear

---

### Edge Cases

- What if `site_dir` does not exist when `copy_to_site` is called?
- What if the bundled asset files are missing from the installed package?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The plugin MUST append the chat stylesheet path to the MkDocs CSS list during initialisation
- **FR-002**: The plugin MUST append the chat script path to the MkDocs JavaScript list during initialisation
- **FR-003**: The plugin MUST copy the bundled `chat.css` and `chat.js` into the built site's assets directory after the build completes
- **FR-004**: The plugin MUST create the destination assets directory if it does not already exist
- **FR-005**: When the plugin is disabled, it MUST NOT register or copy any assets

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: After every successful build, `site/assets/chat.css` and `site/assets/chat.js` are present and non-empty
- **SC-002**: Every generated HTML page includes a reference to both asset files
- **SC-003**: No assets are added when the plugin is disabled

## Assumptions

- Bundled `chat.css` and `chat.js` files already exist in the package's `assets/` directory
- MkDocs resolves `extra_css` and `extra_javascript` paths relative to `docs_dir` at build time
- The `site_dir` is always provided by MkDocs before `on_post_build` is called
