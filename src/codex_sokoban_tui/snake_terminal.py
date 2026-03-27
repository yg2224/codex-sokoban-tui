"""Terminal runner helpers for the snake game."""

from __future__ import annotations

import os
import shutil
import time
from typing import Literal

try:
    import msvcrt  # type: ignore
except Exception:  # pragma: no cover - non-Windows environment
    msvcrt = None

from codex_sokoban_tui.snake import Direction, SnakeGame


Action = Direction | Literal["restart", "quit"] | None

_SPECIAL_ARROWS = {
    "h": Direction.UP,
    "p": Direction.DOWN,
    "k": Direction.LEFT,
    "m": Direction.RIGHT,
}

_KEY_TO_ACTION = {
    "w": Direction.UP,
    "up": Direction.UP,
    "arrow_up": Direction.UP,
    "s": Direction.DOWN,
    "down": Direction.DOWN,
    "arrow_down": Direction.DOWN,
    "a": Direction.LEFT,
    "left": Direction.LEFT,
    "arrow_left": Direction.LEFT,
    "d": Direction.RIGHT,
    "right": Direction.RIGHT,
    "arrow_right": Direction.RIGHT,
    "r": "restart",
    "q": "quit",
}


def map_key_to_action(key: str) -> Action:
    """Map a terminal key input to a snake action."""
    if not isinstance(key, str) or not key:
        return None

    normalised = key.strip().lower()
    if len(normalised) == 2 and normalised[0] in {"\x00", "\xe0"}:
        normalised = normalised[1]
    if normalised in _SPECIAL_ARROWS:
        return _SPECIAL_ARROWS[normalised]
    if normalised in _KEY_TO_ACTION:
        return _KEY_TO_ACTION[normalised]
    return None


def _required_frame_size(game: SnakeGame) -> tuple[int, int]:
    score_line = f"Score: {game.score}"
    required_width = max(game.width + 2, len(score_line))
    required_height = game.height + 3
    return required_width, required_height


def render_frame(game: SnakeGame, width: int, height: int) -> str:
    """Render one frame of the game into a terminal-friendly string."""
    required_width, required_height = _required_frame_size(game)
    if width < required_width or height < required_height:
        return (
            "Terminal too small. "
            f"Need at least {required_width}x{required_height}, "
            f"got {width}x{height}."
        )

    snake_cells = set(game.snake)
    food = game.food
    board_width = game.width
    board_height = game.height

    score_line = f"Score: {game.score}"
    if game.game_over:
        score_line = f"{score_line} | GAME OVER"
    if len(score_line) < width:
        score_line = score_line.ljust(width)
    elif len(score_line) > width:
        score_line = score_line[:width]

    border = "+" + ("-" * board_width) + "+"

    lines: list[str] = [score_line]
    lines.append(border)
    head = game.snake[0] if game.snake else None
    for y in range(board_height):
        row = []
        for x in range(board_width):
            cell = (x, y)
            if cell == head:
                row.append("@")
            elif cell in snake_cells:
                row.append("O")
            elif cell == food:
                row.append("*")
            else:
                row.append(" ")
        lines.append("|" + "".join(row) + "|")
    lines.append(border)

    return "\n".join(lines)


def _read_key() -> str | None:
    if msvcrt is None:
        return None
    if not msvcrt.kbhit():
        return None

    first = msvcrt.getwch()
    if first in {"\x00", "\xe0"}:
        second = msvcrt.getwch()
        return f"{first}{second}"
    return first


def _paint(lines: str) -> None:
    os.system("cls" if os.name == "nt" else "clear")
    print(lines)


def _game_loop_tick(game: SnakeGame) -> bool:
    key = _read_key()
    if key is None:
        return True
    action = map_key_to_action(key)
    if action == "quit":
        return False
    if action == "restart":
        game.restart()
    elif isinstance(action, Direction):
        game.set_direction(action)
    game.tick()
    return True


def main() -> None:
    game = SnakeGame(
        width=20,
        height=10,
        snake=((10, 5),),
        direction=Direction.RIGHT,
        initial_food=(3, 3),
    )

    while True:
        columns, rows = shutil.get_terminal_size(fallback=(80, 24))
        frame = render_frame(game, width=columns, height=rows)
        _paint(frame)

        if not _game_loop_tick(game):
            break

        if "terminal too small" in frame.lower():
            time.sleep(0.25)
            continue

        if not game.game_over:
            time.sleep(0.1)
        else:
            time.sleep(0.05)
