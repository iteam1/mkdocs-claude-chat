# Architecture

This page describes how the internal modules of `mkdocs-ask-claude` collaborate.

## Module Collaboration

```mermaid
graph TD
    config["config.py\nDefines _PluginConfig\nmodel · position · llmstxt_url\nsystem_prompt · chat_title\nbackend_port · session_ttl · max_sessions"]
    plugin["plugin.py\nMkDocs plugin entry point\non_config · on_post_build · on_page_context\non_post_page · on_startup"]
    assets["assets.py\nInjects chat.js and chat.css\ninto the built site"]
    server["server.py\nFastAPI chat backend\nClaudeSDKClient session per browser tab\nreads llms.txt from disk\nstreams SSE answers"]
    logger["logger.py\nPlugin-namespaced\nlogging utilities"]

    config -->|imported by| plugin
    plugin -->|build time: register + copy CSS/JS| assets
    plugin -->|on_startup: start server thread| server
    plugin -->|on_post_build: configure site_dir| server
    server -->|reads from disk| llmstxt["site/llms.txt\nsite/llms-full.txt"]
    server -->|delegates to| Claude["ClaudeSDKClient\nallowed tools: Bash · WebFetch · WebSearch"]
    Claude -->|fetches doc pages| Web["HTTP (curl / WebFetch)"]

    logger -.->|used by| plugin
    logger -.->|used by| server
```

## Build-time Flow

When `mkdocs build` or `mkdocs serve` runs:

```mermaid
sequenceDiagram
    participant MkDocs
    participant plugin.py
    participant assets.py
    participant server.py

    MkDocs->>plugin.py: on_startup(command="serve")
    plugin.py->>server.py: server.run() [daemon thread]

    MkDocs->>plugin.py: on_config()
    plugin.py->>plugin.py: resolve _llmstxt_url
    plugin.py->>assets.py: register chat.css + chat.js in extra_css/extra_javascript

    MkDocs->>plugin.py: on_page_context() [per page]
    plugin.py->>plugin.py: add claude_chat_config to Jinja2 context

    MkDocs->>plugin.py: on_post_page() [per page]
    plugin.py->>MkDocs: inject window.__CLAUDE_CHAT_CONFIG__ before </body>

    MkDocs->>plugin.py: on_post_build()
    plugin.py->>assets.py: copy chat.css + chat.js to site/assets/
    plugin.py->>server.py: configure(site_dir, llmstxt_url, …)
```

## Chat Runtime Flow

When a visitor asks a question in the widget:

```mermaid
sequenceDiagram
    participant Browser
    participant server.py
    participant Worker
    participant Claude
    participant Filesystem

    Browser->>server.py: POST /chat {question, session_id}
    server.py->>Worker: get_or_create session worker task

    Note over Worker: On first message for session:
    Worker->>Filesystem: read site/llms.txt
    Worker->>Claude: ClaudeSDKClient(system_prompt with llms.txt embedded)

    server.py->>Worker: question_q.put((question, reply_q))
    Worker->>Claude: client.query(question)

    Claude->>Claude: scan embedded llms.txt index
    Claude->>Claude: identify relevant pages

    loop for each relevant page
        Claude-->>Worker: ToolUseBlock (Bash / WebFetch)
        Worker-->>Browser: SSE: tool_call event
        Claude->>Claude: execute tool (curl page URL)
        Claude-->>Worker: ToolResultBlock
        Worker-->>Browser: SSE: tool_result event
    end

    Claude-->>Worker: AssistantMessage (TextBlock chunks)
    Worker-->>Browser: SSE: text events
    Worker-->>Browser: SSE: [DONE]
```

## Module Dependencies

```plantuml
@startuml
skinparam componentStyle rectangle

component "plugin.py" as plugin
component "config.py" as config
component "assets.py" as assets
component "server.py" as server
component "logger.py" as logger

plugin --> config : reads _PluginConfig
plugin --> assets : register + copy at build time
plugin --> server : configure() after each build\nrun() on startup
logger <-- plugin : used by
logger <-- server : used by

note right of server
  FastAPI + uvicorn sidecar
  POST /chat → SSE stream
  ClaudeSDKClient per session
  reads docs from disk
end note
@enduml
```

## Implementation Status

| Module | Status | Notes |
|---|---|---|
| `config.py` | Done | Full config schema: enabled, model, system_prompt, llmstxt_url, chat_title, position, backend_port, session_ttl, max_sessions |
| `plugin.py` | Done | on_config, on_post_build, on_page_context, on_post_page, on_startup |
| `assets.py` | Done | CSS/JS registration + copy to site/assets/ |
| `server.py` | Done | FastAPI backend, ClaudeSDKClient sessions, SSE streaming, session TTL + eviction |
| `logger.py` | Done | Plugin-namespaced logging adapter (mkdocs.plugins.ask-claude.*) |
| `tools.py` | Stub | Reserved for custom Claude tool definitions |
