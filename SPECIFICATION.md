# AdminMCP Technical Specification

## Version
AdminMCP v0.1.0

## Overview

AdminMCP is a dual-purpose tool that serves as both a command-line interface (CLI) for managing Model Context Protocol (MCP) servers and an MCP server implementation itself. The system provides a robust environment for system administration tasks through MCP-compatible agents.

### Architecture Components

- **CLI Tool (`acp`)**: Command-line interface for server lifecycle management
- **MCP Server**: FastMCP-based server providing tools and resources for administrative operations
- **Configuration System**: User-configurable settings stored in `~/.config/adminmcp/`
- **Logging System**: Structured logging with file rotation and configurable verbosity
- **Client** *(Planned)*: MCP client for connecting to and interacting with MCP servers

## CLI Interface Specification

### Command Structure

The AdminMCP CLI follows a hierarchical command structure using Python's `argparse` module.

#### Main Command
```bash
acp [COMMAND] [OPTIONS]
```

#### Available Commands

##### `acp server`
Manage the MCP server lifecycle.

**Subcommands:**
- `acp server start`: Start the MCP server as a background process
- `acp server stop`: Stop the running MCP server process

##### `acp init`
Initialize the AdminMCP configuration system.

#### Command Line Arguments

| Argument | Type | Description | Required |
|----------|------|-------------|----------|
| `--help` | Flag | Display help information | No |
| `command` | String | Main command (server, init) | Yes |
| `action` | String | Server action (start, stop) | Yes (for server command) |

### CLI Behavior Specifications

#### Server Start Command (`acp server start`)

**Preconditions:**
- No existing server process running (checked via PID file)
- Executable permissions on `src/adminmcp/server/acp_server.py`

**Process:**
1. Check if server is already running by reading `~/.config/adminmcp/acp_server.pid`
2. If PID exists, verify process is alive using `os.kill(pid, 0)`
3. If server not running, launch subprocess: `python src/adminmcp/server/acp_server.py`
4. Capture subprocess PID and write to `~/.config/adminmcp/acp_server.pid`
5. Output: "Server started."

**Error Conditions:**
- Server already running: Output "Server is already running." (WARNING level)
- Subprocess launch failure: Output "Failed to start server: {exception}" (ERROR level)

**Postconditions:**
- Server process running in background
- PID file contains valid process ID
- Log entry: "Server started with PID {pid}"

#### Server Stop Command (`acp server stop`)

**Preconditions:**
- PID file exists at `~/.config/adminmcp/acp_server.pid`

**Process:**
1. Read PID from `~/.config/adminmcp/acp_server.pid`
2. Send SIGTERM signal to process: `os.kill(pid, signal.SIGTERM)`
3. Remove PID file
4. Output: "Server stopped."

**Error Conditions:**
- PID file not found: Output "Server is not running." (WARNING level)
- Process not running: Output "Server was not running." (WARNING level), remove stale PID file
- Kill failure: Output "Failed to stop server: {exception}" (ERROR level)

**Postconditions:**
- Server process terminated
- PID file removed
- Log entry: "Server stopped successfully"

#### Init Command (`acp init`)

**Process:**
1. Create directory `~/.config/adminmcp/` if not exists
2. Copy `config.adminmcp.json` to `~/.config/adminmcp/config.adminmcp.json` (if not exists)
3. Create `~/.config/adminmcp/mcp_settings.json` with default content (if not exists)
4. Output copy/create messages

**Default `mcp_settings.json` content:**
```json
{
    "mcpServers": {}
}
```

**Postconditions:**
- Configuration directory exists
- Configuration files initialized
- Log entry: "Configuration initialized successfully"

### CLI Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | General error |
| 2 | Command line parsing error |

## Server Architecture Specification

### MCP Server Implementation

AdminMCP server is built using the FastMCP framework, providing a standardized MCP server implementation.

#### Server Initialization

**Entry Point:** `src/adminmcp/server/acp_server.py`

