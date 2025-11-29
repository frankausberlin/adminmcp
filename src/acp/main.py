"""Entry point for the `ai` console script."""

from __future__ import annotations

from acp.client.cli import ACPCLI
from acp.config import DEFAULT_CONFIG


def main() -> None:
    """Execute the ACP CLI."""

    cli = ACPCLI(config=DEFAULT_CONFIG)
    cli.run()


if __name__ == "__main__":  # pragma: no cover - script entry point
    main()
