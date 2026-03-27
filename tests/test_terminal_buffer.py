import pytest

from codex_sokoban_tui.terminal_buffer import TerminalBuffer


def test_feed_plain_text_updates_visible_lines() -> None:
    buffer = TerminalBuffer(columns=20, rows=4)

    buffer.feed("hello\r\nworld")

    assert buffer.render_lines()[-2:] == ["hello", "world"]


def test_feed_ansi_cursor_movement_and_clear_updates_line() -> None:
    buffer = TerminalBuffer(columns=20, rows=4)

    buffer.feed("hello\x1b[2D\x1b[2K!")

    assert buffer.render_lines() == ["   !"]


def test_resize_changes_screen_dimensions() -> None:
    buffer = TerminalBuffer(columns=20, rows=4)

    buffer.resize(3, 2)
    buffer.feed("abcdef")

    assert buffer.columns == 3
    assert buffer.rows == 2
    assert buffer.render_lines() == ["abc", "def"]


def test_feed_bytes_decodes_text() -> None:
    buffer = TerminalBuffer(columns=20, rows=4)

    buffer.feed_bytes(b"h\xc3")
    buffer.feed_bytes(b"\xa9llo")

    assert buffer.render_lines() == ["h\u00e9llo"]


def test_render_lines_preserves_trailing_unicode_whitespace() -> None:
    buffer = TerminalBuffer(columns=20, rows=4)

    buffer.feed("hello\u00a0")

    assert buffer.render_lines() == ["hello\u00a0"]


def test_columns_and_rows_are_read_only() -> None:
    buffer = TerminalBuffer(columns=20, rows=4)

    with pytest.raises(AttributeError):
        buffer.columns = 10  # type: ignore[misc]

    with pytest.raises(AttributeError):
        buffer.rows = 2  # type: ignore[misc]
