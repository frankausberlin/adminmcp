"""Configuration helpers for ACP."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os


@dataclass(frozen=True)
class LLMSettings:
    """Resolved configuration for communicating with the LLM provider."""

    api_key: str | None
    base_url: str
    model: str

    def with_overrides(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> "LLMSettings":
        """Return a copy with overrides applied when provided."""

        return LLMSettings(
            api_key=api_key if api_key is not None else self.api_key,
            base_url=base_url if base_url is not None else self.base_url,
            model=model if model is not None else self.model,
        )


@dataclass(frozen=True)
class ACPConfig:
    """Central configuration object shared across client and server."""

    server_host: str = "127.0.0.1"
    server_port: int = 8765
    state_filename: str = "ai_state.json"
    log_dir_name: str = "bash_session_logs"
    default_llm_base_url: str = "https://api.openai.com/v1"
    default_llm_model: str = "gpt-4o-mini"

    @property
    def base_url(self) -> str:
        """Return the base URL for HTTP calls."""

        return f"http://{self.server_host}:{self.server_port}"

    @property
    def runtime_state_path(self) -> Path:
        """Return the resolved path for the CLI runtime state file."""

        runtime_dir = os.environ.get("XDG_RUNTIME_DIR") or os.environ.get("TMPDIR") or "/tmp"
        return Path(runtime_dir) / self.state_filename

    @property
    def log_dir_path(self) -> Path:
        """Return the directory where the client stores shell logs."""

        temp_dir = os.environ.get("TMPDIR") or os.environ.get("TEMP") or "/tmp"
        return Path(temp_dir) / self.log_dir_name

    @property
    def llm_settings(self) -> LLMSettings:
        """Return the resolved LLM settings from the environment."""

        return LLMSettings(
            api_key=os.environ.get("ACP_LLM_KEY"),
            base_url=os.environ.get("ACP_LLM_BASE_URL") or self.default_llm_base_url,
            model=os.environ.get("ACP_LLM_MODEL") or self.default_llm_model,
        )

    def resolve_llm_settings(
        self,
        *,
        api_key: str | None = None,
        base_url: str | None = None,
        model: str | None = None,
    ) -> LLMSettings:
        """Return LLM settings with optional overrides applied."""

        return self.llm_settings.with_overrides(api_key=api_key, base_url=base_url, model=model)

    @property
    def llm_api_key(self) -> str | None:
        """Return the API key used by the LLM client, if configured."""

        return self.llm_settings.api_key

    @property
    def llm_base_url(self) -> str:
        """Return the OpenAI-compatible base URL for the LLM client."""

        return self.llm_settings.base_url

    @property
    def llm_model(self) -> str:
        """Return the default model name for LLM invocations."""

        return self.llm_settings.model


DEFAULT_CONFIG = ACPConfig()
