import pytest

from codex_sokoban_tui.sokoban import GameState, MoveResult, load_builtin_level, load_level


def test_move_into_floor_updates_player_position() -> None:
    state = load_level([
        "#####",
        "#@ .#",
        "#####",
    ])

    result = state.move("right")

    assert result is MoveResult.MOVED
    assert state.player == (2, 1)
    assert state.move_count == 1


def test_move_into_wall_is_blocked() -> None:
    state = load_level([
        "#####",
        "#@ .#",
        "#####",
    ])

    result = state.move("left")

    assert result is MoveResult.BLOCKED
    assert state.player == (1, 1)
    assert state.move_count == 0
    assert state.push_count == 0


def test_push_box_into_free_space_moves_box_and_player() -> None:
    state = load_level([
        "######",
        "#@$. #",
        "######",
    ])

    result = state.move("right")

    assert result is MoveResult.PUSHED
    assert state.player == (2, 1)
    assert state.boxes == {(3, 1)}
    assert state.move_count == 1
    assert state.push_count == 1


def test_cannot_push_box_into_wall() -> None:
    state = load_level([
        "#####",
        "#@$##",
        "#####",
    ])

    result = state.move("right")

    assert result is MoveResult.BLOCKED
    assert state.player == (1, 1)
    assert state.boxes == {(2, 1)}
    assert state.move_count == 0
    assert state.push_count == 0


def test_cannot_push_box_into_another_box() -> None:
    state = load_level([
        "######",
        "#@$$.#",
        "######",
    ])

    result = state.move("right")

    assert result is MoveResult.BLOCKED
    assert state.player == (1, 1)
    assert state.boxes == {(2, 1), (3, 1)}
    assert state.move_count == 0
    assert state.push_count == 0


def test_level_is_complete_when_all_boxes_are_on_goals() -> None:
    state = load_level([
        "#####",
        "#@$.#",
        "#####",
    ])

    assert state.is_complete is False

    result = state.move("right")

    assert result is MoveResult.PUSHED
    assert state.boxes == {(3, 1)}
    assert state.is_complete is True


def test_restart_restores_initial_state() -> None:
    state = load_level([
        "#####",
        "#@$.#",
        "#####",
    ])

    state.move("right")
    state.restart()

    assert state.player == (1, 1)
    assert state.boxes == {(2, 1)}
    assert state.move_count == 0
    assert state.push_count == 0
    assert state.is_complete is False


def test_load_builtin_level_selects_requested_map() -> None:
    state = load_builtin_level(1)

    assert state.level_index == 1
    assert state.player == (1, 1)

    assert state.move("right") is MoveResult.MOVED
    assert state.move("right") is MoveResult.PUSHED
    assert state.is_complete is True


def test_plus_and_star_tiles_preserve_goal_semantics() -> None:
    state = load_level([
        "#####",
        "#+* #",
        "#####",
    ])

    assert state.player == (1, 1)
    assert state.boxes == {(2, 1)}
    assert state.goals == {(1, 1), (2, 1)}
    assert state.is_complete is True


def test_missing_cells_in_ragged_rows_are_not_walkable() -> None:
    state = load_level([
        "#####",
        "#@ ",
        "#####",
    ])

    assert state.move("right") is MoveResult.MOVED
    assert state.move("right") is MoveResult.BLOCKED
    assert state.player == (2, 1)
    assert state.move_count == 1


@pytest.mark.parametrize(
    ("lines",),
    [
        ([
            "#####",
            "#@@.#",
            "#####",
        ],),
        ([
            "#####",
            "#+@.#",
            "#####",
        ],),
    ],
)
def test_load_level_rejects_multiple_players(lines: list[str]) -> None:
    with pytest.raises(ValueError, match="exactly one player"):
        load_level(lines)
