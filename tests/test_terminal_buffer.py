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

    buffer.feed("hello")
    buffer.resize(10, 2)

    assert buffer.columns == 10
    assert buffer.rows == 2
    assert buffer.render_lines() == ["hello"]


def test_feed_bytes_decodes_text() -> None:
    buffer = TerminalBuffer(columns=20, rows=4)

    buffer.feed_bytes(b"h\xc3")
    buffer.feed_bytes(b"\xa9llo")

    assert buffer.render_lines() == ["h\u00e9llo"]
