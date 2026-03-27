# Research: Plugin Hooks

**Branch**: `003-plugin-hooks` | **Date**: 2026-03-27

## Findings

No unknowns. All decisions are prescribed by the constitution and MkDocs API conventions.

| Decision | Choice | Rationale |
|---|---|---|
| Hook for asset registration | `on_config` | First hook called; `extra_css`/`extra_javascript` must be set before MkDocs processes pages |
| Hook for file copy | `on_post_build` | Called after all pages are built; `site_dir` is fully populated |
| Hook for page config injection | `on_page_context` | Called per-page with template context; cleanest injection point |
| State initialisation | `on_config` only | Constitution §IV: never in `__init__` |
| `llmstxt_url` fallback | `""` when `site_url` empty | Widget handles empty string gracefully; avoids raising during build |
| TYPE_CHECKING guard | Yes for `MkDocsConfig`, `Page` | Avoids circular imports at runtime; idiomatic Python pattern |

## Alternatives Considered

- **`on_env`** for asset registration — fires after `on_config` but before page rendering; rejected because `extra_css`/`extra_javascript` must be set in `on_config`
- **`on_page_content`** for config injection — operates on rendered HTML strings; would require string injection, fragile compared to template context
