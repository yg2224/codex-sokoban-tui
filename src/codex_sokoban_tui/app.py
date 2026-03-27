from __future__ import annotations

from collections.abc import Callable

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static

from codex_sokoban_tui.sokoban import load_builtin_level
from codex_sokoban_tui.terminal_adapter import TerminalAdapter
from codex_sokoban_tui.widgets import (
    CodexPaneWidget,
    InputRouter,
    PaneRender,
    SokobanWidget,
    StatusBarWidget,
)


class _PaneStatic(Static):
    can_focus = True


AdapterFactory = Callable[[list[str]], object]


class CodexSokobanApp(App[None]):
    CSS = """
    Screen {
        layout: vertical;
    }

    #panes {
        height: 1fr;
        layout: horizontal;
    }

    #codex-pane, #sokoban-pane {
        width: 1fr;
    }

    #status-bar {
        height: auto;
    }
    """

    def __init__(
        self,
        *,
        command: list[str] | None = None,
        adapter_factory: AdapterFactory | None = None,
        poll_interval: float = 0.05,
    ) -> None:
        super().__init__()
        self._command = command or ["codex"]
        self._adapter_factory = adapter_factory or (lambda command: TerminalAdapter(command=command))
        self._poll_interval = poll_interval
        self._adapter = self._adapter_factory(self._command)
        self._game = load_builtin_level(0)
        self._router = InputRouter(
            game=self._game,
            terminal_adapter=self._adapter,
        )
        self._codex_widget = CodexPaneWidget()
        self._sokoban_widget = SokobanWidget()
        self._status_widget = StatusBarWidget()

    def compose(self) -> ComposeResult:
        with Horizontal(id="panes"):
            yield _PaneStatic(id="codex-pane")
            yield _PaneStatic(id="sokoban-pane")
        yield Static(id="status-bar")

    def on_mount(self) -> None:
        self.call_after_refresh(self._start_adapter)
        self.set_interval(self._poll_interval, self._poll_adapter)

    def on_unmount(self) -> None:
        self._adapter.terminate()

    def on_resize(self) -> None:
        columns, rows = self._codex_dimensions()
        self._adapter.resize(columns, rows)
        self._refresh_views()

    def on_key(self, event) -> None:
        if not self._router.handle_key(event.key):
            return

        if event.key == "f6":
            self._sync_focus()

        self._refresh_views()
        event.stop()

    def _start_adapter(self) -> None:
        columns, rows = self._codex_dimensions()
        self._adapter.start(columns, rows)
        self._sync_focus()
        self._refresh_views()

    def _poll_adapter(self) -> None:
        self._adapter.poll_output()
        self._refresh_views()

    def _codex_dimensions(self) -> tuple[int, int]:
        columns = max(1, self.size.width // 2)
        rows = max(1, self.size.height - 1)
        return columns, rows

    def _sync_focus(self) -> None:
        target_id = "#codex-pane" if self._router.focus.name == "CODEX" else "#sokoban-pane"
        self.query_one(target_id, _PaneStatic).focus()

    def _refresh_views(self) -> None:
        codex_view = self._codex_widget.render(
            buffer_lines=self._adapter.render_lines(),
            focused=self._router.focus.name == "CODEX",
            status=self._adapter.status,
        )
        self.query_one("#codex-pane", Static).update(self._render_pane(codex_view))

        sokoban_view = self._sokoban_widget.render(
            game=self._game,
            focused=self._router.focus.name == "GAME",
        )
        self.query_one("#sokoban-pane", Static).update(self._render_pane(sokoban_view))

        status_line = self._status_widget.render(
            focus=self._router.focus,
            game=self._game,
            terminal_status=self._adapter.status,
        )
        self.query_one("#status-bar", Static).update(status_line)

    @staticmethod
    def _render_pane(view: PaneRender) -> str:
        focus_label = "FOCUSED" if view.focused else "UNFOCUSED"
        header = f"{view.title} [{focus_label}] | {view.status}"
        body = "\n".join(view.lines)
        return f"{header}\n{body}" if body else header
