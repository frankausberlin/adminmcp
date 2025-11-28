This is a comprehensive project specification designed to be pasted directly into Kilocode or any other AI-driven development environment. It provides the necessary context, architectural decisions, and feature requirements to start coding immediately.

***

# Project Specification: AdminMCP

## 1. Project Overview
**AdminMCP** is a Model Context Protocol (MCP) server designed for Linux system administration. It bridges the gap between LLM-based coding environments (VS Code / Kilocode) and direct system interaction. It is implemented in Python using the official `mcp` SDK.

**Core Philosophy:** "Safe, Human-in-the-Loop Administration."
AdminMCP does not just execute commands blindly; it provides context, validates safety, and enforces user interaction for high-risk operations via a dedicated **Shellagent**.

## 2. Technical Architecture

The system consists of three main components:

1.  **MCP Client:** The IDE (VS Code/Kilocode).
2.  **AdminMCP Server (Python):** The core logic running as a subprocess of the IDE. It handles MCP requests (Resources, Prompts, Tools).
3.  **Shellagent (Python Wrapper):** A standalone process injected into the user's active shell (Bash/Zsh).
    * **Communication:** The Server communicates with the Shellagent via local IPC (Inter-Process Communication, e.g., Unix Domain Sockets or ZeroMQ).
    * **Function:** Wraps the standard shell to intercept commands, render TUI (Text User Interfaces) overlays, and capture STDOUT/STDERR.

## 3. Core Features (MCP Primitives)

### 3.1. Resources
Resources provide the LLM with the necessary context about the system state *before* it attempts to solve a problem.

| URI Scheme | Description | Security Note |
| :--- | :--- | :--- |
| `admin://system/hostinfo` | Kernel, OS release, Uptime, CPU/RAM stats. | Read-only |
| `admin://network/interfaces` | `ip a`, routing tables, DNS config. | Read-only |
| `admin://processes/top` | Snapshot of top resource-consuming processes. | Read-only |
| `admin://logs/{service}` | Fetches logs for specific services. | **Must apply PII masking.** |
| `admin://config/{path}` | Reads configuration files (e.g., `/etc/nginx/nginx.conf`). | Restricted to whitelisted paths. |

### 3.2. Prompts (Recipes)
Standardized administrative workflows that guide the LLM to generate specific execution plans.

* **Security:** `setup_firewall`, `harden_ssh`, `setup_dmz`.
* **Infrastructure:** `deploy_vpn` (WireGuard/OpenVPN), `manage_service` (systemd), `docker_compose_up`.
* **Maintenance:** `system_update`, `disk_cleanup` (log rotation, cache clearing).

### 3.3. Tools

#### A. The Shellagent (`execute_command`)
The primary execution engine. It supports three distinct operation modes to ensure safety:

* **Scenario 1: Autonomous (High Trust)**
    * Executes commands directly via the Shellagent.
    * *Restriction:* Only for low-risk commands (e.g., `ls`, `grep`) or explicitly authorized sessions.
* **Scenario 2: Simple Edit (Review)**
    * Injects the command into the user's shell `STDIN` (Readline buffer).
    * The command appears in the terminal, but requires the **user to press Enter**. The user can edit the command before execution.
* **Scenario 3: Tutor Edit (Educational)**
    * Intercepts execution and renders a TUI menu (using `rich` or `dialog`).
    * **Display:** Shows the command + a generated explanation of "Why" and "What".
    * **Actions:** `[E]xecute`, `[M]odify`, `[C]ancel`, `[?] Explain`.

#### B. Safety & Recovery Tools
Tools designed to prevent damage and assist in rollback.

* **`config_backup`**: Creates a timestamped copy of a file (e.g., `.bak`) before editing. Returns the backup path.
* **`syntax_check`**: Runs dry-run validation (e.g., `nginx -t`, `visudo -c`) before restarting services.
* **`smart_log_fetch`**: Fetches logs but utilizes regex to mask PII (IPs, passwords, emails) to protect privacy before sending data to the LLM.
* **`ask_user`**: Triggers an input request in the IDE if the LLM is missing parameters, preventing "hallucinated" values.

#### C. Management Tools
* **`cron_manager`**: Safely parses and edits Crontabs (validates syntax).
* **`package_inspector`**: Verifies package integrity (`rpm -V` / `debsums`).

## 4. Security Layer (Guardrails)

The implementation must strictly adhere to these security principles:

1.  **Sudo Handling:** The MCP Server **never** handles root passwords. If `sudo` is invoked, the Shellagent must rely on the interactive shell to prompt the user for the password standardly.
2.  **Command Blacklist:** Hardcoded forbidden commands (e.g., `rm -rf /`, formatting disks) that are rejected regardless of context.
3.  **Read-Only Flag:** Support for a server startup flag `--read-only` which disables all Tools except non-destructive information gathering.

## 5. Implementation Roadmap for Agent

**Phase 1: Skeleton & Basic IPC**
* Setup Python project with `mcp` SDK.
* Implement `AdminMCPServer` class.
* Create the `Shellagent` wrapper prototype using standard library `pty` or `pexpect`.
* Establish IPC between Server and Shellagent.

**Phase 2: Resources & Simple Edit**
* Implement system info resources (`psutil` recommended).
* Implement `execute_command` with **Scenario 2 (Simple Edit)** mechanism (injecting into STDIN).

**Phase 3: Safety Tools & Prompts**
* Implement `config_backup` and `smart_log_fetch` (with PII regex).
* Add basic Prompts (`system_update`).

**Phase 4: Advanced Interaction**
* Implement **Scenario 3 (Tutor Mode)** TUI.

---

**Directive for Kilocode/Agent:**
Start by setting up the project structure for **Phase 1**. Create the `server.py` and a basic `shell_agent.py`. Ensure type hinting is used throughout.

Please work according to agile software development principles and use unit tests. Refer to the `PROJECT_PROGRESS.md` for sprint updates and status tracking.