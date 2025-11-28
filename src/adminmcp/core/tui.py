import asyncio
from typing import Callable, Optional

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Footer, Header, Label, RichLog, Static

class ConfirmationModal(ModalScreen[bool]):
    """A modal dialog for confirming command execution."""

    def __init__(self, command: str):
        super().__init__()
        self.command = command

    def compose(self) -> ComposeResult:
        yield Container(
            Label(f"Allow execution of command?\n\n{self.command}"),
            Container(
                Button("Yes", variant="success", id="yes"),
                Button("No", variant="error", id="no"),
                classes="buttons",
            ),
            classes="modal-container",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "yes":
            self.dismiss(True)
        else:
            self.dismiss(False)

class TerminalWidget(RichLog):
    """A widget to display terminal output."""
    
    def __init__(self):
        super().__init__(highlight=True, markup=True)

    def write_output(self, data: str) -> None:
        """Write data to the terminal widget."""
        self.write(data)

class AgentTUI(App):
    """The TUI application for the ShellAgent."""

    CSS = """
    Screen {
        align: center middle;
    }

    .modal-container {
        padding: 1 2;
        background: $surface;
        border: thick $primary;
        width: 60;
        height: auto;
    }

    .buttons {
        layout: horizontal;
        align: center middle;
        height: auto;
        margin-top: 1;
    }

    Button {
        margin: 0 1;
    }
    
    TerminalWidget {
        background: $surface-darken-1;
        color: $text;
        border: solid $secondary;
        height: 1fr;
    }
    """

    def __init__(self):
        super().__init__()
        self.terminal = TerminalWidget()
        self.status_bar = Static("Mode: Autonomous | Status: Ready")
        self.pending_confirmation: Optional[asyncio.Future[bool]] = None

    def compose(self) -> ComposeResult:
        yield Header()
        yield Vertical(
            self.terminal,
            self.status_bar,
        )
        yield Footer()

    def update_status(self, mode: str, status: str) -> None:
        """Update the status bar."""
        self.status_bar.update(f"Mode: {mode} | Status: {status}")

    def write_to_terminal(self, data: str) -> None:
        """Write data to the terminal widget."""
        self.terminal.write_output(data)

    async def request_confirmation(self, command: str) -> bool:
        """Request user confirmation for a command."""
        return await self.push_screen(ConfirmationModal(command))