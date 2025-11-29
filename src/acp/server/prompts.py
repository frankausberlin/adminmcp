"""Prompt repository abstraction."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Dict, Iterable, List, Optional

from acp.common.models import PromptAnalysisRequest, PromptAnalysisResponse, PromptArgument


@dataclass
class PromptTemplate:
    prompt_id: str
    title: str
    description: str
    arguments: List[PromptArgument] = field(default_factory=list)
    keywords: List[str] = field(default_factory=list)


class PromptRegistry:
    """Manage prompt templates for different admin personas."""

    def __init__(self) -> None:
        self._prompts: Dict[str, PromptTemplate] = {}
        self._load_defaults()

    def _load_defaults(self) -> None:
        self.register(
            PromptTemplate(
                prompt_id="/clean_logs",
                title="Clean Logs by Service and Age",
                description="Safely removes old log files for a specific service.",
                arguments=[
                    PromptArgument(name="service_name", type="string", description="Service name"),
                    PromptArgument(name="age_days", type="integer", description="Minimum age in days"),
                ],
                keywords=["log", "cleanup", "journalctl", "rotate"],
            )
        )
        self.register(
            PromptTemplate(
                prompt_id="/restart_service",
                title="Restart a Managed Service",
                description="Runs systemctl commands to restart a service with safety checks.",
                arguments=[
                    PromptArgument(name="service_name", type="string", description="systemd service name"),
                ],
                keywords=["restart", "systemctl", "service"],
            )
        )

    def register(self, template: PromptTemplate) -> None:
        self._prompts[template.prompt_id] = template

    def load_prompts(self, path: Path | str) -> None:
        source = Path(path)
        payload = json.loads(source.read_text(encoding="utf-8"))
        templates: Iterable[dict] = payload if isinstance(payload, list) else payload.get("prompts", [])
        for item in templates:
            template = PromptTemplate(
                prompt_id=item["id"],
                title=item["title"],
                description=item["description"],
                arguments=[
                    PromptArgument(**argument) for argument in item.get("arguments", [])
                ],
                keywords=item.get("keywords", []),
            )
            self.register(template)

    def find_match(self, text: str) -> Optional[PromptTemplate]:
        if not self._prompts:
            return None
        normalized = text.lower()
        best_score = -1
        best_prompt: Optional[PromptTemplate] = None
        for prompt in self._prompts.values():
            if not prompt.keywords:
                if best_prompt is None:
                    best_prompt = prompt
                continue
            score = sum(1 for keyword in prompt.keywords if keyword in normalized)
            if score > best_score:
                best_score = score
                best_prompt = prompt
        return best_prompt or next(iter(self._prompts.values()))

    def analyze(self, request: PromptAnalysisRequest) -> dict:
        prompt = self.find_match(request.text)
        if prompt is None:
            return PromptAnalysisResponse(prompt_id=None, title=None, description=None, arguments=[]).model_dump()
        response = PromptAnalysisResponse(
            prompt_id=prompt.prompt_id,
            title=prompt.title,
            description=prompt.description,
            arguments=prompt.arguments,
        )
        return response.model_dump()
