import threading
import time
from collections.abc import Callable

from codex_sokoban_tui.sokoban import load_level
from codex_sokoban_tui.terminal_adapter import TerminalAdapter, _PtyBackend


class FakeBackend:
    def __init__(self, reads: list[bytes | str] | None = None) -> None:
        self.reads = list(reads or [])
        self.writes: list[bytes] = []
        self.resizes: list[tuple[int, int]] = []
        self.terminated = False

    def write(self, data: bytes) -> int:
        self.writes.append(data)
        return len(data)

    def read(self, size: int = 4096) -> bytes | str:
        if self.reads:
            return self.reads.pop(0)
        return b""

    def setwinsize(self, rows: int, columns: int) -> None:
        self.resizes.append((rows, columns))

    def terminate(self) -> bool:
        self.terminated = True
        return True


class StrOnlyPtyProcess:
    def __init__(self) -> None:
        self.writes: list[str] = []

    def read(self, size: int = 4096) -> bytes:
        return b""

    def write(self, data: str) -> None:
        if not isinstance(data, str):
            raise TypeError("write() argument must be str, not bytes")
        self.writes.append(data)

    def setwinsize(self, rows: int, columns: int) -> None:
        return None

    def terminate(self) -> bool:
        return True


class QueueDrivenPtyProcess:
    def __init__(self, reads: list[bytes | str]) -> None:
        self._reads = list(reads)
        self.read_calls = 0

    def read(self, size: int = 4096) -> bytes | str:
        self.read_calls += 1
        if self._reads:
            return self._reads.pop(0)
        return b""

    def write(self, data: str) -> None:
        return None

    def setwinsize(self, rows: int, columns: int) -> None:
        return None

    def terminate(self) -> bool:
        return True


class BlockingPtyProcess:
    def __init__(self) -> None:
        self.read_started = threading.Event()
        self.release_read = threading.Event()
        self.terminated = False

    def read(self, size: int = 4096) -> bytes:
        self.read_started.set()
        self.release_read.wait(timeout=1.0)
        return b""

    def write(self, data: str) -> None:
        return None

    def setwinsize(self, rows: int, columns: int) -> None:
        return None

    def terminate(self) -> bool:
        self.terminated = True
        self.release_read.set()
        return True