**Initialization Sequence:**
1. Import required modules with fallback handling
2. Setup logging via `adminmcp.logging_config.setup_logging()`
3. Create FastMCP instance: `mcp = FastMCP("AdminMCP Server")`
4. Register tools and resources
5. Call `mcp.run()` to start the server

#### Tool Registration

Tools are registered using the `@mcp.tool()` decorator.

##### Available Tools

###### `add(a: int, b: int) -> int`
**Description:** Add two integers
**Parameters:**
- `a`: First integer
- `b`: Second integer
**Returns:** Sum of a and b
**Implementation:** `return a + b`

###### `subtract(a: int, b: int) -> int`
**Description:** Subtract two integers
**Parameters:**
- `a`: Minuend
- `b`: Subtrahend
**Returns:** Difference of a and b
**Implementation:** `return a - b`

###### `multiply(a: int, b: int) -> int`
**Description:** Multiply two integers
**Parameters:**
- `a`: First factor
- `b`: Second factor
**Returns:** Product of a and b
**Implementation:** `return a * b`

###### `divide(a: int, b: int) -> float | None`
**Description:** Divide two numbers
**Parameters:**
- `a`: Dividend
- `b`: Divisor
**Returns:** Quotient if b ≠ 0, None if b = 0
**Implementation:** `return a / b if b != 0 else None`

#### Resource Registration

Resources are registered using the `@mcp.resource()` decorator with URI templates.

##### Available Resources

###### `resource://math/constant/{name}`
**Description:** Access mathematical constants
**URI Parameters:**
- `name`: Constant name (pi, e, tau)
**Returns:** Float value or None if not found
**Supported Constants:**
- `pi`: π (3.141592653589793)
- `e`: e (2.718281828459045)
- `tau`: τ (6.283185307179586)

###### `resource://number/{n}/is_even`
**Description:** Check if a number is even
**URI Parameters:**
- `n`: Integer to check
**Returns:** Boolean (true if even, false if odd)
**Implementation:** `return n % 2 == 0`

###### `resource://datetime/current`
**Description:** Get current datetime information
**Returns:** Dictionary with:
- `datetime`: ISO 8601 formatted datetime string
- `timezone`: Timezone name
- `unix_timestamp`: Unix timestamp (float)

**Timezone Handling:**
- Attempts to use `pytz` library if available
- Falls back to `zoneinfo.ZoneInfo` if available
- Defaults to system timezone or UTC

###### `resource://wikipedia/article/{title}`
**Description:** Fetch Wikipedia article summary
**URI Parameters:**
- `title`: Article title (URL encoded)
**Returns:** Wikipedia API response JSON or error dict
**API Endpoint:** `https://en.wikipedia.org/api/rest_v1/page/summary/{title}`
**Headers:** `User-Agent: Python MCP server`
**Error Handling:** Returns `{"error": "Article not found", "title": title}` for 404 responses

### Server Runtime Behavior

**Startup Process:**
1. Log "Starting AdminMCP Server"
2. Initialize FastMCP server
3. Register all tools and resources
4. Log "MCP server is starting up"
5. Enter event loop via `mcp.run()`

**Shutdown Process:**
- Graceful shutdown on SIGTERM/SIGINT
- Log any exceptions during shutdown

**Error Handling:**
- All exceptions during server operation are logged at ERROR level
- Server continues running unless fatal error occurs

## Configuration System Specification

### Configuration File Locations

| File | Location | Purpose |
|------|----------|---------|
| `config.adminmcp.json` | `~/.config/adminmcp/config.adminmcp.json` | Application configuration |
| `mcp_settings.json` | `~/.config/adminmcp/mcp_settings.json` | MCP server settings |

### Configuration File Formats

#### `config.adminmcp.json` Format

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

**Field Specifications:**

