# ACP (Admin-MCP)

> An alpha-stage Admin Context Protocol implementation that pairs an MPC-friendly control plane with a guarded local shell executor.

ACP ("Admin-MCP") ships both a FastAPI server and a safety-aware CLI so platform engineers can experiment with the Model Context Protocol while keeping privileged shell access under policy control. The project is feature-complete for its alpha release and is now preparing for its first PyPI upload.

## Table of Contents

1. [Overview](#overview)
2. [Key Features](#key-features)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Usage](#usage)
6. [Configuration](#configuration)
7. [Development](#development)
8. [Contributing](#contributing)
9. [License](#license)

## Overview

The Admin Context Protocol couples a local watchdog CLI (`acp`) with an MCP-ready FastAPI service. The CLI executes shell commands, ships structured logs to the server, and exposes policy gates (`logonly`, `watch`, and `dialog` modes). The server keeps an in-memory prompt registry, provides MCP-style tool endpoints, and enforces the deny/review policy before any privileged operation is executed.

## Key Features

- **One binary, two roles** – `acp serve` launches the FastAPI server, while `acp run ...` keeps acting as the command execution client.
- **Multi-mode policy enforcement** – `logonly` for hands-off logging, `watch` for policy checking before execution, and `dialog` for synchronous tool callbacks.
- **Structured local audit trail** – every shell invocation is logged to JSON in a temp directory and replicated to the MCP server when available.
- **Root synchronization** – the CLI publishes its current working directory so the server can reason about the operator's workspace roots.
- **Prompt analysis** – simple keyword-based prompt registry returns matching runbooks and required arguments to help automate admin tasks.
- **Safe tool execution** – the server exposes a single `shell/execute` tool with policy gating, timeout handling, and dry-run support.

## Installation

> **Python requirement:** 3.11+

### PyPI (coming soon)

Once the package is published:

```bash
pip install acp
```

### From source (recommended for alpha)

```bash
git clone https://github.com/admin-mcp/acp.git
cd acp
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

The editable install exposes the `acp` (and legacy `ai`) console scripts for local testing.

## Quick Start

1. **Run the server** (default host `127.0.0.1`, port `8765`):

   ```bash
   acp serve
   # legacy equivalent
   acp mode serve
   ```

   Leave this process running in its own terminal.

2. **Open a second terminal** and execute commands through ACP:

   ```bash
   acp run uname -a
   acp --timeout 120 run systemctl status nginx
   ```

   The CLI executes your command, writes a JSON log under `$TMPDIR/bash_session_logs`, and posts the entry to the server.

3. **Toggle modes as needed:**

   ```bash
   acp mode            # prints the current mode
   acp mode watch      # switch to watch mode
   acp --set-mode dialog
   ```

4. **Ask the prompt analyzer for guidance:**

   ```bash
   acp --prompt-text "restart nginx"
   ```

   The CLI reports the best-matching prompt template and any required arguments.

## Usage

### Running the server (`acp serve`)

- `acp serve` (or `acp mode serve`) boots the FastAPI app via Uvicorn using the `ACPConfig` defaults.
- Use `CTRL+C` to stop the server.
- For now, host/port customization requires editing the config (see [Configuration](#configuration)).

### Executing commands (`acp run ...`)

- Prepend optional global flags before `run`, e.g. `acp --timeout 600 run "dnf update"`.
- The CLI automatically synchronizes your current working directory roots with the server before execution.
- In `watch` mode, ACP performs a dry-run policy check (deny/review lists live in `PolicyEngine`).
- In `dialog` mode, the CLI immediately follows up with a live `shell/execute` tool call so remote orchestrators can react to the log entry.

### Managing modes

ACP remembers the selected mode across sessions using a JSON file in `XDG_RUNTIME_DIR` (falling back to `/tmp/ai_state.json`). You can manage modes via:

```bash
acp --set-mode watch   # immediate switch
acp mode dialog        # same effect as above
acp mode               # prints current mode
```

### Prompt analysis

Send natural language text to the server to retrieve the closest prompt template:

```bash
acp --prompt-text "clean logs older than 14 days"
```

The CLI prints the template ID, title, description, and argument schema so you can craft the final tool call.

### Tooling and logs

- Use `acp run ...` in `dialog` mode to trigger synchronous tool invocations.
- All structured logs are persisted locally under `$TMPDIR/bash_session_logs/*_shellexecute.json`.
- The `--log` flag is reserved for a future tailing experience; today it prints a placeholder message.

## Configuration

`ACPConfig` centralizes runtime settings:

| Setting | Default | Notes |
| --- | --- | --- |
| `server_host` | `127.0.0.1` | Change to expose the FastAPI server externally (edit `src/acp/config.py` or instantiate your own config). |
| `server_port` | `8765` | Must match between server and client. |
| `state_filename` | `ai_state.json` | Stored under `XDG_RUNTIME_DIR` (or `/tmp`). Tracks the active mode. |
| `log_dir_name` | `bash_session_logs` | Logs live under `$TMPDIR/<log_dir_name>`. |

Advanced users can instantiate `ACPCLI(config=ACPConfig(...))` inside their own launcher script if they need to override these defaults before the CLI reads them.

## Development

1. **Install dev dependencies:** `pip install -e .[dev]`
2. **Run the test suite:**

   ```bash
   pytest
   ```

3. **Type checks / formatting:** The project currently relies on `ruff`-style conventions (PEP 8 + typing). Add any new linters in `pyproject.toml` as needed.
4. **Building wheels for PyPI:**

   ```bash
   python -m build
   twine check dist/*
   ```

   (The `hatchling` backend is configured already; just ensure `README.md` renders on PyPI.)

## Contributing

- Fork the repo and create feature branches.
- Keep changes covered by tests where practical (`pytest`).
- Update the README/design docs when touching user-facing behavior.
- Submit a PR; automation will run the full suite.

## License

Released under the [MIT License](LICENSE).
