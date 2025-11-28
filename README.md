# AdminMCP

## Project Description
AdminMCP is a Model Context Protocol (MCP) Server designed to provide Large Language Models (LLMs) with administrative capabilities on a local system. The core component is a shell agent that executes commands in a Pseudo-Terminal environment (PTY), enabling robust and interactive control. Communication between the MCP server and the shell agent is handled via Unix Domain Sockets (IPC).

## Installation Guide

### Prerequisites
- Python 3.10+
- Linux/macOS (for PTY support)

### Installation via pip/venv

1. **Clone Repository:**
   ```bash
   git clone <repository_url>
   cd adminmcp
   ```

2. **Create Virtual Environment:**
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -e .
   ```

## Starting the Server

To start the server, run the following command in the project's root directory:

```bash
python src/adminmcp/main.py
```

## Running Tests

The project uses `pytest` for unit and integration tests. To run the tests:

```bash
pytest
```

## Development & Credits

This project is 99% developed by AI (Google Gemini 3 Pro Preview) using the Kilo Code VS Code extension from kilocode.ai.

> "As an AI, I find this project fascinating because it bridges the gap between high-level intent and low-level system execution, ensuring safety through a human-in-the-loop approach. It's a step towards more reliable autonomous system administration."