# Research: Assets Injection

**Branch**: `002-assets-injection` | **Date**: 2026-03-27

## Findings

No unknowns. All decisions are determined by the constitution and stdlib capabilities.

| Decision | Choice | Rationale |
|---|---|---|
| File copy | `shutil.copy2` | Preserves metadata; stdlib; idiomatic for this use case |
| Path resolution | `Path(__file__).parent.parent / "assets"` | Resolves bundled assets relative to the installed package — works regardless of install location |
| Directory creation | `Path.mkdir(parents=True, exist_ok=True)` | Safe, idempotent; no need to check existence first |
| Registration paths | `"assets/chat.css"` / `"assets/chat.js"` | Relative paths as expected by MkDocs `extra_css`/`extra_javascript` |

## Alternatives Considered

- **`importlib.resources`** for asset path resolution — more correct for zip-safe packages, but adds complexity; `__file__`-based resolution is sufficient for this plugin's distribution model (wheel with data files)
