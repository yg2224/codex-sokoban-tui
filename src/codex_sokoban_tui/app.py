from __future__ import annotations

from collections.abc import Callable

from textual.app import App, ComposeResult
from textual.containers import Horizontal
from textual.css.query import NoMatches
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
        self._poll_timer = None
        self._active = False
        self._last_codex_dimensions = (0, 0)

    def compose(self) -> ComposeResult:
        with Horizontal(id="panes"):
            yield _PaneStatic(id="codex-pane")
            yield _PaneStatic(id="sokoban-pane")
        yield Static(id="status-bar")

    def on_mount(self) -> None:
        self._active = True
        self.call_after_refresh(self._start_adapter)
        self._poll_timer = self.set_interval(self._poll_interval, self._poll_adapter)

    def on_unmount(self) -> None:
        self._active = False
        if self._poll_timer is not None:
            self._poll_timer.stop()
        self._adapter.terminate()

    def on_resize(self, event) -> None:
        if not self._active:
            return
        self._sync_adapter_size()
        self._refresh_views()

    def on_key(self, event) -> None:
        if not self._router.handle_key(event.key):
            return

        if event.key == "f6":
            self._sync_focus()

        self._refresh_views()
        event.stop()

    def _start_adapter(self) -> None:
        if not self._active:
            return
        columns, rows = self._codex_dimensions()
        self._adapter.start(columns, rows)
        self._last_codex_dimensions = (columns, rows)
        self._sync_focus()
        self._refresh_views()

    def _poll_adapter(self) -> None:
        if not self._active:
            return
        self._sync_adapter_size()
        self._adapter.poll_output()
        self._refresh_views()

    def _codex_dimensions(self) -> tuple[int, int]:
        try:
            codex_pane = self.query_one("#codex-pane", Static)
            columns = max(1, codex_pane.size.width)
            rows = max(1, codex_pane.size.height - 1)
        except NoMatches:
            columns = max(1, self.size.width // 2)
            rows = max(1, self.size.height - 2)
        return columns, rows

    def _sync_focus(self) -> None:
        if not self._active:
            return
        target_id = "#codex-pane" if self._router.focus.name == "CODEX" else "#sokoban-pane"
        try:
            self.query_one(target_id, _PaneStatic).focus()
        except NoMatches:
            return

    def _sync_adapter_size(self) -> None:
        dimensions = self._codex_dimensions()
        if dimensions == self._last_codex_dimensions:
            return
        self._adapter.resize(*dimensions)
        self._last_codex_dimensions = dimensions

    def _refresh_views(self) -> None:
        if not self._active:
            return
        try:
            codex_pane = self.query_one("#codex-pane", Static)
            sokoban_pane = self.query_one("#sokoban-pane", Static)
            status_bar = self.query_one("#status-bar", Static)
        except NoMatches:
            return

        codex_view = self._codex_widget.render(
            buffer_lines=self._adapter.render_lines(),
            focused=self._router.focus.name == "CODEX",
            status=self._adapter.status,
        )
        codex_pane.update(self._render_pane(codex_view))

        sokoban_view = self._sokoban_widget.render(
            game=self._game,
            focused=self._router.focus.name == "GAME",
        )
        sokoban_pane.update(self._render_pane(sokoban_view))

        status_line = self._status_widget.render(
            focus=self._router.focus,
            game=self._game,
            terminal_status=self._adapter.status,
        )
        status_bar.update(status_line)

    @staticmethod
    def _render_pane(view: PaneRender) -> str:
        focus_label = "FOCUSED" if view.focused else "UNFOCUSED"
        header = f"{view.title} [{focus_label}] | {view.status}"
        body = "\n".join(view.lines)
        return f"{header}\n{body}" if body else header
