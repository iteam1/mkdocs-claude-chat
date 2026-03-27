# Implementation Plan: Assets Injection

**Branch**: `002-assets-injection` | **Date**: 2026-03-27 | **Spec**: [spec.md](spec.md)

## Summary

Implement `src/mkdocs_claude_chat/_internal/assets.py` — two functions:
- `register(extra_css, extra_javascript)` — appends the plugin's CSS/JS paths to MkDocs config lists at `on_config` time
- `copy_to_site(site_dir)` — copies the bundled `chat.css` and `chat.js` from the package's `assets/` directory into `site/assets/` after the build completes

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `shutil`, `pathlib` (stdlib only) — no new packages
**Storage**: Filesystem — reads from package `assets/`, writes to `site_dir/assets/`
**Testing**: pytest
**Target Platform**: Any (library module, runs inside MkDocs process)
**Project Type**: MkDocs plugin (library)
**Performance Goals**: N/A — file copy is not a bottleneck
**Constraints**: Zero external dependencies; `site_dir/assets/` may not exist — must be created

## Constitution Check

| Rule (Constitution §) | Status | Notes |
|---|---|---|
| §II — `_internal/` only | ✅ | File lives in `_internal/assets.py` |
| §II — `assets/` bundled separately | ✅ | Source files are in `src/mkdocs_claude_chat/assets/` |
| §VII — `from __future__ import annotations` | ✅ | Required |
| §VII — Full type annotations | ✅ | Both functions fully annotated |
| §IV — Asset injection via `extra_css`/`extra_javascript` | ✅ | Exact pattern from constitution |
| §X — Google docstring convention | ✅ | Applied |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-assets-injection/
├── plan.md       ← this file
├── research.md
└── tasks.md      ← /speckit.tasks
```

### Source Code

```text
src/mkdocs_claude_chat/
├── assets/
│   ├── chat.css          ← source (already exists)
│   └── chat.js           ← source (already exists)
└── _internal/
    └── assets.py         ← new implementation

tests/
└── test_assets.py        ← new unit tests
```

---

## Phase 0: Research

No unknowns. Both functions use stdlib only (`shutil.copy2`, `pathlib.Path`). MkDocs asset injection pattern is specified in the constitution (§IV).

See [research.md](research.md).

---

## Phase 1: Design

### Interface

```
register(extra_css: list, extra_javascript: list) -> None
  Appends "assets/chat.css" to extra_css
  Appends "assets/chat.js" to extra_javascript
  Mutates the lists in place — no return value

copy_to_site(site_dir: str) -> None
  dest = Path(site_dir) / "assets"
  dest.mkdir(parents=True, exist_ok=True)
  copies ASSETS_DIR/chat.css  → dest/chat.css
  copies ASSETS_DIR/chat.js   → dest/chat.js

ASSETS_DIR = Path(__file__).parent.parent / "assets"
```

### Test plan

| Test | What it checks |
|---|---|
| `test_register_appends_css` | `extra_css` contains `"assets/chat.css"` after call |
| `test_register_appends_js` | `extra_javascript` contains `"assets/chat.js"` after call |
| `test_register_no_duplicates` | Calling twice does not add duplicates |
| `test_copy_to_site_creates_files` | Both files exist in `tmp_path/site/assets/` after call |
| `test_copy_to_site_creates_dir` | `site/assets/` is created if it doesn't exist |
| `test_copy_to_site_content` | Copied files are non-empty |
