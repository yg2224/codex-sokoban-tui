import tomllib
import shutil
from pathlib import Path
from unittest.mock import MagicMock

from codex_sokoban_tui import launcher
from codex_sokoban_tui.wt_command import build_wt_command


def _contains_subsequence(items: list[str], subsequence: list[str]) -> bool:
    """Check whether `items` contains `subsequence` as a contiguous segment."""
    if len(subsequence) == 0:
        return True

    for i in range(len(items) - len(subsequence) + 1):
        if items[i : i + len(subsequence)] == subsequence:
            return True
    return False


def test_check_requirements_requires_wt() -> None:
    original_which = shutil.which

    def fake_which(cmd: str) -> str | None:
        if cmd == "wt":
            return None
        return "/usr/bin/codex"

    shutil.which = fake_which
    try:
        assert launcher.check_requirements() == "Windows Terminal (wt) is required"
    finally:
        shutil.which = original_which


def test_check_requirements_requires_codex() -> None:
    original_which = shutil.which

    def fake_which(cmd: str) -> str | None:
        if cmd == "wt":
            return "/usr/bin/wt"
        if cmd == "codex":
            return None
        return None

    shutil.which = fake_which
    try:
        assert launcher.check_requirements() == "codex must be available on PATH"
    finally:
        shutil.which = original_which


def test_console_script_name_is_codex_snake() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as file:
        project_data = tomllib.load(file)

    scripts = project_data["project"]["scripts"]
    assert scripts["codex-snake"] == "codex_sokoban_tui.launcher:main"


def test_build_wt_command_left_and_right_panes() -> None:
    project_dir = Path("/tmp/project")
    command = build_wt_command(project_dir=project_dir, python_executable="python")

    assert command[0] == "wt"
    left_command_index = command.index("codex")
    split_pane_index = command.index("split-pane")
    assert left_command_index < split_pane_index
    assert _contains_subsequence(
        command,
        ["python", "-m", "codex_sokoban_tui.snake_terminal"],
    )


def test_launcher_main_calls_subprocess_run_with_wt_command() -> None:
    original_check_requirements = launcher.check_requirements
    original_build_wt_command = launcher.build_wt_command
    original_subprocess_run = launcher.subprocess.run

    expected_command = ["wt", "new-tab", "codex"]
    fake_result = MagicMock(returncode=0)
    captured = {}

    launcher.check_requirements = lambda: None
    launcher.build_wt_command = lambda *, project_dir, python_executable: expected_command
    launcher.subprocess.run = lambda command, check=False: captured.update(
        {"command": command}
    ) or fake_result

    try:
        assert launcher.main() is None
    finally:
        launcher.check_requirements = original_check_requirements
        launcher.build_wt_command = original_build_wt_command
        launcher.subprocess.run = original_subprocess_run

    assert captured["command"] == expected_command
