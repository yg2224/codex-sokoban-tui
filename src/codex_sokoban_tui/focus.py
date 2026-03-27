"""Focus primitives for the TUI."""

from __future__ import annotations

from enum import Enum


class PaneFocus(str, Enum):
    CODEX = "codex"
    GAME = "game"
