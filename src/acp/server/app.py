"""FastAPI application factory for the ACP server."""

from __future__ import annotations

from fastapi import FastAPI

from acp.config import ACPConfig, DEFAULT_CONFIG
from acp.server.core import PolicyEngine, ServerContext
from acp.server.prompts import PromptRegistry
from acp.server.routes import register_routes
from acp.server.tools import ToolManager


def create_app(config: ACPConfig | None = None) -> FastAPI:
    """Create and configure the FastAPI server."""

    resolved_config = config or DEFAULT_CONFIG
    app = FastAPI(title="Admin Context Protocol Server", version="0.1.0")

    tool_manager = ToolManager()
    tool_manager.register_builtin_tools()

    prompt_registry = PromptRegistry()
    policy_engine = PolicyEngine()
    context = ServerContext(config=resolved_config, tool_manager=tool_manager, prompt_registry=prompt_registry, policy_engine=policy_engine)

    register_routes(app, context)
    return app