- `application.config_folder`: String, default "~/.config/adminmcp"
- `application.log_folder`: String, default "~/.local/share/adminmcp/logs"
- `application.data_folder`: String, default "~/.local/share/adminmcp/data"
- `application.logging_level`: String enum ["debug", "info", "warning", "error", "critical"], default "info"
- `server.port`: Integer, default 8000
- `client`: Object, currently empty (reserved for future use)

#### `mcp_settings.json` Format

```json
{
    "mcpServers": {},
    "acpServerPort": 8080,
    "acpLoggingLevel": "info"
}
```

**Field Specifications:**

- `mcpServers`: Object mapping server names to configurations (future use)
- `acpServerPort`: Integer, server listening port, default 8080
- `acpLoggingLevel`: String enum, logging verbosity, default "info"

### Configuration Loading Behavior

**Load Order:**
1. Use default configuration values
2. Override with values from `config.adminmcp.json` if file exists
3. Ignore file if JSON parsing fails (use defaults)

**Path Expansion:**
- Paths containing `~` are expanded using `Path.expanduser()`
- Relative paths are resolved relative to configuration file location

## Logging Mechanism Specification

### Logging Configuration

**Configuration Source:** `src/adminmcp/logging_config.py`

**Setup Function:** `setup_logging()`

### Log File Management

**Log Directory:** Configurable via `application.log_folder`, default `~/.local/share/adminmcp/logs`

**Log File:** `adminmcp.log` with rotation

**Rotation Policy:**
- Maximum file size: 10 MB
- Backup count: 5 files
- Rotation creates: `adminmcp.log.1`, `adminmcp.log.2`, etc.

### Log Format

**Format String:** `'%(asctime)s - %(name)s - %(levelname)s - %(message)s'`

**Example Output:**
```
2024-01-15 10:30:45,123 - adminmcp.cli - INFO - Server started with PID 12345
```

### Log Levels

**Supported Levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General information about program execution
- `WARNING`: Warning messages for potentially harmful situations
- `ERROR`: Error messages for serious problems
- `CRITICAL`: Critical errors that may prevent program execution

**Level Mapping:**
- String values in config are converted to uppercase
- Invalid strings default to `INFO` level

### Handler Configuration

**File Handler:**
- `logging.handlers.RotatingFileHandler`
- Logs to file with rotation

**Console Handler:**
- `logging.StreamHandler`
- Logs to stderr/stdout
- Same formatter as file handler

### Logger Hierarchy

**Root Logger:** Configured with specified level and handlers

**Module Loggers:** Inherit configuration from root logger

**Logger Names:**
- `adminmcp.cli`: CLI operations
- `adminmcp.server.acp_server`: Server operations
- `adminmcp.logging_config`: Logging setup

## MCP Integration Specification

### MCP Protocol Compliance

**Protocol Version:** Model Context Protocol v1.0

**Server Type:** FastMCP-based server

**Transport:** Stdio (for CLI integration), HTTP/WebSocket (planned)

### Tool Discovery

**Discovery Method:** Automatic via `@mcp.tool()` decorator

**Tool Metadata:**
- Name: Function name
- Description: Function docstring
- Parameters: Type hints
- Return type: Type hints

### Resource Discovery

**Discovery Method:** Automatic via `@mcp.resource()` decorator

**Resource Metadata:**
- URI Template: Decorator parameter
- Description: Function docstring
- Parameters: URI template variables

### MCP Client Integration (Future)

**Planned Features:**
- Server connection management
- Tool execution via MCP protocol
- Resource access via MCP protocol
- Interactive REPL mode

## Future Client Functionality Specification

### Planned Architecture

**Client Components:**
- Connection manager for MCP servers
- Tool execution engine
- Resource access layer
- Interactive command interface

### Client Configuration

**Configuration File:** `~/.config/adminmcp/client.json`

**Planned Structure:**
```json
{
    "servers": {
        "server_name": {
            "url": "http://localhost:8080",
            "transport": "websocket",
            "auth": {}
        }
    },
    "default_server": "server_name"
}
```

