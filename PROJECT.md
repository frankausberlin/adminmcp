# 📝 Project Specification: Admin Context Protocol (ACP) CLI v0.1

This is a comprehensive project specification that can be directly inserted into Kilocode or any other AI-powered development environment. It provides the necessary context, architectural decisions, and functional requirements to begin programming immediately. This document is continuously updated.

---

## 1. 🎯 Project Overview and Goal (Revised)

The **Admin Context Protocol (ACP) CLI** is a highly controlled, context-aware command-line wrapper built around the Model Context Protocol (**MCP**) standards.

**Crucially, ACP is a domain-agnostic orchestration layer.** It does not inherently represent a "Linux Admin" or "Database Admin." Instead, its functional domain and persona are **entirely defined by its collection of Prompts (recipes)** and the **Tools** it exposes.

The system's goal is to introduce controlled, accountable, and agentic AI supervision into standard administrative shell environments, allowing the same core framework to serve different specialized roles (e.g., managing Ubuntu services, maintaining Windows systems, interacting with AWS/Azure, or querying specific database systems) simply by switching the **Prompt/Tool/Resource** set.

The system consists of a Python-based CLI (`ai`) acting as the **MCP Client** and a corresponding Python service acting as the **MCP Server**.

### Key Deliverables

1.  **`ai` Client:** The command wrapper for execution, logging, mode switching, and initiating LLM Prompts (`ai - ...`).
2.  **`ai mode serve` Server:** A persistent HTTP/WebSocket API that hosts the LLM logic, manages **Tools**, **Resources**, and enforces the security policy (**Watch Mode**).

---

## 2. 🏛️ Architectural Decisions

### A. Communication

* **Protocol:** Minimalistic **RESTful API** (HTTP POST/GET) for initial state and command execution, evolving potentially to WebSockets for real-time Elicitation/Sampling requests.
* **Location:** The server runs locally (`localhost`) and listens on a configurable port (default: `8765`).
* **Data Format:** All communication (Tools, Resources, Elicitation requests/responses) uses **JSON**, adhering to the MCP structure.

### B. Language and Environment

* **Language:** Python 3.11+
* **Core Libraries:**
    * **Client (`ai`):** `subprocess`, `argparse`, `os`, `json`, **`requests`** (for communicating with the Server).
    * **Server (`ai mode serve`):** **`Flask`** or **`FastAPI`** (for API endpoint management), `os`, `json`, (Future: LLM SDK integration).

---

## 3. ⚙️ Functional Requirements (Client: `ai`)

The Client handles user input, logs execution, manages session state (**Mode**), and communicates with the Server.

### A. Execution Modes and State Management

The current operating mode must be persisted in a temporary file (e.g., `$XDG_RUNTIME_DIR/ai_state.json`) and is set via `ai mode [mode]`.

| Command | Mode | Behavior | MCP Implication |
| :--- | :--- | :--- | :--- |
| `ai mode logonly` | `logonly` (Default) | Executes command, logs all details (using existing Python implementation), sends log entry to Server as a **Resource**. No Server intervention required for execution. | **Passive Context Collection** |
| `ai mode watch` | `watch` | **Intercepts** command execution, sends command data to Server for approval/denial, awaits Server response before calling `subprocess.run`. | **Tool Execution Control** |
| `ai mode dialog` | `dialog` | Primarily used for Prompt execution (`ai - ...`). Displays the full User Interaction Model (UIM) including **Elicitation** menus. | **Structured Interaction** |
| `ai mode serve` | N/A | Starts the persistent ACP Server process. | **Server Initiation** |

### B. Core Functions

#### 1. Command Execution and Logging (Existing Prototype)

* **Requirement:** The existing `log_shell_command` logic must be retained for reliable logging of structured metadata.
* **Enhancement:** After local logging, the Client must send the complete JSON log entry to the Server via a POST request (`/api/v1/log/submit`) to update the Server's context.

#### 2. Prompt Execution Interface

* **Syntax:** If input starts with `ai -`, the entire following text is treated as a **natural language prompt**.
* **Flow:**
    1.  Client sends raw prompt text to Server (`POST /api/v1/prompt/analyze`).
    2.  Client awaits a structured response containing the best-matched **Prompt ID** and required parameters.
    3.  If in `dialog` mode, the Client renders the user interaction menu: `(p)arameter anpassen`, `(e)dit Prompt`, `(c)ancel`, `(y)es/ausführen`.
    4.  If approved (`y`), the Client sends the final, parameterized **Tool Call** request to the Server.

