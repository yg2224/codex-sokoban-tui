import tomllib
from pathlib import Path


def test_console_script_name_is_codex_snake() -> None:
    pyproject_path = Path(__file__).resolve().parents[1] / "pyproject.toml"
    with pyproject_path.open("rb") as file:
        project_data = tomllib.load(file)

    scripts = project_data["project"]["scripts"]
    assert scripts["codex-snake"] == "codex_sokoban_tui.launcher:main"
