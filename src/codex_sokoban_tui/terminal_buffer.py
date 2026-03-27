from __future__ import annotations

import codecs

import pyte


class TerminalBuffer:
    def __init__(self, columns: int, rows: int) -> None:
        self._screen = pyte.Screen(columns, rows)
        self._stream = pyte.Stream(self._screen)
        self._decoder = codecs.getincrementaldecoder("utf-8")(errors="replace")

    @property
    def columns(self) -> int:
        return self._screen.columns

    @property
    def rows(self) -> int:
        return self._screen.lines

    def feed(self, data: str) -> None:
        self._stream.feed(data)

    def feed_bytes(self, data: bytes) -> None:
        self.feed(self._decoder.decode(data))

    def resize(self, columns: int, rows: int) -> None:
        self._screen.resize(rows, columns)

    def render_lines(self) -> list[str]:
        lines = [line.rstrip(" ") for line in self._screen.display]
        while lines and not lines[-1]:
            lines.pop()
        return lines
