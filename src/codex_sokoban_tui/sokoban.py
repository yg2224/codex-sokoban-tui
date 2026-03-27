"""Pure Sokoban game engine."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Iterable

from codex_sokoban_tui.levels import BUILTIN_LEVELS

Position = tuple[int, int]

_DIRECTIONS: dict[str, tuple[int, int]] = {
    "up": (0, -1),
    "down": (0, 1),
    "left": (-1, 0),
    "right": (1, 0),
}


class MoveResult(str, Enum):
    BLOCKED = "blocked"
    MOVED = "moved"
    PUSHED = "pushed"


@dataclass(slots=True)
class GameState:
    width: int
    height: int
    row_lengths: tuple[int, ...]
    walls: frozenset[Position]
    goals: frozenset[Position]
    boxes: set[Position]
    player: Position
    _initial_boxes: frozenset[Position] = field(repr=False, compare=False)
    _initial_player: Position = field(repr=False, compare=False)
    level_index: int = -1
    move_count: int = 0
    push_count: int = 0

    @property
    def is_complete(self) -> bool:
        return self.boxes <= self.goals

    def move(self, direction: str) -> MoveResult:
        if direction not in _DIRECTIONS:
            raise ValueError(f"unknown direction: {direction}")

        dx, dy = _DIRECTIONS[direction]
        target = (self.player[0] + dx, self.player[1] + dy)

        if self._is_blocked(target):
            return MoveResult.BLOCKED

        if target in self.boxes:
            box_target = (target[0] + dx, target[1] + dy)
            if self._is_blocked(box_target) or box_target in self.boxes:
                return MoveResult.BLOCKED

            self.boxes.remove(target)
            self.boxes.add(box_target)
            self.player = target
            self.move_count += 1
            self.push_count += 1
            return MoveResult.PUSHED

        self.player = target
        self.move_count += 1
        return MoveResult.MOVED

    def restart(self) -> None:
        self.boxes = set(self._initial_boxes)
        self.player = self._initial_player
        self.move_count = 0
        self.push_count = 0

    def _is_blocked(self, position: Position) -> bool:
        x, y = position
        if x < 0 or y < 0 or y >= self.height:
            return True
        if x >= self.row_lengths[y]:
            return True
        return position in self.walls


def load_level(lines: Iterable[str]) -> GameState:
    grid = list(lines)
    if not grid:
        raise ValueError("level must contain at least one row")

    width = max(len(row) for row in grid)
    height = len(grid)
    row_lengths = tuple(len(row) for row in grid)
    walls: set[Position] = set()
    goals: set[Position] = set()
    boxes: set[Position] = set()
    player: Position | None = None
    player_count = 0

    for y, row in enumerate(grid):
        for x, tile in enumerate(row):
            if tile == "#":
                walls.add((x, y))
            elif tile == ".":
                goals.add((x, y))
            elif tile == "$":
                boxes.add((x, y))
            elif tile == "@":
                player_count += 1
                if player_count > 1:
                    raise ValueError("level must include exactly one player")
                player = (x, y)
            elif tile == "*":
                goals.add((x, y))
                boxes.add((x, y))
            elif tile == "+":
                player_count += 1
                if player_count > 1:
                    raise ValueError("level must include exactly one player")
                goals.add((x, y))
                player = (x, y)
            elif tile == " ":
                continue
            else:
                raise ValueError(f"unknown tile: {tile!r}")

    if player_count != 1 or player is None:
        raise ValueError("level must include exactly one player")

    return GameState(
        width=width,
        height=height,
        row_lengths=row_lengths,
        walls=frozenset(walls),
        goals=frozenset(goals),
        boxes=boxes,
        player=player,
        _initial_boxes=frozenset(boxes),
        _initial_player=player,
    )


def load_builtin_level(index: int) -> GameState:
    state = load_level(BUILTIN_LEVELS[index])
    state.level_index = index
    return state
