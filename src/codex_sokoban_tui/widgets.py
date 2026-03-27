"""UI-facing widgets and small control helpers."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

from codex_sokoban_tui.focus import PaneFocus
from codex_sokoban_tui.sokoban import GameState

_MOVEMENT_KEYS: dict[str, str] = {
    "up": "up",
    "down": "down",
    "left": "left",
    "right": "right",
    "w": "up",
    "s": "down",
    "a": "left",
    "d": "right",
}


class TerminalInputTarget(Protocol):
    status: str

    def send_input(self, data: bytes) -> int:
        ...


@dataclass(frozen=True, slots=True)
class PaneRender:
    title: str
    lines: tuple[str, ...]
    focused: bool
    status: str


class CodexPaneWidget:
    def render(
        self,
        *,
        buffer_lines: Sequence[str],
        focused: bool,
        status: str,
    ) -> PaneRender:
        lines = tuple(buffer_lines) if buffer_lines else ("",)
        return PaneRender(
            title="Codex",
            lines=lines,
            focused=focused,
            status=status,
        )


class SokobanWidget:
    def render(self, *, game: GameState, focused: bool) -> PaneRender:
        return PaneRender(
            title="Sokoban",
            lines=tuple(_render_game_map(game)),
            focused=focused,
            status=f"Moves: {game.move_count} | Pushes: {game.push_count}",
        )


class StatusBarWidget:
    def render(
        self,
        *,
        focus: PaneFocus,
        game: GameState,
        terminal_status: str,
    ) -> str:
        return (
            f"Focus: {focus.name} | Moves: {game.move_count} | "
            f"Pushes: {game.push_count} | Codex: {terminal_status}"
        )


@dataclass(slots=True)
class InputRouter:
    game: GameState
    terminal_adapter: TerminalInputTarget
    focus: PaneFocus = PaneFocus.CODEX

    def handle_key(self, key: str) -> bool:
        normalized = key.lower()

        if normalized == "f6":
            self.focus = (
                PaneFocus.GAME
                if self.focus is PaneFocus.CODEX
                else PaneFocus.CODEX
            )
            return True

        if normalized == "ctrl+c" and self.focus is PaneFocus.CODEX:
            self.terminal_adapter.send_input(b"\x03")
            return True

        if self.focus is PaneFocus.CODEX:
            terminal_input = _translate_terminal_input(key)
            if terminal_input is None:
                return False
            self.terminal_adapter.send_input(terminal_input)
            return True

        direction = _MOVEMENT_KEYS.get(normalized)
        if direction is None or self.focus is not PaneFocus.GAME:
            return False

        self.game.move(direction)
        return True


def _translate_terminal_input(key: str) -> bytes | None:
    if len(key) == 1:
        return key.encode("utf-8")
    return None


def _render_game_map(game: GameState) -> list[str]:
    lines: list[str] = []
    for y in range(game.height):
        row: list[str] = []
        for x in range(game.row_lengths[y]):
            position = (x, y)
            if position in game.walls:
                row.append("#")
            elif position == game.player and position in game.goals:
                row.append("+")
            elif position == game.player:
                row.append("@")
            elif position in game.boxes and position in game.goals:
                row.append("*")
            elif position in game.boxes:
                row.append("$")
            elif position in game.goals:
                row.append(".")
            else:
                row.append(" ")
        lines.append("".join(row))
    return lines
