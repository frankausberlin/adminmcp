"""Client-side LLM orchestration for the ACP CLI."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple

from openai import OpenAI

from acp.client.api import APIClient
from acp.common.models import ToolCall
from acp.config import ACPConfig

DEFAULT_SYSTEM_PROMPT = (
    "You are the ACP client agent. Interpret the operator's request, "
    "decide whether local ACP tools are required, and return a concise answer. "
    "Use tools only when they are essential. When using tools, wait for results "
    "before forming your final response."
)


class LLMClientError(RuntimeError):
    """Raised when the LLM workflow cannot be completed."""


@dataclass
class ToolSpec:
    """Holds the OpenAI tool definition and mapping to the server tool name."""

    openai_definition: Dict[str, Any]
    server_name: str


class LLMClient:
    """High-level helper that runs the OpenAI-assisted tool calling loop."""

    def __init__(
        self,
        *,
        config: ACPConfig,
        api: APIClient,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
        system_prompt: str = DEFAULT_SYSTEM_PROMPT,
        mode: str = "dialog",
        max_tool_iterations: int = 5,
    ) -> None:
        self.config = config
        self.api = api
        self.mode = mode
        self.max_tool_iterations = max_tool_iterations
        self.system_prompt = system_prompt

        settings = self.config.resolve_llm_settings(api_key=api_key, base_url=base_url, model=model)
        self.api_key = settings.api_key
        self.base_url = settings.base_url
        self.model = settings.model

        if not self.api_key:
            raise LLMClientError(
                "LLM API key is not configured. Set ACP_LLM_KEY or pass --llm-key to the CLI."
            )

        self._client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    def process_request(self, user_request: str, tools: Dict[str, Any] | None = None) -> str:
        """Run the LLM + tool calling loop and return the final assistant answer."""

        if not user_request.strip():
            raise LLMClientError("Cannot process an empty request.")

        tool_specs, alias_map = self._build_tool_specs(tools)
        messages: List[Dict[str, Any]] = [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_request},
        ]

        iterations = 0
        while iterations <= self.max_tool_iterations:
            iterations += 1
            completion_kwargs: Dict[str, Any] = {
                "model": self.model,
                "messages": messages,
            }
            if tool_specs:
                completion_kwargs["tools"] = [spec.openai_definition for spec in tool_specs]
                completion_kwargs["tool_choice"] = "auto"

            try:
                response = self._client.chat.completions.create(**completion_kwargs)
            except Exception as exc:  # pragma: no cover - network/SDK errors
                raise LLMClientError(f"OpenAI API call failed: {exc}") from exc

            choice = response.choices[0]
            assistant_message = choice.message

            if assistant_message.tool_calls:
                messages.append(self._assistant_message_dict(assistant_message))
                self._handle_tool_calls(assistant_message.tool_calls, alias_map, messages)
                continue

            final_content = assistant_message.content or ""
            messages.append({"role": "assistant", "content": final_content})
            return final_content.strip() or "LLM returned an empty response."

        raise LLMClientError(
            "Exceeded maximum tool iterations without concluding the conversation."
        )

    def _assistant_message_dict(self, assistant_message: Any) -> Dict[str, Any]:
        return {
            "role": "assistant",
            "content": assistant_message.content or "",
            "tool_calls": [
                {
                    "id": call.id,
                    "type": call.type,
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
                for call in assistant_message.tool_calls or []
            ],
        }

    def _handle_tool_calls(self, tool_calls: Any, alias_map: Dict[str, str], messages: List[Dict[str, Any]]) -> None:
        for tool_call in tool_calls:
            server_name = alias_map.get(tool_call.function.name, tool_call.function.name)
            arguments = self._parse_arguments(tool_call.function.arguments)
            invocation = ToolCall(name=server_name, arguments=arguments, mode=self.mode)
            try:
                result = self.api.call_tool(invocation)
            except Exception as exc:  # pragma: no cover - network errors
                raise LLMClientError(f"Tool execution failed for {server_name}: {exc}") from exc

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result.model_dump(), ensure_ascii=False),
                }
            )

    def _parse_arguments(self, raw_arguments: str | None) -> Dict[str, Any]:
        if not raw_arguments:
            return {}
        try:
            parsed = json.loads(raw_arguments)
        except json.JSONDecodeError as exc:
            raise LLMClientError(f"Tool arguments are not valid JSON: {raw_arguments}") from exc
        if not isinstance(parsed, dict):
            raise LLMClientError("Tool arguments must decode to an object/dict.")
        return parsed

    def _build_tool_specs(self, raw_listing: Dict[str, Any] | None) -> Tuple[List[ToolSpec], Dict[str, str]]:
        """Convert MCP tool descriptors into OpenAI-compatible tool specs."""

        listing: Dict[str, Any] | None = raw_listing
        if listing is None:
            listing = self.api.list_tools() or {}

        raw_tools: Any
        if isinstance(listing, dict) and "tools" in listing:
            raw_tools = listing.get("tools")
        else:
            raw_tools = listing

        if not isinstance(raw_tools, dict):
            return [], {}

        tool_specs: List[ToolSpec] = []
        alias_map: Dict[str, str] = {}

        for server_name, descriptor in raw_tools.items():
            if not isinstance(descriptor, dict):
                descriptor = {}
            function_name = server_name.replace("/", "__")
            alias_map[function_name] = server_name
            tool_specs.append(
                ToolSpec(
                    openai_definition={
                        "type": "function",
                        "function": {
                            "name": function_name,
                            "description": f"{descriptor.get('description', '')} (Server tool: {server_name})",
                            "parameters": descriptor.get("inputSchema", {"type": "object"}),
                        },
                    },
                    server_name=server_name,
                )
            )

        return tool_specs, alias_map
