import threading
import time
from collections.abc import Callable

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
