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
