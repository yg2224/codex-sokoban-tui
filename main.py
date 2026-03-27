from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"


def _ensure_repo_src_on_path() -> None:
    if SRC_DIR.exists():
        sys.path.insert(0, str(SRC_DIR))


def main() -> None:
    _ensure_repo_src_on_path()
    from codex_sokoban_tui.launcher import main as launcher_main

    launcher_main()


if __name__ == "__main__":
    main()
