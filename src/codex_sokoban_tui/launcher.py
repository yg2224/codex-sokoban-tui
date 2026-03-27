"""Launcher for running Codex and Snake in Windows Terminal."""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from codex_sokoban_tui.wt_command import build_wt_command


def check_requirements() -> str | None:
    """Validate required dependencies are available on PATH."""
    if shutil.which("wt") is None:
        return "Windows Terminal (wt) is required"
    if shutil.which("codex") is None:
        return "codex must be available on PATH"
    return None


def main() -> None:
    """Entry point for `codex-snake`."""
    requirement_error = check_requirements()
    if requirement_error is not None:
        raise SystemExit(requirement_error)

    project_dir = Path(__file__).resolve().parents[2]
    command = build_wt_command(
        project_dir=project_dir,
        python_executable=sys.executable,
    )

    try:
        completed = subprocess.run(command, check=False)
    except OSError as exc:
        raise SystemExit(f"Failed to launch Windows Terminal: {exc}") from exc

    if completed.returncode != 0:
        raise SystemExit(
            f"Failed to launch Windows Terminal command, exit code: {completed.returncode}"
        )
