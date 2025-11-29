"""API routes for the ACP server."""

from __future__ import annotations

from fastapi import APIRouter, FastAPI, HTTPException

from acp.common.models import (
    LogEntry,
    PromptAnalysisRequest,
    PromptAnalysisResponse,
    RootUpdateRequest,
    ServerResponse,
    ToolCall,
    ToolInvocationResult,
)
from acp.server.core import ServerContext


def register_routes(app: FastAPI, context: ServerContext) -> None:
    router = APIRouter(prefix="/api/v1")

    @router.post("/roots/update", response_model=ServerResponse)
    async def update_roots(payload: RootUpdateRequest) -> ServerResponse:
        context.roots = payload.roots
        return ServerResponse(message="Roots updated", data=context.roots)

    @router.post("/log/submit", response_model=ServerResponse)
    async def submit_log(entry: LogEntry) -> ServerResponse:
        context.logs.append(entry)
        return ServerResponse(message="Log stored")

    @router.post("/prompt/analyze", response_model=PromptAnalysisResponse)
    async def analyze_prompt(request: PromptAnalysisRequest) -> PromptAnalysisResponse:
        payload = context.prompt_registry.analyze(request)
        return PromptAnalysisResponse(**payload)

    @router.post("/tools/call", response_model=ToolInvocationResult)
    async def tools_call(call: ToolCall) -> ToolInvocationResult:
        try:
            return await context.tool_manager.execute(call, context)
        except ValueError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    @router.get("/tools/list")
    async def list_tools() -> dict:
        return {"tools": context.tool_manager.list_tools()}

    app.include_router(router)
