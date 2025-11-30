"""Command-line interface for the ACP client."""

from __future__ import annotations

import argparse
import asyncio
import os
import sys
from typing import Sequence

from uvicorn import Config, Server

from acp.client.api import APIClient
from acp.client.executor import CommandExecutor
from acp.client.llm import LLMClient, LLMClientError
from acp.client.state import ACPMode, StateManager
from acp.common.models import PromptAnalysisRequest, ToolCall
from acp.config import ACPConfig
from acp.server.app import create_app

WATCHABLE_MODES: tuple[ACPMode, ...] = ("logonly", "watch", "dialog")


class ACPCLI:
    """High-level facade coordinating command execution and server calls."""

    def __init__(self, config: ACPConfig) -> None:
        self.config = config
        self.state = StateManager(config)
        self.executor = CommandExecutor(config)
        self.api = APIClient(config)

    def run(self, argv: Sequence[str] | None = None) -> None:
        parser = self._build_parser()
        args = parser.parse_args(argv)

        if args.set_mode:
            self._handle_mode_switch(args.set_mode)
            return
        if args.prompt_text:
            self._handle_prompt(args.prompt_text)
            return

        command = args.command or []
        if command:
            head, tail = command[0], command[1:]
            if head == "serve":
                self._start_server()
                return
            if head == "run":
                if not tail:
                    parser.error("'acp run' requires a command to execute")
                self._handle_command(tail, timeout=args.timeout)
                return
            if head == "mode":
                self._handle_mode_command(tail)
                return
            if head == "ask":
                if not tail:
                    parser.error("'acp ask' requires a prompt")
                prompt_text = " ".join(tail).strip()
                if not prompt_text:
                    parser.error("'acp ask' requires a non-empty prompt")
                self._handle_ask(
                    prompt_text,
                    llm_key=args.llm_key,
                    llm_base_url=args.llm_base_url,
                    llm_model=args.llm_model,
                )
                return
            self._handle_command(command, timeout=args.timeout)
            return

        if args.log:
            self._handle_log_mode(args)
            return
        parser.print_help()

    def _build_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(description="Admin Context Protocol CLI")
        parser.add_argument("-t", "--timeout", type=int, default=7200, help="Execution timeout in seconds")
        parser.add_argument("-s", "--set-mode", dest="set_mode", choices=WATCHABLE_MODES, help="Immediately switch active mode")
        parser.add_argument("--log", action="store_true", help="Display command logs (stub)")
        parser.add_argument("-p", "--prompt-text", help="Natural language prompt to analyze")
        parser.add_argument("--llm-key", dest="llm_key", help="Override the LLM API key (defaults to ACP_LLM_KEY)")
        parser.add_argument(
            "--llm-base-url",
            dest="llm_base_url",
            help="Override the OpenAI-compatible base URL (defaults to ACP_LLM_BASE_URL or config)",
        )
        parser.add_argument("--llm-model", dest="llm_model", help="Override the LLM model name")
        parser.add_argument(
            "command",
            nargs=argparse.REMAINDER,
            help="Use 'serve' to launch the server, 'run <cmd>' to execute a shell command, or 'mode <value>' to manage modes",
        )
        return parser

    def _handle_mode_command(self, parts: Sequence[str]) -> None:
        if not parts:
            print(f"Current mode: {self.state.get_mode()}")
            return
        target = parts[0]
        if target == "serve":
            self._start_server()
            return
        if target not in WATCHABLE_MODES:
            print(f"Unknown mode '{target}'. Valid modes: {', '.join(WATCHABLE_MODES)}")
            return
        self._handle_mode_switch(target)  # type: ignore[arg-type]

    def _start_server(self) -> None:
        app = create_app(self.config)
        config = Config(app=app, host=self.config.server_host, port=self.config.server_port, log_level="info")
        server = Server(config)
        asyncio.run(server.serve())

    def _handle_mode_switch(self, mode: ACPMode) -> None:
        self.state.set_mode(mode)
        print(f"Mode switched to {mode}")

    def _handle_command(self, command: Sequence[str], timeout: int) -> None:
        filtered_command = [arg for arg in command if arg]
        if not filtered_command:
            raise ValueError("No command supplied for execution")
        command_line = " ".join(filtered_command)
        current_mode = self.state.get_mode()

        self._publish_current_roots()

        if current_mode == "watch" and not self._policy_allows_execution(command_line, current_mode):
            print("Command blocked by policy engine.", file=sys.stderr)
            return

        entry = self.executor.run(filtered_command, timeout=timeout)
        print(entry.model_dump_json(indent=2))

        self.api.send_log(entry)

        if current_mode == "dialog":
            tool_call = ToolCall(name="shell/execute", arguments={"command": command_line, "dry_run": False}, mode=current_mode)
            try:
                result = self.api.call_tool(tool_call)
                print(result.model_dump_json(indent=2))
            except Exception as exc:  # pragma: no cover - network errors
                print(f"Failed to call tool: {exc}", file=sys.stderr)

    def _policy_allows_execution(self, command_line: str, mode: ACPMode) -> bool:
        tool_call = ToolCall(name="shell/execute", arguments={"command": command_line, "dry_run": True}, mode=mode)
        try:
            decision = self.api.call_tool(tool_call)
            return decision.status == "EXECUTE"
        except Exception:
            # Fail open if the server is unavailable to avoid blocking local workflows.
            return True

    def _publish_current_roots(self) -> None:
        cwd = os.getcwd()
        try:
            self.api.update_roots({"cwd": cwd})
        except Exception:
            # Roots synchronization is best-effort.
            pass

    def _handle_prompt(self, prompt_text: str) -> None:
        request = PromptAnalysisRequest(text=prompt_text, mode=self.state.get_mode())
        try:
            response = self.api.analyze_prompt(request)
        except Exception as exc:  # pragma: no cover - network errors
            print(f"Prompt analysis failed: {exc}", file=sys.stderr)
            return
        print("Prompt match:")
        print(f"  id: {response.prompt_id}")
        print(f"  title: {response.title}")
        print(f"  description: {response.description}")
        if response.arguments:
            print("  arguments:")
            for arg in response.arguments:
                flag = "(required)" if arg.required else "(optional)"
                print(f"    - {arg.name} [{arg.type}] {flag}: {arg.description or ''}")

    def _handle_ask(
        self,
        prompt_text: str,
        *,
        llm_key: str | None,
        llm_base_url: str | None,
        llm_model: str | None,
    ) -> None:
        try:
            llm_client = LLMClient(
                config=self.config,
                api=self.api,
                api_key=llm_key,
                base_url=llm_base_url,
                model=llm_model,
            )
            tool_listing = self.api.list_tools()
            if tool_listing is None:
                print("Warning: Unable to fetch tool inventory; proceeding without tools.", file=sys.stderr)
            answer = llm_client.process_request(prompt_text, tools=tool_listing)
        except LLMClientError as exc:
            print(f"LLM request failed: {exc}", file=sys.stderr)
            return
        except Exception as exc:  # pragma: no cover - SDK/runtime errors
            print(f"Unexpected LLM failure: {exc}", file=sys.stderr)
            return
        print(answer)

    def _handle_log_mode(self, args: argparse.Namespace) -> None:
        print("Log viewing is not yet implemented in this scaffold.")