---

## 4. ⚙️ Functional Requirements (Server: `ai mode serve`)

The Server is the LLM orchestrator and policy enforcer.

### A. API Endpoints (Minimal Required)

| Method | Endpoint | Purpose | MCP Concept |
| :--- | :--- | :--- | :--- |
| `POST` | `/api/v1/roots/update` | Client informs the Server of its current working directory (**Roots**). | **Roots** |
| `POST` | `/api/v1/log/submit` | Client sends a newly created JSON log entry for context analysis. | **Resource Update** |
| `POST` | `/api/v1/prompt/analyze` | Receives raw user text, identifies the best matching **Prompt**, and returns required **Elicitation** schema. | **Prompts / Elicitation** |
| `POST` | `/api/v1/tools/call` | Primary endpoint for executing actions (`shell/execute` or other Tools) in `watch` or `dialog` mode. | **Tools** |

### B. Core Server Components

#### 1. Tools Manager

* **Goal:** Define and manage the available functions for the LLM.
* **Initial Tool Schema:** The Server must expose the following core Tool via a `/api/v1/tools/list` endpoint:

    ```json
    {
      "name": "shell/execute",
      "description": "Executes a command on the host machine. Use sparingly and with justification.",
      "inputSchema": {
        "type": "object",
        "properties": {
          "command": {"type": "string", "description": "The command line string to execute."},
          "timeout": {"type": "integer", "default": 7200, "description": "Execution timeout in seconds."}
        },
        "required": ["command"]
      }
    }
    ```

#### 2. Prompts Repository (Admin Recipes) (Revised)

* **Goal:** Store the structured templates for common administrative tasks. **This collection of Prompts (recipes) directly determines the ACP's functional domain** (e.g., Linux, Database, Cloud CLI, etc.).
* **Modularity:** The Server architecture must allow loading different Prompt repositories to instantly change the ACP's specialization.
* **Example Prompt Schema (`clean_logs`):**

    ```json
    {
      "id": "/clean_logs",
      "title": "Clean Logs by Service and Age",
      "description": "Safely removes old log files for a specific service.",
      "arguments": [
        {"name": "service_name", "type": "string", "required": true, "description": "The service whose logs should be cleaned (e.g., 'nginx', 'mariadb')."},
        {"name": "age_days", "type": "integer", "required": true, "description": "Minimum age of logs to delete, in days."}
      ],
      "tool_sequence": [
         // Placeholder for the LLM instruction on how to use shell/execute and filesystem/read
      ]
    }
    ```

#### 3. Watch Mode Policy Engine

* When a `POST /api/v1/tools/call` request arrives from a `watch`-mode client, the server must execute the following logic **before** calling the `shell/execute` tool:
    1.  **Retrieve Context:** Load relevant **Resources** (latest log entries, current **Roots**).
    2.  **Policy Check (LLM):** Feed the proposed command and the context to the LLM with a System Prompt: "Is this command a high-risk operation or a violation of internal policy? Respond with EXECUTE, DENY, or ELICIT."
    3.  **Action Hooks:** If DENY or EXECUTE, trigger the external scripts (e.g., `on_guideline_violation.sh`) as defined by the user's local configuration.

---

## 5. 🏗️ Implementation Roadmap (Phases)

| Phase | Component | Focus | Status |
| :--- | :--- | :--- | :--- |
| **P0** | **Client (Existing)** | Logging, Execution, `--log` view. | **Complete** (Prototype exists) |
| **P1** | **Client & Server API** | Implement `ai mode serve` (Flask/FastAPI). Implement basic Client-Server communication (`/roots/update`, `/log/submit`). Implement Mode switching persistence. | **Start Here** |
| **P2** | **Watch Mode Tooling** | Implement the `/tools/call` endpoint. Integrate basic LLM dummy logic for EXECUTE/DENY (e.g., based on a simple regex check). | **Core Logic** |
| **P3** | **Prompt Engine** | Implement `/prompt/analyze`. Build the `dialog` mode menu (`P, E, C, Y`) for the Client. Implement Elicitation rendering on the Client side. | **User Experience** |