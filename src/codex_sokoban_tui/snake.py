"""纯贪吃蛇引擎（终端无关）。"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from random import Random


Cell = tuple[int, int]


class Direction(Enum):
    """蛇移动方向。"""

    RIGHT = (1, 0)
    DOWN = (0, 1)
    LEFT = (-1, 0)
    UP = (0, -1)

    @property
    def delta(self) -> Cell:
        """返回单步位移。"""

        return self.value

    @property
    def opposite(self) -> "Direction":
        """返回反向。"""

        return {
            Direction.RIGHT: Direction.LEFT,
            Direction.LEFT: Direction.RIGHT,
            Direction.UP: Direction.DOWN,
            Direction.DOWN: Direction.UP,
        }[self]


@dataclass
class _Snapshot:
    snake: tuple[Cell, ...]
    direction: Direction
    score: int
    food: Cell | None
    game_over: bool


class SnakeGame:
    """纯引擎状态与规则。"""

    def __init__(
        self,
        *,
        width: int,
        height: int,
        snake: tuple[Cell, ...],
        direction: Direction,
        rng: Random | None = None,
        initial_food: Cell | None = None,
        score: int = 0,
        game_over: bool = False,
    ) -> None:
        if width <= 0 or height <= 0:
            raise ValueError("width and height must be positive")
        if not snake:
            raise ValueError("snake must have at least one segment")

        self.width = width
        self.height = height
        self.snake = tuple(snake)
        self.direction = direction
        self._rng = rng if rng is not None else Random()
        self._initial_rng_state = self._rng.getstate()
        self.score = score
        self.game_over = game_over
        self.initial_food: Cell | None = initial_food

        if initial_food is not None:
            self._validate_food(initial_food)
            self.food = initial_food
        else:
            self.food = self._spawn_food()

        self._initial_snapshot = _Snapshot(
            snake=self.snake,
            direction=self.direction,
            score=self.score,
            food=self.food,
            game_over=self.game_over,
        )

    def set_direction(self, direction: Direction) -> bool:
        """尝试更新方向。

        蛇身长度大于 1 时，不允许 180° 原地掉头。
        """

        if len(self.snake) > 1 and direction is self.direction.opposite:
            return False
        self.direction = direction
        return True

    def tick(self) -> None:
        """推进一格。"""
        if self.game_over:
            return

        dx, dy = self.direction.delta
        new_head = (self.snake[0][0] + dx, self.snake[0][1] + dy)

        if self._is_wall(new_head):
            self.game_over = True
            return

        if self._is_self_collision(new_head):
            self.game_over = True
            return

        if new_head == self.food:
            self.snake = (new_head, *self.snake)
            self.score += 1
            self.food = self._spawn_food()
            return

        self.snake = (new_head, *self.snake[:-1])

    def restart(self) -> None:
        """恢复初始状态。"""
        self.snake = self._initial_snapshot.snake
        self.direction = self._initial_snapshot.direction
        self.score = self._initial_snapshot.score
        self.game_over = self._initial_snapshot.game_over

        self._rng.setstate(self._initial_rng_state)

        if self.initial_food is not None:
            self.food = self.initial_food
        else:
            self.food = self._spawn_food()

    def _spawn_food(self) -> Cell | None:
        """在空格子中随机选一个，若无空位则返回 ``None``。"""
        empty_cells = [cell for cell in self._iter_cells() if cell not in set(self.snake)]
        if not empty_cells:
            return None
        index = self._rng.randrange(len(empty_cells))
        return empty_cells[index]

    def _is_wall(self, cell: Cell) -> bool:
        x, y = cell
        return not (0 <= x < self.width and 0 <= y < self.height)

    def _is_self_collision(self, next_head: Cell) -> bool:
        if self.food is not None and next_head == self.food:
            return next_head in set(self.snake)

        # 非进食时尾巴会移动，因此撞到当前尾部不是碰撞。
        return next_head in set(self.snake[:-1]) or (len(self.snake) == 1 and next_head in self.snake)

    def _iter_cells(self) -> list[Cell]:
        return [(x, y) for y in range(self.height) for x in range(self.width)]

    def _validate_food(self, cell: Cell) -> None:
        if self._is_wall(cell):
            raise ValueError("food must be inside the board")
        if cell in set(self.snake):
            raise ValueError("food must not be on snake")
