"""Build Windows Terminal command arguments for starting Codex and Snake."""

import base64
from pathlib import Path


def _encode_powershell_command(script: str) -> str:
    return base64.b64encode(script.encode("utf-16-le")).decode("ascii")


def build_wt_command(*, project_dir: Path, python_executable: str) -> list[str]:
    """Build a Windows Terminal command with split panes.

    Left pane runs native `codex`, right pane runs
    `python -m codex_sokoban_tui.snake_terminal`.
    """
    cwd = str(project_dir)
    src_dir = project_dir / "src"
    snake_script = f"$env:PYTHONPATH = '{src_dir}'\n{python_executable} -m codex_sokoban_tui.snake_terminal"
    snake_command = _encode_powershell_command(snake_script)
    return [
        "wt",
        "new-tab",
        "-d",
        cwd,
        "powershell.exe",
        "-NoExit",
        "-Command",
        "codex",
        ";",
        "split-pane",
        "-V",
        "-d",
        cwd,
        "powershell.exe",
        "-NoExit",
        "-EncodedCommand",
        snake_command,
    ]
