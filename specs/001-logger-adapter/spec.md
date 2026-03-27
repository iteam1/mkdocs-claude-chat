# Feature Specification: Logger Adapter

**Feature Branch**: `001-logger-adapter`
**Created**: 2026-03-27
**Status**: Draft
**Input**: User description: "implement logger.py — a logging adapter that prefixes messages with the plugin name and writes to the mkdocs.plugins namespace"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Plugin emits identifiable log messages (Priority: P1)

A developer running `mkdocs serve` or `mkdocs build` sees log messages from this plugin clearly prefixed with `claude-chat:`, distinguishable from other plugin output in the terminal.

**Why this priority**: Foundational to all other modules — without identifiable log output, debugging the plugin is impossible.

**Independent Test**: Enable the plugin, run `mkdocs build`, and observe that all plugin log lines are prefixed with `claude-chat:`.

**Acceptance Scenarios**:

1. **Given** the plugin is enabled, **When** `mkdocs build` runs, **Then** log output includes lines prefixed with `claude-chat:`
2. **Given** a module calls `get_logger(__name__)`, **When** it logs at any level, **Then** the message appears under the `mkdocs.plugins.claude-chat.*` namespace
3. **Given** MkDocs verbosity is set to quiet, **When** the plugin logs a debug message, **Then** it is suppressed (respects standard MkDocs log level behaviour)

---

### Edge Cases

- What happens when `name` passed to `get_logger` is an empty string?
- How does the logger behave if called before MkDocs initialises its logging system?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The logger MUST prefix every emitted message with `claude-chat:`
- **FR-002**: Log records MUST be written to the `mkdocs.plugins.claude-chat.<module>` namespace
- **FR-003**: `get_logger(name)` MUST accept a module `__name__` string and return a usable logger
- **FR-004**: The adapter MUST support all standard log levels: debug, info, warning, error, critical
- **FR-005**: The adapter MUST NOT suppress or alter MkDocs' existing log level configuration

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Every log line produced by any `_internal` module includes the `claude-chat:` prefix
- **SC-002**: Log messages are filterable by namespace using standard logging tools
- **SC-003**: No unhandled exceptions are raised by the logger under any log level or input

## Assumptions

- MkDocs' logging system is already initialised before the plugin runs
- All `_internal` modules call `get_logger(__name__)` at module level
- No custom log handlers are required — MkDocs' default handler is sufficient
