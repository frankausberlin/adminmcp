# ACP (Admin Context Protocol) Design Document

## 1. Project Structure

The project will follow a standard Python `src` layout to ensure packaging compatibility and clean separation of concerns.

```
adminmcp/
├── pyproject.toml          # Project metadata and dependencies
├── README.md
├── PROJECT.md
├── src/
│   └── acp/
│       ├── __init__.py
│       ├── main.py         # Entry point for the 'ai' command
│       ├── config.py       # Configuration (paths, defaults)
│       ├── common/         # Shared code between Client and Server
│       │   ├── __init__.py
│       │   ├── models.py   # Pydantic models (LogEntry, ToolCall, etc.)
│       │   └── utils.py    # Shared utilities
│       ├── client/         # Client-side logic ('ai' CLI)
│       │   ├── __init__.py
│       │   ├── cli.py      # Argument parsing and dispatch
│       │   ├── state.py    # Mode management (read/write state file)
│       │   ├── executor.py # Command execution and local logging (from prototype)
│       │   └── api.py      # HTTP Client for communicating with Server
│       └── server/         # Server-side logic ('ai mode serve')
│           ├── __init__.py
│           ├── app.py      # FastAPI application setup
│           ├── routes.py   # API Endpoints
│           ├── core.py     # Core logic (Policy, Context)
│           ├── tools.py    # Tool definitions (shell/execute)
│           └── prompts.py  # Prompt repository management
└── tests/                  # Unit and integration tests
```

## 2. Dependencies

The project will require the following key dependencies, defined in `pyproject.toml`:

*   **Core:** `python >= 3.11`
*   **Server:**
    *   `fastapi`: For building the REST API.
    *   `uvicorn`: ASGI server for running the FastAPI app.
*   **Client:**
    *   `requests`: For synchronous HTTP requests to the server.
*   **Data/Validation:**
    *   `pydantic`: For robust data validation and schema definition (MCP relies heavily on JSON schemas).
*   **MCP:**
    *   `mcp`: The official Python SDK for Model Context Protocol (to ensure type compatibility and future extensibility).

## 3. Class Hierarchy & Component Design

### 3.1. Common (`src/acp/common/`)

*   **`models.py`**: Defines Pydantic models for data exchange.
    *   `LogEntry`: Schema for command execution logs.
    *   `ToolCall`: Schema for tool execution requests.
    *   `PromptRequest`: Schema for prompt analysis requests.
    *   `ServerResponse`: Standard response wrapper.

### 3.2. Client (`src/acp/client/`)

*   **`StateManager`**:
    *   Methods: `get_mode()`, `set_mode(mode)`, `get_state_path()`.
    *   Responsibility: Persist current mode (`logonly`, `watch`, `dialog`) to `$XDG_RUNTIME_DIR/ai_state.json`.

*   **`CommandExecutor`**:
    *   Methods: `run_command(cmd, timeout)`, `log_execution(data)`.
    *   Responsibility: Wraps `subprocess.run`, captures stdout/stderr, handles local JSON logging (refactored from original `acp` script).

*   **`APIClient`**:
    *   Methods: `send_log(entry)`, `analyze_prompt(text)`, `call_tool(tool_call)`.
    *   Responsibility: Handles HTTP `POST` requests to `localhost:8765`.

*   **`CLI`**:
    *   Methods: `main()`, `parse_args()`, `handle_mode_switch()`, `handle_execution()`.
    *   Responsibility: Entry point. Decides whether to run a command locally, send a prompt to server, or switch modes.

### 3.3. Server (`src/acp/server/`)

*   **`ToolManager`**:
    *   Methods: `register_tool(tool)`, `get_tool(name)`, `execute_tool(name, args)`.
    *   Responsibility: Manages available tools. Implements `shell/execute`.

*   **`PromptRegistry`**:
    *   Methods: `load_prompts(path)`, `find_match(text)`.
    *   Responsibility: Loads prompt templates (recipes) and matches user input to prompts.

*   **`PolicyEngine`**:
    *   Methods: `check_policy(command, context)`.
    *   Responsibility: In `watch` mode, validates commands against safety rules (or LLM) before execution.

*   **`ServerApp` (FastAPI)**:
    *   Endpoints:
        *   `POST /api/v1/roots/update`
        *   `POST /api/v1/log/submit`
        *   `POST /api/v1/prompt/analyze`
        *   `POST /api/v1/tools/call`

## 4. Implementation Plan

1.  **Setup**: Initialize `pyproject.toml` and directory structure.
2.  **Common**: Define Pydantic models to ensure Client/Server speak the same language.
3.  **Server Core**: Implement the FastAPI app with stubbed endpoints.
4.  **Client Core**: Refactor existing `acp` logic into `CommandExecutor` and `CLI`. Implement `StateManager`.
5.  **Integration**: Connect Client `logonly` mode to Server `/log/submit`.
6.  **Features**: Implement `shell/execute` tool on Server and `watch` mode logic.

## 5. Key Decisions

*   **FastAPI vs Flask**: Chosen **FastAPI** for native Pydantic integration (crucial for MCP schemas) and async capabilities (better for handling concurrent LLM requests in future).
*   **State Management**: Using a simple JSON file in `XDG_RUNTIME_DIR` ensures the CLI state persists across shell sessions but is cleaned up on reboot.
*   **Logging**: Local logging is preserved for reliability; server logging is asynchronous/secondary to ensure the CLI remains snappy.