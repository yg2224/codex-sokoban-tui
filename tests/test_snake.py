from random import Random

from codex_sokoban_tui.snake import Direction, SnakeGame
from codex_sokoban_tui.snake_terminal import map_key_to_action, render_frame


def test_tick_moves_head_in_current_direction() -> None:
    game = SnakeGame(
        width=5,
        height=5,
        snake=((2, 2),),
        direction=Direction.RIGHT,
        rng=Random(0),
        initial_food=(0, 0),
    )

    game.tick()

    assert game.snake == ((3, 2),)


def test_tick_increases_score_and_length_when_eating_food() -> None:
    game = SnakeGame(
        width=5,
        height=5,
        snake=((2, 2),),
        direction=Direction.RIGHT,
        rng=Random(0),
        initial_food=(3, 2),
    )

    game.tick()

    assert game.snake == ((3, 2), (2, 2))
    assert game.score == 1
    assert game.food is not None
    assert game.food != (3, 2)
    assert game.food not in game.snake


def test_map_key_to_action_supports_arrow_keys_and_wasd() -> None:
    assert map_key_to_action("up") is Direction.UP
    assert map_key_to_action("down") is Direction.DOWN
    assert map_key_to_action("left") is Direction.LEFT
    assert map_key_to_action("right") is Direction.RIGHT
    assert map_key_to_action("\xe0h") is Direction.UP
    assert map_key_to_action("\xe0p") is Direction.DOWN
    assert map_key_to_action("\xe0k") is Direction.LEFT
    assert map_key_to_action("\xe0m") is Direction.RIGHT
    assert map_key_to_action("w") is Direction.UP
    assert map_key_to_action("a") is Direction.LEFT
    assert map_key_to_action("s") is Direction.DOWN
    assert map_key_to_action("d") is Direction.RIGHT
    assert map_key_to_action("r") == "restart"
    assert map_key_to_action("q") == "quit"


def test_render_frame_shows_small_terminal_warning() -> None:
    game = SnakeGame(
        width=5,
        height=5,
        snake=((2, 2),),
        direction=Direction.RIGHT,
        rng=Random(0),
        initial_food=(0, 0),
        score=2,
    )

    frame = render_frame(game, width=4, height=6)

    assert "too small" in frame.lower()
    assert "need at least" in frame.lower()


def test_render_frame_contains_score_and_border() -> None:
    game = SnakeGame(
        width=3,
        height=3,
        snake=((1, 1),),
        direction=Direction.RIGHT,
        rng=Random(0),
        initial_food=(0, 0),
        score=7,
        game_over=False,
    )

    frame = render_frame(game, width=10, height=10)
    lines = frame.splitlines()

    assert "Score: 7" in frame
    assert any(line.startswith("+") and line.endswith("+") for line in lines)
    assert any(line.startswith("|") and line.endswith("|") for line in lines)


def test_collision_with_wall_sets_game_over() -> None:
    game = SnakeGame(
        width=3,
        height=3,
        snake=((2, 1),),
        direction=Direction.RIGHT,
        rng=Random(0),
        initial_food=(0, 0),
    )

    game.tick()

    assert game.game_over is True
    assert game.snake == ((2, 1),)


def test_collision_with_self_sets_game_over() -> None:
    game = SnakeGame(
        width=5,
        height=5,
        snake=((2, 2), (3, 2), (3, 3)),
        direction=Direction.RIGHT,
        rng=Random(0),
        initial_food=(0, 0),
    )

    game.tick()

    assert game.game_over is True
    assert game.snake == ((2, 2), (3, 2), (3, 3))


def test_restart_restores_initial_state() -> None:
    game = SnakeGame(
        width=5,
        height=5,
        snake=((2, 2),),
        direction=Direction.UP,
        rng=Random(0),
        initial_food=(0, 4),
    )

    game.set_direction(Direction.RIGHT)
    game.tick()
    game.tick()
    game.restart()

    assert game.direction is Direction.UP
    assert game.snake == ((2, 2),)
    assert game.score == 0
    assert game.game_over is False
    assert game.food == (0, 4)


def test_reverse_direction_is_rejected_when_length_is_greater_than_one() -> None:
    game = SnakeGame(
        width=5,
        height=5,
        snake=((2, 2), (1, 2)),
        direction=Direction.RIGHT,
        rng=Random(0),
        initial_food=(0, 0),
    )

    accepted = game.set_direction(Direction.LEFT)

    assert accepted is False
    assert game.direction is Direction.RIGHT
    game.tick()
    assert game.snake == ((3, 2), (2, 2))
