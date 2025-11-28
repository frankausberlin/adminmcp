# AdminMCP Architecture & Implementation Plan

This document outlines the technical architecture and implementation plan for the AdminMCP project, focusing on Phase 1 (Core Infrastructure).

## 1. Project Structure

The project will follow a standard Python package structure using `poetry` or `pip` for dependency management.

```text
adminmcp/
├── pyproject.toml          # Project dependencies and configuration
├── README.md               # Project documentation
├── ARCHITECTURE.md         # This file
├── PROJECT.md              # Original project specification
├── PROJECT_PROGRESS.md     # Sprint tracking
├── src/
│   └── adminmcp/
│       ├── __init__.py
│       ├── main.py         # Entry point for CLI
│       ├── server.py       # MCP Server implementation (mcp SDK)
│       ├── agent.py        # ShellAgent implementation (pty wrapper)
│       ├── ipc.py          # IPC communication layer (UDS)
│       ├── config.py       # Configuration loading
│       └── utils/
│           ├── __init__.py
│           └── logging.py  # Centralized logging
└── tests/
    ├── __init__.py
    ├── conftest.py         # Pytest fixtures
    ├── test_server.py      # Tests for MCP Server logic
    ├── test_agent.py       # Tests for ShellAgent pty handling
    └── test_ipc.py         # Tests for IPC communication
```

## 2. Class Architecture

### 2.1. `AdminMCPServer` (`src/adminmcp/server.py`)
This class implements the Model Context Protocol server. It handles requests from the client (IDE) and delegates execution to the ShellAgent.

*   **Responsibilities:**
    *   Initialize the MCP server instance.
    *   Register Resources, Prompts, and Tools.
    *   Manage the IPC client connection to the ShellAgent.
    *   Handle tool execution requests (e.g., `execute_command`) by sending JSON messages over IPC.

*   **Key Methods:**
    *   `__init__(ipc_path: str)`: Initializes server and IPC client.
    *   `run()`: Starts the MCP server loop (stdio or SSE).
    *   `_handle_tool_call(name: str, arguments: dict)`: Internal handler to route tool calls.
    *   `_connect_agent()`: Establishes connection to the ShellAgent socket.

### 2.2. `ShellAgent` (`src/adminmcp/agent.py`)
This class runs as a standalone process (or subprocess) that wraps the actual system shell (Bash/Zsh) using Python's `pty` library.

*   **Responsibilities:**
    *   Spawn the underlying shell process in a pseudo-terminal (PTY).
    *   Host the IPC server (Unix Domain Socket) to listen for commands from `AdminMCPServer`.
    *   Manage the shell's STDIN/STDOUT/STDERR.
    *   Implement the "Safety Modes" (Autonomous, Simple Edit, Tutor).

*   **Key Methods:**
    *   `__init__(socket_path: str, shell_cmd: list)`: Configures socket and shell command.
    *   `start()`: Forks the PTY and starts the IPC listener loop.
    *   `write_to_shell(command: str)`: Writes command to the shell's master FD.
    *   `read_output(timeout: float)`: Reads from the shell's master FD.
    *   `handle_ipc_request(request: dict)`: Processes incoming JSON commands.

### 2.3. `IPCClient` & `IPCServer` (`src/adminmcp/ipc.py`)
Abstraction layer for Unix Domain Socket communication.

*   **Protocol:** JSON-based messages.
*   **Message Format:**
    ```json
    {
      "id": "uuid",
      "type": "command_execution",
      "payload": {
        "command": "ls -la",
        "mode": "autonomous"
      }
    }
    ```

## 3. IPC Mechanism

We will use **Unix Domain Sockets (UDS)** for low-latency, secure local communication between the Server and the Agent.

*   **Socket Path:** Defaults to `/tmp/adminmcp-{user}.sock` or `$XDG_RUNTIME_DIR/adminmcp.sock`.
*   **Flow:**
    1.  `ShellAgent` starts up, creates the UDS, and listens.
    2.  `AdminMCPServer` starts up and connects to the UDS.
    3.  When `AdminMCPServer` receives a tool call, it serializes the request and sends it to the UDS.
    4.  `ShellAgent` receives the message, interacts with the PTY, and sends back the result (stdout/stderr/exit_code).

