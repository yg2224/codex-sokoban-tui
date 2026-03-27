from __future__ import annotations

from dataclasses import dataclass

import pyte


@dataclass
class TerminalBuffer:
    columns: int
    rows: int

    def __post_init__(self) -> None:
        self._screen = pyte.Screen(self.columns, self.rows)
        self._stream = pyte.Stream(self._screen)

    def feed(self, data: str) -> None:
        self._stream.feed(data)

    def feed_bytes(self, data: bytes) -> None:
        self.feed(data.decode("utf-8", errors="replace"))

    def resize(self, columns: int, rows: int) -> None:
        self._screen.resize(rows, columns)
        self.columns = columns
        self.rows = rows

    def render_lines(self) -> list[str]:
        lines = [line.rstrip() for line in self._screen.display]
        while lines and not lines[-1]:
            lines.pop()
        return lines
