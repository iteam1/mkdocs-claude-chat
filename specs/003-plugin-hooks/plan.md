# Implementation Plan: Plugin Hooks

**Branch**: `003-plugin-hooks` | **Date**: 2026-03-27 | **Spec**: [spec.md](spec.md)

## Summary

Implement the three MkDocs lifecycle hooks in `src/mkdocs_claude_chat/_internal/plugin.py`:
- `on_config` — register assets + resolve `llmstxt_url`
- `on_post_build` — copy bundled assets to `site_dir`
- `on_page_context` — inject `window.__CLAUDE_CHAT_CONFIG__` into every page's template context

Depends on `logger.py` (001) and `assets.py` (002) which are already implemented.

## Technical Context

**Language/Version**: Python 3.10+
**Primary Dependencies**: `mkdocs>=1.5`, `logger.py` (001), `assets.py` (002) — no new packages
**Storage**: N/A (reads config, writes to template context)
**Testing**: pytest with real `MkDocsConfig` objects (constitution §IX — no mocks for MkDocs internals)
**Target Platform**: Any (library module, runs inside MkDocs process)
**Project Type**: MkDocs plugin (library)
**Performance Goals**: N/A — hooks run once per build
**Constraints**: All hook signatures must accept `**kwargs`; state populated in `on_config` only

## Constitution Check

| Rule (Constitution §) | Status | Notes |
|---|---|---|
| §II — `_internal/` only | ✅ | `plugin.py` lives in `_internal/` |
| §IV — Plugin class rules | ✅ | `BasePlugin[_PluginConfig]`, `**kwargs`, state in `on_config` |
| §IV — `enabled` short-circuit | ✅ | Every hook checks `self.config.enabled` first |
| §IV — Asset injection pattern | ✅ | Uses `assets.register()` + `assets.copy_to_site()` |
| §VII — `from __future__ import annotations` | ✅ | Required |
| §VII — TYPE_CHECKING guard for MkDocs imports | ✅ | `MkDocsConfig`, `Page` imported under `TYPE_CHECKING` |
| §VIII — Logger via `get_logger(__name__)` | ✅ | Module-level `_logger` |
| §IX — Real `MkDocsConfig` in tests | ✅ | No mocks for MkDocs internals |
| §X — Google docstring convention | ✅ | Applied |

No violations.

## Project Structure

### Documentation (this feature)

```text
specs/003-plugin-hooks/
├── plan.md       ← this file
├── research.md
└── tasks.md      ← /speckit.tasks
```

### Source Code

```text
src/mkdocs_claude_chat/_internal/
└── plugin.py         ← implement hooks (currently stub)

tests/
└── test_plugin.py    ← unit tests (currently stub)
```

---

## Phase 0: Research

No unknowns. All patterns are specified in the constitution (§IV, §VII, §VIII, §IX). MkDocs hook API is well-documented and version-stable for `>=1.5`.

See [research.md](research.md).

---

## Phase 1: Design

### Hook signatures (constitution §IV)

```python
def on_config(self, config: MkDocsConfig, **kwargs: object) -> MkDocsConfig | None
def on_post_build(self, *, config: MkDocsConfig, **kwargs: object) -> None
def on_page_context(self, context: dict, /, *, page: Page, config: MkDocsConfig, **kwargs: object) -> dict | None
```

### `on_config` logic

```
1. if not self.config.enabled → return None
2. resolve llmstxt_url:
   - if self.config.llmstxt_url → self._llmstxt_url = self.config.llmstxt_url.rstrip("/")
   - else → site_url = (config.get("site_url") or "").rstrip("/")
             self._llmstxt_url = f"{site_url}/llms.txt" if site_url else ""
3. assets.register(config["extra_css"], config["extra_javascript"])
4. _logger.debug(...)
5. return config
```

### `on_post_build` logic

```
1. if not self.config.enabled → return
2. assets.copy_to_site(config["site_dir"])
3. _logger.debug(...)
```

### `on_page_context` logic

```
1. if not self.config.enabled → return None
2. context["claude_chat_config"] = {
     "model": self.config.model,
     "chat_title": self.config.chat_title,
     "position": self.config.position,
     "llmstxt_url": self._llmstxt_url,
     "system_prompt": self.config.system_prompt or "",
   }
3. return context
```

### Class-level state

```python
class MkdocsClaudeChatPlugin(BasePlugin[_PluginConfig]):
    _llmstxt_url: str  # set in on_config
```

### Test plan (constitution §IX — real MkDocsConfig, no mocks)

| Test | What it checks |
|---|---|
| `test_on_config_registers_assets` | `extra_css`/`extra_javascript` contain chat paths after `on_config` |
| `test_on_config_derives_llmstxt_url` | URL derived as `<site_url>/llms.txt` when not set |
| `test_on_config_uses_explicit_llmstxt_url` | Explicit config value used unchanged |
| `test_on_config_disabled` | Returns `None`, no assets registered when `enabled: false` |
| `test_on_post_build_copies_assets` | Asset files appear in `site_dir/assets/` |
| `test_on_post_build_disabled` | No files copied when `enabled: false` |
| `test_on_page_context_injects_config` | `context["claude_chat_config"]` has all required keys |
| `test_on_page_context_disabled` | Returns `None` when `enabled: false` |
