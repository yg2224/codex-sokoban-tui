from random import Random

from codex_sokoban_tui.snake import Direction, SnakeGame


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