## 4. Phase 1 Sprint Plan (Core Infrastructure)

**Goal:** Establish the skeleton, get the ShellAgent running with PTY, and enable basic command execution via MCP.

### Sprint 1.1: Project Skeleton & IPC Layer
*   **Task 1.1.1:** Initialize project structure (pyproject.toml, directories).
*   **Task 1.1.2:** Implement `IPCServer` and `IPCClient` classes in `src/adminmcp/ipc.py`.
*   **Task 1.1.3:** Write unit tests for IPC communication (`tests/test_ipc.py`).

### Sprint 1.2: ShellAgent Prototype
*   **Task 1.2.1:** Implement `ShellAgent` class using `pty.fork()` or `subprocess` with `pty`.
*   **Task 1.2.2:** Implement basic `write_to_shell` and `read_output` methods.
*   **Task 1.2.3:** Integrate `IPCServer` into `ShellAgent` to accept commands.
*   **Task 1.2.4:** Create a standalone script to run the agent for testing.

### Sprint 1.3: AdminMCP Server Basic Implementation
*   **Task 1.3.1:** Implement `AdminMCPServer` class using `mcp` SDK.
*   **Task 1.3.2:** Create the `execute_command` tool definition.
*   **Task 1.3.3:** Connect `AdminMCPServer` to `ShellAgent` via `IPCClient`.
*   **Task 1.3.4:** Implement `main.py` to launch both components (or launch Agent as subprocess).

### Sprint 1.4: Integration & Verification
*   **Task 1.4.1:** Create an end-to-end test: MCP Client -> Server -> IPC -> Agent -> Shell -> Result.
*   **Task 1.4.2:** Verify "Autonomous" mode for simple commands (e.g., `echo "hello"`).

## 5. Phase 2 Architecture (Basic Tools & Security)

### 5.1. Security Layer (`src/adminmcp/core/security.py`)
Centralized security validation for command execution.

*   **Class:** `SecurityValidator`
*   **Responsibilities:**
    *   Validate shell commands against safety rules.
    *   Maintain lists of allowed/blocked commands or patterns.
    *   Enforce operation modes (e.g., "restricted" vs "autonomous").
*   **Key Methods:**
    *   `validate_command(command: str) -> bool`: Returns True if command is safe.
    *   `check_permissions(tool_name: str) -> bool`: Checks if a tool is allowed.

### 5.2. System Tools (`src/adminmcp/tools/system.py`)
Native Python implementations for system inspection, avoiding shell parsing where possible.

*   **Tools:**
    *   `system_info`: Returns JSON with OS, Kernel, CPU, Memory stats.
    *   `list_processes`: Returns JSON list of active processes (PID, name, status).
*   **Dependencies:**
    *   `psutil` (recommended for robust process/system monitoring).

## 6. Phase 3 Architecture (Interactive Shell & TUI)

### 6.1. TUI Framework (`textual`)
We will use **Textual** to build the interactive terminal interface for the `ShellAgent`. This allows the agent to be visible to the user, displaying the shell output and providing a mechanism for manual intervention (Tutor Mode).

*   **Class:** `AgentTUI` (extends `textual.app.App`)
*   **Components:**
    *   `TerminalWidget`: Renders the VT100 output from the PTY.
    *   `StatusBar`: Shows current mode (Autonomous, Tutor, Restricted) and connection status.
    *   `ConfirmationModal`: A popup dialog for Tutor mode approvals.

### 6.2. Tutor Mode Workflow
In Tutor mode, the Agent acts as a gatekeeper.

1.  **Request:** `AdminMCPServer` sends an `execute_command` request with `mode="tutor"`.
2.  **Interception:** `ShellAgent` receives the request but does *not* immediately write to the PTY.
3.  **Prompt:** The `AgentTUI` displays a confirmation modal: "Allow execution of: `<command>`?".
4.  **User Action:**
    *   **Approve:** User presses 'y'/'Enter'. Agent writes command to PTY and returns output.
    *   **Deny:** User presses 'n'/'Esc'. Agent returns "Permission denied by user" error.
    *   **Edit:** (Optional for later) User edits the command before approving.

### 6.3. Architecture Updates
*   **`ShellAgent`:** Will now initialize and run the `AgentTUI` application. The IPC server will run as a background task within the Textual event loop or alongside it.