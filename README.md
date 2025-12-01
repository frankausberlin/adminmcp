# AdminMCP (ACP)

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io/)

A comprehensive MCP (Model Context Protocol) based agent environment for system administration and automation tasks. AdminMCP provides both a CLI tool for managing MCP servers and a server implementation with built-in tools and resources for administrative operations.

## 📋 Table of Contents

- [Project Description](#-project-description)
- [Features](#-features)
- [Installation](#-installation)
- [Usage Examples](#-usage-examples)
- [Configuration](#-configuration)
- [Development Setup](#-development-setup)
- [Testing](#-testing)
- [Contributing](#-contributing)
- [License](#-license)

## 🎯 Project Description

AdminMCP is a dual-purpose tool that serves as both a command-line interface (CLI) for managing MCP servers and an MCP server itself. The project aims to create a robust environment for system administration tasks through MCP-compatible agents.

The CLI component (`acp`) provides easy management of MCP server processes, while the server component offers a collection of tools and resources for common administrative and computational tasks. Future versions will include client functionality for connecting to and interacting with MCP servers.

### Architecture

- **CLI Tool**: Command-line interface for server lifecycle management
- **MCP Server**: FastMCP-based server providing tools and resources
- **Configuration System**: User-configurable settings stored in `~/.config/adminmcp/`
- **Client** *(Planned)*: MCP client for connecting to servers and executing tasks

## ✨ Features

### Current Features

#### CLI Server Management
- **Server Control**: Start and stop MCP servers as background processes
- **Process Management**: Automatic PID tracking and safe process termination
- **Safety Checks**: Prevents multiple server instances and handles edge cases

#### MCP Server Tools
- **Mathematical Operations**: Add, subtract, multiply, divide numbers
- **Mathematical Constants**: Access to π, e, τ via resource endpoints
- **Number Utilities**: Check if numbers are even/odd
- **DateTime Resources**: Current datetime with timezone information
- **Wikipedia Integration**: Fetch article summaries from Wikipedia

#### Configuration Management
- **Initialization**: Automated setup of configuration directories
- **User Settings**: Customizable server port and logging levels
- **MCP Server Registry**: Management of connected MCP servers

### Planned Features

#### Client Functionality
- **Server Connection**: Connect to MCP servers via WebSocket/SSE
- **Tool Execution**: Remote execution of server-provided tools
- **Resource Access**: Query server resources programmatically
- **Interactive Mode**: REPL for interactive server interaction

#### Advanced Administration Tools
- **System Monitoring**: CPU, memory, disk usage tools
- **File Operations**: Safe file manipulation tools
- **Network Utilities**: DNS lookup, port scanning, connectivity tests
- **Process Management**: List, start, stop system processes

## 🚀 Installation

### Prerequisites

- Python 3.11 or higher
- `uv` package manager (recommended) or `pip`

### Install from Source

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/adminmcp.git
   cd adminmcp
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   # Using uv (recommended)
   uv pip install -e .

   # Or using pip
   pip install -e .
   ```

4. **Verify installation:**
   ```bash
   acp --help
   ```

### Using uv (Recommended)

```bash
# Install uv if not already installed
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install AdminMCP
uv pip install -e .
```

## 📖 Usage Examples

### Basic Server Management

**Start the MCP server:**
```bash
acp server start
# Output: Server started.
```

**Stop the MCP server:**
```bash
acp server stop
# Output: Server stopped.
```

**Initialize configuration:**
```bash
acp init
# Output:
# Copied config.adminmcp.json to /home/user/.config/adminmcp/config.adminmcp.json
# Created /home/user/.config/adminmcp/mcp_settings.json
# Configuration initialized.
```

### Testing with MCP Inspector

The easiest way to test the server is using the MCP Inspector:

```bash
mcp dev ./src/adminmcp/server/acp_server.py
```

This starts the MCP Inspector UI where you can interact with all available tools and resources.

### Programmatic Usage

The server can be used programmatically through MCP clients. Here are some example tool calls:

```python
# Mathematical operations
result = add(5, 3)  # Returns 8
result = multiply(4, 7)  # Returns 28

# Resource access
pi_value = get_constant("pi")  # Returns 3.141592653589793
is_even = is_even(42)  # Returns True

# DateTime information
current = current_datetime()
# Returns: {"datetime": "2024-01-01T12:00:00+00:00", "timezone": "UTC", "unix_timestamp": 1704110400.0}

# Wikipedia lookup
article = wikipedia_article("Python (programming language)")
# Returns article summary JSON
```

## ⚙️ Configuration

AdminMCP uses a configuration system stored in `~/.config/adminmcp/`. The configuration is initialized automatically with the `acp init` command.

### Configuration Files

#### `config.adminmcp.json`
Template configuration file with default settings:

```json
{
    "application": {
        "config_folder": "~/.config/adminmcp",
        "log_folder": "~/.local/share/adminmcp/logs",
        "data_folder": "~/.local/share/adminmcp/data",
        "logging_level": "info"
    },
    "server": {
        "port": 8000
    },
    "client": {}
}
```

#### `mcp_settings.json`
Runtime configuration for MCP server settings:

```json
{
    "mcpServers": {},
    "acpServerPort": 8080,
    "acpLoggingLevel": "info"
}
```

### Configuration Options

- **`acpServerPort`**: Port number for the AdminMCP server (default: 8080)
- **`acpLoggingLevel`**: Logging verbosity - "debug", "info", "warning", "error" (default: "info")
- **`mcpServers`**: Registry of configured MCP servers (for future client functionality)

### Customizing Configuration

1. Run initialization: `acp init`
2. Edit `~/.config/adminmcp/mcp_settings.json` with your preferred settings
3. Restart the server for changes to take effect

## 🛠️ Development Setup

### Development Environment

1. **Clone and setup:**
   ```bash
   git clone https://github.com/yourusername/adminmcp.git
   cd adminmcp
   uv venv
   source .venv/bin/activate
   uv pip install -e .
   ```

2. **Install development dependencies:**
   ```bash
   uv pip install pytest pytest-asyncio
   ```

3. **Run tests:**
   ```bash
   pytest
   ```

### Project Structure

```
adminmcp/
├── cli.py                 # Main CLI entry point
├── logging_config.py      # Logging configuration
├── server/
│   ├── acp_server.py     # MCP server implementation
│   └── server.py          # Additional server utilities
└── client/                # Future client implementation
```

### Development Workflow

1. **Make changes** to source files in `src/adminmcp/`
2. **Run tests** to ensure functionality
3. **Test with MCP Inspector** for server changes
4. **Update documentation** as needed

### Adding New Tools

To add new MCP tools to the server:

```python
@mcp.tool()
def your_tool_name(param1: type, param2: type) -> return_type:
    """Tool description for MCP discovery."""
    # Implementation here
    return result
```

### Adding New Resources

To add new MCP resources:

```python
@mcp.resource("resource://your/resource/{param}")
def your_resource(param: str) -> dict:
    """Resource description."""
    # Implementation here
    return data
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=adminmcp

# Run specific test file
pytest tests/test_cli.py
```

### Test Structure

Tests are organized in the `tests/` directory. Currently, the test suite includes:

- CLI command tests
- Server functionality tests
- Configuration management tests

### Writing Tests

Example test structure:

```python
import pytest
from adminmcp.cli import start_server, stop_server

def test_server_start_stop():
    # Test server lifecycle
    start_server()
    # Assertions here
    stop_server()
    # Assertions here
```

## 🤝 Contributing

We welcome contributions to AdminMCP! Here's how you can help:

### Development Process

1. **Fork the repository** on GitHub
2. **Create a feature branch**: `git checkout -b feature/your-feature-name`
3. **Make your changes** following the coding standards
4. **Add tests** for new functionality
5. **Run the test suite**: `pytest`
6. **Update documentation** if needed
7. **Submit a pull request**

### Coding Standards

- **Python Style**: Follow PEP 8 guidelines
- **Type Hints**: Use type annotations for function parameters and return values
- **Documentation**: Add docstrings to all public functions and classes
- **Logging**: Use the provided logging configuration
- **Error Handling**: Implement proper exception handling

### Areas for Contribution

- **New MCP Tools**: Add administrative tools (file operations, system monitoring, etc.)
- **Client Implementation**: Build the MCP client functionality
- **Documentation**: Improve documentation and examples
- **Testing**: Expand test coverage
- **Performance**: Optimize server performance and resource usage

### Reporting Issues

- **Bug Reports**: Use GitHub Issues with detailed reproduction steps
- **Feature Requests**: Describe the use case and expected behavior
- **Security Issues**: Contact maintainers directly

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Model Context Protocol](https://modelcontextprotocol.io/) for the underlying protocol
- [FastMCP](https://github.com/jlowin/fastmcp) for the Python MCP server implementation
- The open-source community for inspiration and tools

---

**AdminMCP** is an ongoing project. Stay tuned for updates and new features!