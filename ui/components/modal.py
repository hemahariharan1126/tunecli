"""
Modal Component — Premium popup dialog for track selection.
"""

from textual.app import ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Label, OptionList, Button, Rule
from textual.containers import Container, Vertical


# Badge styles for option rankings
_BADGES = [
    "[bold green](ID)[/bold green]",   # Exact / Identity match
    "[bold cyan](SIM)[/bold cyan]",     # Similar
    "[bold blue](SIM)[/bold blue]",
    "[bold dim](SIM)[/bold dim]",
    "[dim](SIM)[/dim]",
]


class SelectionModal(ModalScreen[int]):
    """A styled modal dialog to select a track from a list of options."""

    BINDINGS = [("escape", "dismiss_modal", "Cancel")]

    def __init__(self, title: str, options: list[dict]):
        super().__init__()
        self.modal_title = title
        self.options     = options

    def compose(self) -> ComposeResult:
        display_items = []
        for i, opt in enumerate(self.options):
            badge  = _BADGES[min(i, len(_BADGES) - 1)]
            title  = opt.get("title", "Unknown")
            artist = opt.get("artist", "Unknown")
            # Truncate long titles in the modal list
            if len(title) > 36:
                title = title[:35] + "…"
            display_items.append(f"{badge} {title}  [dim]— {artist}[/dim]")

        yield Container(
            Vertical(
                Label(
                    f"[bold bright_cyan]◈  {self.modal_title}[/bold bright_cyan]",
                    id="modal_header",
                ),
                Rule(id="modal_rule"),
                OptionList(*display_items, id="selection_list"),
                Button("✕  Cancel", variant="warning", id="cancel_btn"),
            ),
            id="modal_container",
        )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Return the index of the selected option."""
        self.dismiss(event.option_index)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "cancel_btn":
            self.dismiss(-1)

    def action_dismiss_modal(self) -> None:
        self.dismiss(-1)