def wait_for(predicate: Callable[[], bool], timeout: float = 1.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(0.01)
    raise AssertionError("condition not met before timeout")


class RecordingTerminalAdapter:
    def __init__(self) -> None:
        self.inputs: list[bytes] = []
        self.status = "running"

    def send_input(self, data: bytes) -> int:
        self.inputs.append(data)
        return len(data)


def make_test_game():
    return load_level(
        [
            "#####",
            "#@$.#",
            "#####",
        ]
    )


def test_adapter_reports_missing_codex_binary() -> None:
    adapter = TerminalAdapter(command=["__missing_codex__"])

    started = adapter.start(columns=80, rows=24)

    assert started is False
    assert "not found" in adapter.status.lower()


def test_adapter_forwards_input_to_backend() -> None:
    backend = FakeBackend()
    adapter = TerminalAdapter(
        command=["python"],
        backend_factory=lambda command, columns, rows: backend,
    )

    assert adapter.start(columns=80, rows=24) is True

    adapter.send_input(b"\x1b[A")

    assert backend.writes == [b"\x1b[A"]


def test_default_pty_backend_converts_input_bytes_for_str_only_process() -> None:
    process = StrOnlyPtyProcess()
    backend = _PtyBackend(process)

    written = backend.write(b"\x1b[A")
    backend.terminate()

    assert written == 3
    assert process.writes == ["\x1b[A"]


def test_default_pty_backend_decodes_utf8_input_before_writing() -> None:
    process = StrOnlyPtyProcess()
    backend = _PtyBackend(process)

    written = backend.write("h\u00e9".encode("utf-8"))
    backend.terminate()

    assert written == 3
    assert process.writes == ["h\u00e9"]


def test_default_pty_backend_preserves_non_utf8_bytes_without_decode_error() -> None:
    process = StrOnlyPtyProcess()
    backend = _PtyBackend(process)

    written = backend.write(b"\xff\x80")
    backend.terminate()

    assert written == 2
    assert process.writes == ["\xff\x80"]


def test_pty_backend_reader_thread_queues_output_and_stops_on_eof() -> None:
    process = QueueDrivenPtyProcess(reads=[b"hello", b""])
    backend = _PtyBackend(process)

    wait_for(lambda: backend.read() == b"hello")
    wait_for(lambda: not backend._reader.is_alive())

    assert process.read_calls >= 2
    assert backend.read() == b""


def test_pty_backend_terminate_unblocks_reader_and_joins_thread() -> None:
    process = BlockingPtyProcess()
    backend = _PtyBackend(process)

    assert process.read_started.wait(timeout=1.0) is True

    backend.terminate()

    assert process.terminated is True
    assert backend._reader.is_alive() is False


def test_adapter_forwards_resize_to_backend() -> None:
    backend = FakeBackend()
    adapter = TerminalAdapter(
        command=["python"],
        backend_factory=lambda command, columns, rows: backend,
    )

    assert adapter.start(columns=80, rows=24) is True

    adapter.resize(columns=100, rows=30)

    assert backend.resizes == [(30, 100)]


def test_adapter_polls_output_into_terminal_buffer() -> None:
    backend = FakeBackend(reads=[b"h\xc3", b"\xa9llo\r\nworld"])
    adapter = TerminalAdapter(
        command=["python"],
        backend_factory=lambda command, columns, rows: backend,
    )

    assert adapter.start(columns=20, rows=4) is True

    assert adapter.poll_output() == "h"
    assert adapter.poll_output() == "\u00e9llo\r\nworld"
    assert adapter.buffer.render_lines()[-2:] == ["h\u00e9llo", "world"]


def test_adapter_terminates_backend() -> None:
    backend = FakeBackend()
    adapter = TerminalAdapter(
        command=["python"],
        backend_factory=lambda command, columns, rows: backend,
    )

    assert adapter.start(columns=80, rows=24) is True

    adapter.terminate()

    assert backend.terminated is True
    assert adapter.status == "terminated"


def test_focus_router_toggles_between_codex_and_game_with_f6() -> None:
    from codex_sokoban_tui.focus import PaneFocus
    from codex_sokoban_tui.widgets import InputRouter

    router = InputRouter(
        game=make_test_game(),
        terminal_adapter=RecordingTerminalAdapter(),
    )

    assert router.focus is PaneFocus.CODEX
    assert router.handle_key("f6") is True
    assert router.focus is PaneFocus.GAME
    assert router.handle_key("f6") is True
    assert router.focus is PaneFocus.CODEX


def test_game_keys_do_not_move_player_when_game_is_unfocused() -> None:
    from codex_sokoban_tui.focus import PaneFocus
    from codex_sokoban_tui.widgets import InputRouter

    game = make_test_game()
    starting_player = game.player
    router = InputRouter(
        game=game,
        terminal_adapter=RecordingTerminalAdapter(),
        focus=PaneFocus.CODEX,
    )

    assert router.handle_key("right") is False
    assert game.player == starting_player
    assert game.move_count == 0


def test_game_keys_move_player_when_game_is_focused() -> None:
    from codex_sokoban_tui.focus import PaneFocus
    from codex_sokoban_tui.widgets import InputRouter

    game = make_test_game()
    router = InputRouter(
        game=game,
        terminal_adapter=RecordingTerminalAdapter(),
        focus=PaneFocus.GAME,
    )

    assert router.handle_key("right") is True
    assert game.player == (2, 1)
    assert game.boxes == {(3, 1)}
    assert game.move_count == 1
    assert game.push_count == 1


def test_ctrl_c_is_forwarded_to_terminal_when_codex_is_focused() -> None:
    from codex_sokoban_tui.focus import PaneFocus
    from codex_sokoban_tui.widgets import InputRouter

    adapter = RecordingTerminalAdapter()
    router = InputRouter(
        game=make_test_game(),
        terminal_adapter=adapter,
        focus=PaneFocus.CODEX,
    )

    assert router.handle_key("ctrl+c") is True
    assert adapter.inputs == [b"\x03"]


def test_plain_input_is_forwarded_to_terminal_when_codex_is_focused() -> None:
    from codex_sokoban_tui.focus import PaneFocus
    from codex_sokoban_tui.widgets import InputRouter

    adapter = RecordingTerminalAdapter()
    game = make_test_game()
    starting_player = game.player
    router = InputRouter(
        game=game,
        terminal_adapter=adapter,
        focus=PaneFocus.CODEX,
    )

    assert router.handle_key("x") is True
    assert adapter.inputs == [b"x"]
    assert game.player == starting_player
    assert game.move_count == 0


def test_wasd_keys_move_player_when_game_is_focused() -> None:
    from codex_sokoban_tui.focus import PaneFocus
    from codex_sokoban_tui.widgets import InputRouter

    game = make_test_game()
    router = InputRouter(
        game=game,
        terminal_adapter=RecordingTerminalAdapter(),
        focus=PaneFocus.GAME,
    )

    assert router.handle_key("d") is True
    assert game.player == (2, 1)
    assert game.boxes == {(3, 1)}
    assert game.move_count == 1
    assert game.push_count == 1


def test_widget_rendering_exposes_focus_and_status_for_shell_consumption() -> None:
    from codex_sokoban_tui.focus import PaneFocus
    from codex_sokoban_tui.widgets import (
        CodexPaneWidget,
        SokobanWidget,
        StatusBarWidget,
    )

    codex_view = CodexPaneWidget().render(
        buffer_lines=["$ help"],
        focused=False,
        status="running",
    )
    assert codex_view.title == "Codex"
    assert codex_view.focused is False
    assert codex_view.lines == ("$ help",)
    assert codex_view.status == "running"

    game_view = SokobanWidget().render(game=make_test_game(), focused=True)
    assert game_view.title == "Sokoban"
    assert game_view.focused is True
    assert game_view.lines == ("#####", "#@$.#", "#####")
    assert game_view.status == "Moves: 0 | Pushes: 0"

    game = make_test_game()
    game.move("right")
    status_line = StatusBarWidget().render(
        focus=PaneFocus.GAME,
        game=game,
        terminal_status="running",
    )
    assert status_line == "Focus: GAME | Moves: 1 | Pushes: 1 | Codex: running"
