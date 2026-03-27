"""Build Windows Terminal command arguments for starting Codex and Snake."""

from pathlib import Path


def build_wt_command(*, project_dir: Path, python_executable: str) -> list[str]:
    """Build a Windows Terminal command with split panes.

    Left pane runs native `codex`, right pane runs
    `python -m codex_sokoban_tui.snake_terminal`.
    """
    cwd = str(project_dir)
    src_dir = project_dir / "src"
    snake_command = f"$env:PYTHONPATH = '{src_dir}'; {python_executable} -m codex_sokoban_tui.snake_terminal"
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
        "-Command",
        snake_command,
    ]
