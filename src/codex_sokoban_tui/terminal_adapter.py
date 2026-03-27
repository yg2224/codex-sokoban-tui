from __future__ import annotations

import codecs
import queue
import shutil
import threading
from collections.abc import Callable
from typing import Protocol

from winpty import PtyProcess

from codex_sokoban_tui.terminal_buffer import TerminalBuffer


class TerminalBackend(Protocol):
    def write(self, data: bytes) -> int:
        ...

    def read(self, size: int = 4096) -> bytes | str:
        ...

    def setwinsize(self, rows: int, columns: int) -> None:
        ...

    def terminate(self) -> bool | None:
        ...


BackendFactory = Callable[[list[str], int, int], TerminalBackend]


class _PtyBackend:
    def __init__(self, process: PtyProcess) -> None:
        self._process = process
        self._output_queue: queue.SimpleQueue[bytes | str] = queue.SimpleQueue()
        self._closed = threading.Event()
        self._reader = threading.Thread(target=self._read_forever, daemon=True)
        self._reader.start()

    @staticmethod
    def _decode_input_bytes(data: bytes) -> str:
        # pywinpty 的 PtyProcess.write() 只接收 str，无法真正透传原始 bytes。
        # 默认策略优先把合法 UTF-8 输入还原成文本；如果不是合法 UTF-8，
        # 再退回 latin-1 的 1:1 字节到码点映射，避免默认 backend 抛解码错误。
        try:
            return data.decode("utf-8")
        except UnicodeDecodeError:
            return data.decode("latin-1")

    def _read_forever(self) -> None:
        while not self._closed.is_set():
            try:
                chunk = self._process.read(4096)
            except (EOFError, OSError):
                break

            if chunk in ("", b""):
                break

            self._output_queue.put(chunk)

        self._closed.set()

    def write(self, data: bytes) -> int:
        self._process.write(self._decode_input_bytes(data))
        return len(data)

    def read(self, size: int = 4096) -> bytes | str:
        try:
            return self._output_queue.get_nowait()
        except queue.Empty:
            return b""

    def setwinsize(self, rows: int, columns: int) -> None:
        self._process.setwinsize(rows, columns)

    def terminate(self) -> bool | None:
        self._closed.set()
        try:
            return self._process.terminate()
        finally:
            self._reader.join(timeout=0.2)


def _spawn_pty_backend(command: list[str], columns: int, rows: int) -> TerminalBackend:
    return _PtyBackend(PtyProcess.spawn(command, dimensions=(rows, columns)))


class TerminalAdapter:
    def __init__(
        self,
        command: list[str],
        backend_factory: BackendFactory | None = None,
    ) -> None:
        self._command = command
        self._backend_factory = backend_factory or _spawn_pty_backend
        self._backend: TerminalBackend | None = None
        self._buffer: TerminalBuffer | None = None
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self.status = "idle"

    @property
    def buffer(self) -> TerminalBuffer:
        if self._buffer is None:
            raise RuntimeError("Terminal buffer is not initialized.")
        return self._buffer

    def render_lines(self) -> list[str]:
        if self._buffer is None:
            return []
        return self._buffer.render_lines()

    def start(self, columns: int, rows: int) -> bool:
        executable = self._command[0] if self._command else ""
        if not executable or shutil.which(executable) is None:
            self.status = f"Command not found: {executable}"
            return False

        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")
        self._buffer = TerminalBuffer(columns=columns, rows=rows)
        try:
            self._backend = self._backend_factory(self._command, columns, rows)
        except OSError as exc:
            self.status = str(exc)
            return False
        self.status = "running"
        return True

    def send_input(self, data: bytes) -> int:
        if self._backend is None:
            return 0
        return self._backend.write(data)

    def poll_output(self) -> str:
        if self._backend is None or self._buffer is None:
            return ""

        data = self._backend.read()
        if data in ("", b""):
            return ""

        if isinstance(data, bytes):
            text = self._decoder.decode(data)
        else:
            text = data

        if text:
            self._buffer.feed(text)
        return text

    def resize(self, columns: int, rows: int) -> None:
        if self._buffer is not None:
            self._buffer.resize(columns, rows)
        if self._backend is not None:
            self._backend.setwinsize(rows, columns)

    def terminate(self) -> None:
        if self._backend is not None:
            self._backend.terminate()
            self._backend = None
        self.status = "terminated"
