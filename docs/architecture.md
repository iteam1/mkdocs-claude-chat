# Architecture

This page describes how the internal modules of `mkdocs-claude-chat` collaborate.

## Module Collaboration

```mermaid
graph TD
    config["config.py\nDefines _PluginConfig\nmodel · position · llmstxt_url\nsystem_prompt · chat_title"]
    plugin["plugin.py\nMkDocs plugin entry point\non_config · on_post_build\non_page_context"]
    assets["assets.py\nInjects chat.js and chat.css\ninto the built site"]
    server["server.py\nChat backend\nClaudeSDKClient session\nstreams answers"]
    tools["tools.py\nClaude tools\nfetch_llmstxt()\nfetch_page()"]
    logger["logger.py\nPlugin-namespaced\nlogging utilities"]

    config -->|imported by| plugin
    plugin -->|build time: inject CSS/JS| assets
    plugin -->|runtime: delegate question| server
    server -->|Claude calls| tools
    tools -->|fetches docs from| llmstxt["/llms.txt\n(external)"]

    logger -.->|used by| plugin
    logger -.->|used by| server
    logger -.->|used by| tools
    logger -.->|used by| assets
```

## Build-time Flow

When `mkdocs build` runs:

```mermaid
sequenceDiagram
    participant MkDocs
    participant plugin.py
    participant config.py
    participant assets.py

    MkDocs->>plugin.py: on_config()
    plugin.py->>config.py: read _PluginConfig (model, position, …)
    plugin.py->>assets.py: inject chat.js + chat.css into site

    MkDocs->>plugin.py: on_page_context()
    plugin.py->>MkDocs: write window.__CLAUDE_CHAT_CONFIG__ into page

    MkDocs->>plugin.py: on_post_build()
    plugin.py->>assets.py: copy bundled assets to site/
```

## Chat Runtime Flow

When a visitor asks a question in the widget:

```mermaid
sequenceDiagram
    participant Browser
    participant server.py
    participant tools.py
    participant Claude

    Browser->>server.py: user question
    server.py->>Claude: start ClaudeSDKClient session
    Claude->>tools.py: fetch_llmstxt()
    tools.py-->>Claude: documentation index
    Claude->>tools.py: fetch_page(url)
    tools.py-->>Claude: page content
    Claude-->>server.py: answer
    server.py-->>Browser: streamed response
```

## Implementation Status

| Module | Status | Notes |
|---|---|---|
| `config.py` | Done | Full config schema |
| `plugin.py` | Partial | Class declared, hooks not implemented |
| `assets.py` | Stub | Empty |
| `server.py` | Stub | Empty |
| `tools.py` | Stub | Empty |
| `logger.py` | Stub | Empty |
