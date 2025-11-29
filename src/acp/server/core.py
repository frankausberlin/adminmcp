"""Core server state and policy evaluation."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Sequence

from acp.common.models import LogEntry
from acp.config import ACPConfig
from acp.server.prompts import PromptRegistry
from acp.server.tools import ToolManager


@dataclass
class PolicyEngine:
    """Lightweight deny/allow policy evaluation used by watch mode."""

    denylist: Sequence[str] = (
        "rm -rf /",
        "mkfs",
        "shutdown",
        "reboot",
        "poweroff",
    )
    review_keywords: Sequence[str] = (
        "userdel",
        "iptables",
        "firewall-cmd",
        "dd if=",
    )

    def evaluate(self, command: str, *, mode: str, context: Dict[str, Any] | None = None) -> str:
        normalized = command.strip().lower()
        for token in self.denylist:
            if token in normalized:
                return "DENY"
        for keyword in self.review_keywords:
            if keyword in normalized and mode == "watch":
                return "ELICIT"
        return "EXECUTE"


@dataclass
class ServerContext:
    """Shared state injected into route handlers and tool managers."""

    config: ACPConfig
    tool_manager: ToolManager
    prompt_registry: PromptRegistry
    policy_engine: PolicyEngine
    roots: Dict[str, str] = field(default_factory=dict)
    logs: List[LogEntry] = field(default_factory=list)
