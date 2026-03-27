import builtins
import base64
import sys
import types
from pathlib import Path
from codex_sokoban_tui import launcher
from codex_sokoban_tui.wt_command import build_wt_command
import tomllib
import shutil
import main as entrypoint
from unittest.mock import MagicMock

import pytest


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

    encoded_script = command[-1]
    decoded_script = base64.b64decode(encoded_script).decode("utf-16-le")

    assert command[:-1] == [
        "wt",
        "new-tab",
        "-d",
        str(project_dir),
        "powershell.exe",
        "-NoExit",
        "-Command",
        "codex",
        ";",
        "split-pane",
        "-V",
        "-d",
        str(project_dir),
        "powershell.exe",
        "-NoExit",
        "-EncodedCommand",
    ]
    assert "$env:PYTHONPATH" in decoded_script
    assert str(project_dir / "src") in decoded_script
    assert "python -m codex_sokoban_tui.snake_terminal" in decoded_script


def test_launcher_main_uses_current_working_directory(monkeypatch: pytest.MonkeyPatch) -> None:
    captured = {}

    monkeypatch.setattr(launcher, "check_requirements", lambda: None)
    monkeypatch.setattr(launcher, "build_wt_command", lambda **kwargs: captured.update(kwargs) or ["wt"])
    monkeypatch.setattr(launcher.subprocess, "run", lambda command, check=False: MagicMock(returncode=0))

    launcher.main()

    assert captured["project_dir"] == Path.cwd().resolve()


def test_launcher_main_calls_subprocess_run_with_wt_command(monkeypatch: pytest.MonkeyPatch) -> None:
    expected_command = ["wt", "new-tab", "codex"]
    fake_result = MagicMock(returncode=0)
    captured = {}

    monkeypatch.setattr(launcher, "check_requirements", lambda: None)
    monkeypatch.setattr(
        launcher,
        "build_wt_command",
        lambda *, project_dir, python_executable: expected_command,
    )
    monkeypatch.setattr(
        launcher.subprocess,
        "run",
        lambda command, check=False: captured.update({"command": command}) or fake_result,
    )

    assert launcher.main() is None

    assert captured["command"] == expected_command


def test_main_entrypoint_delegates_to_launcher_not_hosted_app(monkeypatch: pytest.MonkeyPatch) -> None:
    launcher_called = {}

    fake_launcher = types.ModuleType("codex_sokoban_tui.launcher")
    fake_launcher.main = lambda: launcher_called.setdefault("called", True)
    monkeypatch.setitem(sys.modules, "codex_sokoban_tui.launcher", fake_launcher)

    original_import = builtins.__import__

    def guard_import(name: str, globals=None, locals=None, fromlist=(), level=0):
        if name == "codex_sokoban_tui.app" or name.startswith("codex_sokoban_tui.app"):
            raise AssertionError("legacy hosted Codex TUI entry point was used")
        return original_import(name, globals, locals, fromlist, level)

    monkeypatch.setattr(builtins, "__import__", guard_import)
    monkeypatch.setattr(entrypoint, "_ensure_repo_src_on_path", lambda: None)

    entrypoint.main()

    assert launcher_called.get("called") is True


def test_launcher_main_raises_when_requirement_check_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher, "check_requirements", lambda: "Windows Terminal (wt) is required")

    with pytest.raises(SystemExit, match="Windows Terminal \\(wt\\) is required"):
        launcher.main()


def test_launcher_main_raises_when_subprocess_run_fails(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher, "check_requirements", lambda: None)
    monkeypatch.setattr(launcher, "build_wt_command", lambda **kwargs: ["wt"])

    def raise_os_error(command: list[str], check: bool = False) -> MagicMock:
        raise OSError("boom")

    monkeypatch.setattr(launcher.subprocess, "run", raise_os_error)

    with pytest.raises(SystemExit, match="Failed to launch Windows Terminal:"):
        launcher.main()


def test_launcher_main_raises_when_wt_exits_nonzero(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(launcher, "check_requirements", lambda: None)
    monkeypatch.setattr(launcher, "build_wt_command", lambda **kwargs: ["wt"])
    monkeypatch.setattr(launcher.subprocess, "run", lambda command, check=False: MagicMock(returncode=3))

    with pytest.raises(SystemExit, match="exit code: 3"):
        launcher.main()
