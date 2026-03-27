from pathlib import Path
import sys


PROJECT_ROOT = Path(__file__).resolve().parent
SRC_DIR = PROJECT_ROOT / "src"
if SRC_DIR.exists():
    sys.path.insert(0, str(SRC_DIR))

from codex_sokoban_tui.app import CodexSokobanApp


if __name__ == "__main__":
    CodexSokobanApp().run()