### Client Commands (Planned)

#### `acp client connect <server>`
Connect to specified MCP server

#### `acp client list-tools <server>`
List available tools on server

#### `acp client call-tool <server> <tool> [args...]`
Execute tool on server

#### `acp client get-resource <server> <uri>`
Fetch resource from server

#### `acp client repl <server>`
Start interactive REPL with server

## API Specifications

### Internal APIs

#### CLI Module API

**Functions:**
- `main()`: Entry point for CLI
- `start_server()`: Start MCP server process
- `stop_server()`: Stop MCP server process
- `init_config()`: Initialize configuration
- `is_server_running()`: Check server status

#### Server Module API

**Classes:**
- `FastMCP`: MCP server instance

**Decorators:**
- `@mcp.tool()`: Register tool function
- `@mcp.resource()`: Register resource function

#### Logging Module API

**Functions:**
- `setup_logging()`: Configure logging system

### External APIs

#### MCP Protocol API

**Tool Calling:**
- Request: `{"method": "tools/call", "params": {"name": "add", "arguments": {"a": 1, "b": 2}}}`
- Response: `{"result": 3}`

**Resource Access:**
- Request: `{"method": "resources/read", "params": {"uri": "resource://math/constant/pi"}}`
- Response: `{"contents": [{"text": "3.141592653589793"}]}`

## File Formats

### Configuration Files

**Format:** JSON

**Encoding:** UTF-8

**Validation:** Schema-based (future implementation)

### Log Files

**Format:** Plain text with structured format

**Encoding:** UTF-8

**Rotation:** Automatic size-based rotation

### PID Files

**Format:** Single line containing integer PID

**Location:** `~/.config/adminmcp/acp_server.pid`

**Content Example:** `12345\n`

## Implementation Details

### Dependencies

**Core Dependencies:**
- `mcp`: Model Context Protocol library
- `fastmcp`: FastMCP server framework

**Optional Dependencies:**
- `pytz`: Enhanced timezone support
- `zoneinfo`: Modern timezone support (Python 3.9+)

### Directory Structure

```
adminmcp/
├── cli.py                 # CLI entry point
├── logging_config.py      # Logging configuration
├── server/
│   ├── acp_server.py     # MCP server implementation
│   └── server.py          # Legacy server (deprecated)
└── client/                # Future client implementation (empty)
```

### Process Management

**Server Process:**
- Background execution via `subprocess.Popen`
- PID tracking in file
- Signal-based termination (SIGTERM)

**CLI Process:**
- Foreground execution
- Synchronous operations
- Immediate feedback

### Error Handling

**CLI Errors:**
- Invalid commands: argparse error handling
- Server operations: Try/catch with user feedback
- Configuration: Graceful fallback to defaults

**Server Errors:**
- Tool execution: Exception handling with logging
- Resource access: HTTP error handling
- Initialization: Fatal error on startup failure

### Security Considerations

**File Permissions:**
- Configuration directory: User-only access (0700)
- Log files: User-only access (0600)
- PID files: User-only access (0600)

**Network Security:**
- No network exposure in current version
- Future client: TLS support planned

**Input Validation:**
- JSON parsing with error handling
- Path traversal prevention via Path operations
- Command injection prevention via subprocess arguments

### Performance Characteristics

**Startup Time:** < 1 second (typical)

**Memory Usage:** < 50 MB baseline

**Tool Execution:** Synchronous, < 100ms for mathematical operations

**Resource Access:** Network-dependent for external resources

### Testing Strategy

**Unit Tests:**
- Tool function correctness
- Configuration loading
- CLI argument parsing

**Integration Tests:**
- Server startup/shutdown
- MCP protocol compliance
- Configuration persistence

**End-to-End Tests:**
- CLI workflow testing
- MCP client integration (future)

---

This specification serves as the comprehensive technical reference for AdminMCP implementation and can be used to generate detailed man pages and documentation.