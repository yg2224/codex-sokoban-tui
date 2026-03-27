# Codex Sokoban TUI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a Python terminal app that launches a real `codex` session on the left and a playable Sokoban game on the right inside one terminal window.

**Architecture:** Use `Textual` as the outer TUI shell, a pure Sokoban engine for game rules, and a Windows PTY-backed adapter to host the `codex` child process. Render the PTY output through a terminal-emulation layer so the left pane behaves like a real interactive terminal while the right pane remains a focused game surface.

**Tech Stack:** Python 3.12, `Textual`, `pyte`, `pywinpty`, `pytest`, `pytest-asyncio`

---

## Planned File Structure

- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `main.py`
- Create: `src/codex_sokoban_tui/__init__.py`
- Create: `src/codex_sokoban_tui/app.py`
- Create: `src/codex_sokoban_tui/focus.py`
- Create: `src/codex_sokoban_tui/levels.py`
- Create: `src/codex_sokoban_tui/sokoban.py`
- Create: `src/codex_sokoban_tui/terminal_adapter.py`
- Create: `src/codex_sokoban_tui/terminal_buffer.py`
- Create: `src/codex_sokoban_tui/widgets.py`
- Create: `tests/test_sokoban.py`
- Create: `tests/test_terminal_buffer.py`
- Create: `tests/test_app.py`

## Task 1: Initialize Repository And Python Project

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `README.md`
- Create: `src/codex_sokoban_tui/__init__.py`

- [ ] **Step 1: Initialize the local git repository and bind the remote**

Run:

```bash
git init
git branch -M main
git remote add origin https://github.com/yg2224/codex-sokoban-tui.git
git remote -v
```

Expected: `origin` appears for fetch and push, pointing to `https://github.com/yg2224/codex-sokoban-tui.git`

- [ ] **Step 2: Add project metadata and dependencies**

Write `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools>=68", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "codex-sokoban-tui"
version = "0.1.0"
description = "Single-terminal Textual app with Codex on the left and Sokoban on the right"
requires-python = ">=3.12"
dependencies = [
  "textual>=2.1.2,<3",
  "pyte>=0.8.2,<1",
  "pywinpty>=2.0.15,<3; platform_system == 'Windows'",
]

[project.optional-dependencies]
dev = [
  "pytest>=8.3,<9",
  "pytest-asyncio>=0.25,<1",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"

[tool.setuptools.packages.find]
where = ["src"]
```

- [ ] **Step 3: Add ignore rules**

Write `.gitignore`:

```gitignore
__pycache__/
.pytest_cache/
.venv/
*.pyc
dist/
build/
*.egg-info/
```

- [ ] **Step 4: Add a minimal README with the intended startup command**

Write `README.md`:

````md
# codex-sokoban-tui

Run a split terminal app with `codex` on the left and Sokoban on the right.

## Development

```bash
python -m pip install -e .[dev]
python main.py
pytest -q
```
````

- [ ] **Step 5: Commit the bootstrap**

Run:

```bash
git add pyproject.toml .gitignore README.md src/codex_sokoban_tui/__init__.py
git commit -m "chore: 初始化 Python 项目骨架"
```

Expected: 1 bootstrap commit on `main`

## Task 2: Build The Pure Sokoban Engine With TDD

**Files:**
- Create: `src/codex_sokoban_tui/levels.py`
- Create: `src/codex_sokoban_tui/sokoban.py`
- Test: `tests/test_sokoban.py`

- [ ] **Step 1: Write the first failing test for simple movement into empty floor**

Write `tests/test_sokoban.py`:

```python
from codex_sokoban_tui.sokoban import GameState, MoveResult, load_level


def test_move_into_floor_updates_player_position() -> None:
    state = load_level(
        [
            "#####",
            "#@ .#",
            "#####",
        ]
    )

    result = state.move("right")

    assert result is MoveResult.MOVED
    assert state.player == (2, 1)
    assert state.move_count == 1
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
pytest tests/test_sokoban.py::test_move_into_floor_updates_player_position -v
```

Expected: FAIL because `GameState`, `MoveResult`, or `load_level` do not exist yet

- [ ] **Step 3: Write the minimal engine implementation to pass the test**

Implement the minimum API in `src/codex_sokoban_tui/sokoban.py`:

```python
from dataclasses import dataclass
from enum import Enum


class MoveResult(str, Enum):
    BLOCKED = "blocked"
    MOVED = "moved"
    PUSHED = "pushed"


@dataclass
class GameState:
    player: tuple[int, int]
    move_count: int = 0

    def move(self, direction: str) -> MoveResult:
        offsets = {"right": (1, 0)}
        dx, dy = offsets[direction]
        x, y = self.player
        self.player = (x + dx, y + dy)
        self.move_count += 1
        return MoveResult.MOVED
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
pytest tests/test_sokoban.py::test_move_into_floor_updates_player_position -v
```

Expected: PASS

- [ ] **Step 5: Add failing tests for walls, pushing, invalid pushes, win detection, restart, and level switching**

Add tests shaped like:

```python
def test_move_into_wall_is_blocked() -> None: ...
def test_push_box_into_floor_moves_box_and_player() -> None: ...
def test_cannot_push_box_into_wall() -> None: ...
def test_level_is_complete_when_all_boxes_on_targets() -> None: ...
def test_restart_restores_initial_state() -> None: ...
def test_select_level_loads_requested_map() -> None: ...
```

- [ ] **Step 6: Run the full Sokoban test file and confirm the new cases fail for the right reasons**

Run:

```bash
pytest tests/test_sokoban.py -v
```

Expected: the new assertions fail because the engine lacks map state and box logic

- [ ] **Step 7: Implement the minimal complete Sokoban engine**

Create focused units:

- `levels.py` stores a small built-in list of ASCII levels.
- `sokoban.py` owns:
  - tile parsing
  - player and box coordinates
  - target coordinates
  - `move()`
  - `restart()`
  - `load_builtin_level(index)`
  - `is_complete`

Core implementation shape:

```python
@dataclass
class Snapshot:
    walls: frozenset[tuple[int, int]]
    goals: frozenset[tuple[int, int]]
    boxes: set[tuple[int, int]]
    player: tuple[int, int]


@dataclass
class GameState:
    snapshot: Snapshot
    initial_snapshot: Snapshot
    level_index: int
    move_count: int = 0
    push_count: int = 0

    @property
    def is_complete(self) -> bool:
        return self.snapshot.boxes == set(self.snapshot.goals)
```

- [ ] **Step 8: Run the full Sokoban test file and verify all tests pass**

Run:

```bash
pytest tests/test_sokoban.py -v
```

Expected: PASS

- [ ] **Step 9: Commit the game engine**

Run:

```bash
git add src/codex_sokoban_tui/levels.py src/codex_sokoban_tui/sokoban.py tests/test_sokoban.py
git commit -m "feat: 实现推箱子核心规则"
```

## Task 3: Build The Terminal Buffer For Hosted Codex Output

**Files:**
- Create: `src/codex_sokoban_tui/terminal_buffer.py`
- Test: `tests/test_terminal_buffer.py`

- [ ] **Step 1: Write the first failing test for plain text rendering**

Write `tests/test_terminal_buffer.py`:

```python
from codex_sokoban_tui.terminal_buffer import TerminalBuffer


def test_feed_plain_text_updates_visible_lines() -> None:
    buffer = TerminalBuffer(columns=20, rows=4)

    buffer.feed("hello\r\nworld")

    assert buffer.render_lines()[-2:] == ["hello", "world"]
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
pytest tests/test_terminal_buffer.py::test_feed_plain_text_updates_visible_lines -v
```

Expected: FAIL because `TerminalBuffer` does not exist yet

- [ ] **Step 3: Implement the minimal terminal buffer**

Use `pyte` in `src/codex_sokoban_tui/terminal_buffer.py`:

```python
import pyte


class TerminalBuffer:
    def __init__(self, columns: int, rows: int) -> None:
        self._screen = pyte.Screen(columns, rows)
        self._stream = pyte.Stream(self._screen)

    def feed(self, data: str) -> None:
        self._stream.feed(data)

    def resize(self, columns: int, rows: int) -> None:
        self._screen.resize(rows, columns)

    def render_lines(self) -> list[str]:
        return [self._screen.display[i] for i in range(len(self._screen.display))]
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
pytest tests/test_terminal_buffer.py::test_feed_plain_text_updates_visible_lines -v
```

Expected: PASS

- [ ] **Step 5: Add failing tests for ANSI cursor movement and resize preservation**

Add:

```python
def test_feed_ansi_clear_and_cursor_movement() -> None: ...
def test_resize_changes_screen_dimensions() -> None: ...
```

- [ ] **Step 6: Run the full terminal buffer test file and confirm failures are meaningful**

Run:

```bash
pytest tests/test_terminal_buffer.py -v
```

Expected: FAIL for cursor or resize behavior until the wrapper is complete

- [ ] **Step 7: Finish the terminal buffer implementation**

Add:

- normalized decoding entrypoint for bytes from the PTY
- width and height accessors
- trailing space trimming for widget rendering

- [ ] **Step 8: Run the full terminal buffer test file and verify all tests pass**

Run:

```bash
pytest tests/test_terminal_buffer.py -v
```

Expected: PASS

- [ ] **Step 9: Commit the terminal buffer**

Run:

```bash
git add src/codex_sokoban_tui/terminal_buffer.py tests/test_terminal_buffer.py
git commit -m "feat: 添加终端缓冲与 ANSI 渲染"
```

## Task 4: Build The Codex PTY Adapter

**Files:**
- Create: `src/codex_sokoban_tui/terminal_adapter.py`
- Modify: `src/codex_sokoban_tui/terminal_buffer.py`
- Test: `tests/test_app.py`

- [ ] **Step 1: Write the first failing adapter test against a fake PTY process**

Create `tests/test_app.py` with a test helper and the first adapter test:

```python
class FakeBackend:
    def __init__(self) -> None:
        self.writes: list[bytes] = []
        self.resizes: list[tuple[int, int]] = []
        self.output = b""

    def write(self, data: bytes) -> None:
        self.writes.append(data)

    def read(self) -> bytes:
        return self.output

    def resize(self, columns: int, rows: int) -> None:
        self.resizes.append((columns, rows))


from codex_sokoban_tui.terminal_adapter import TerminalAdapter


def test_adapter_reports_missing_codex_binary() -> None:
    adapter = TerminalAdapter(command=["__missing_codex__"])

    started = adapter.start(columns=80, rows=24)

    assert started is False
    assert "not found" in adapter.status.lower()
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
pytest tests/test_app.py::test_adapter_reports_missing_codex_binary -v
```

Expected: FAIL because `TerminalAdapter` does not exist yet

- [ ] **Step 3: Implement the minimal adapter**

Implementation requirements:

- accept `command: list[str]`
- expose `status`
- expose `start(columns, rows) -> bool`
- detect missing executable with `shutil.which`
- create a PTY-backed process on Windows with `PtyProcess.spawn(...)`

Code shape:

```python
from pywinpty import PtyProcess


class TerminalAdapter:
    def __init__(self, command: list[str]) -> None:
        self.command = command
        self.status = "idle"
        self.process = None
```

- [ ] **Step 4: Run the test to verify it passes**

Run:

```bash
pytest tests/test_app.py::test_adapter_reports_missing_codex_binary -v
```

Expected: PASS

- [ ] **Step 5: Add failing tests for input forwarding, resize forwarding, and output collection with a fake backend**

Add tests shaped like:

```python
def test_adapter_writes_input_to_backend() -> None: ...
def test_adapter_resizes_backend() -> None: ...
def test_adapter_reads_output_into_terminal_buffer() -> None: ...
```

- [ ] **Step 6: Run the targeted adapter tests and confirm they fail**

Run:

```bash
pytest tests/test_app.py -k "adapter" -v
```

Expected: FAIL until backend injection and polling are implemented

- [ ] **Step 7: Complete the adapter with a replaceable backend seam**

Implementation requirements:

- separate PTY creation from higher-level adapter logic
- poll output without blocking the TUI event loop
- decode bytes safely
- forward raw key bytes unchanged when left pane is focused
- support `resize(columns, rows)`
- support `terminate()`

- [ ] **Step 8: Run the adapter tests and verify they pass**

Run:

```bash
pytest tests/test_app.py -k "adapter" -v
```

Expected: PASS

- [ ] **Step 9: Commit the adapter**

Run:

```bash
git add src/codex_sokoban_tui/terminal_adapter.py src/codex_sokoban_tui/terminal_buffer.py tests/test_app.py
git commit -m "feat: 实现 Codex 伪终端托管适配器"
```

## Task 5: Build The TUI Widgets And Focus Model

**Files:**
- Create: `src/codex_sokoban_tui/focus.py`
- Create: `src/codex_sokoban_tui/widgets.py`
- Modify: `src/codex_sokoban_tui/sokoban.py`
- Test: `tests/test_app.py`

- [ ] **Step 1: Write the first failing UI test for focus toggling**

Add to `tests/test_app.py`:

```python
from codex_sokoban_tui.app import CodexSokobanApp
from codex_sokoban_tui.focus import PaneFocus


def build_test_app() -> CodexSokobanApp:
    return CodexSokobanApp(command=["__fake_codex__"], adapter_factory=lambda *_: FakeBackend())


async def test_f6_toggles_focus_between_codex_and_game() -> None:
    app = build_test_app()

    async with app.run_test() as pilot:
        assert app.focus is PaneFocus.CODEX
        await pilot.press("f6")
        assert app.focus is PaneFocus.GAME
```

- [ ] **Step 2: Run the test to verify it fails**

Run:

```bash
pytest tests/test_app.py::test_f6_toggles_focus_between_codex_and_game -v
```

Expected: FAIL because the app shell and focus enum do not exist yet

- [ ] **Step 3: Implement the minimum focus primitives**

Create `focus.py`:

```python
from enum import Enum


class PaneFocus(str, Enum):
    CODEX = "codex"
    GAME = "game"
```

- [ ] **Step 4: Add failing UI tests for game input routing and `Ctrl+C` passthrough**

Add:

```python
async def test_game_keys_do_not_move_player_when_game_unfocused() -> None: ...
async def test_ctrl_c_is_forwarded_to_terminal_when_codex_focused() -> None: ...
```

- [ ] **Step 5: Run the targeted focus tests and confirm failures**

Run:

```bash
pytest tests/test_app.py -k "focus or ctrl_c or game_keys" -v
```

Expected: FAIL until the widgets and event routing exist

- [ ] **Step 6: Implement the game and status widgets**

Create `widgets.py` with:

- `CodexPaneWidget`
- `SokobanWidget`
- `StatusBarWidget`

Responsibilities:

- render terminal buffer lines into the left pane
- render ASCII map, moves, pushes, completion state in the right pane
- expose helper methods for focus styling

- [ ] **Step 7: Implement the input routing rules**

Rules:

- `F6` toggles focus
- `Ctrl+Q` exits the host app
- `Ctrl+C` is forwarded to the terminal adapter when `PaneFocus.CODEX` is active
- movement keys only affect the game when `PaneFocus.GAME` is active

- [ ] **Step 8: Run the focused app tests and verify they pass**

Run:

```bash
pytest tests/test_app.py -k "focus or ctrl_c or game_keys" -v
```

Expected: PASS

- [ ] **Step 9: Commit the widget and focus work**

Run:

```bash
git add src/codex_sokoban_tui/focus.py src/codex_sokoban_tui/widgets.py src/codex_sokoban_tui/sokoban.py tests/test_app.py
git commit -m "feat: 添加双栏控件与焦点切换"
```

## Task 6: Assemble The App Shell And Entry Point

**Files:**
- Create: `src/codex_sokoban_tui/app.py`
- Create: `main.py`
- Modify: `src/codex_sokoban_tui/widgets.py`
- Modify: `src/codex_sokoban_tui/terminal_adapter.py`
- Test: `tests/test_app.py`

- [ ] **Step 1: Write the first failing smoke test for app composition**

Add to `tests/test_app.py`:

```python
async def test_app_mounts_codex_pane_game_pane_and_status_bar() -> None:
    app = build_test_app()

    async with app.run_test():
        assert app.query_one("#codex-pane") is not None
        assert app.query_one("#sokoban-pane") is not None
        assert app.query_one("#status-bar") is not None
```

- [ ] **Step 2: Run the smoke test to verify it fails**

Run:

```bash
pytest tests/test_app.py::test_app_mounts_codex_pane_game_pane_and_status_bar -v
```

Expected: FAIL because the app shell does not exist yet

- [ ] **Step 3: Implement the `Textual` app shell**

Create `src/codex_sokoban_tui/app.py` with:

- `CodexSokobanApp(App)`
- constructor parameters `command: list[str] | None = None` and `adapter_factory` for tests
- vertical split layout
- startup hook that starts the terminal adapter with `["codex"]`
- timer or worker that polls PTY output
- resize handler that updates both the game and the adapter

- [ ] **Step 4: Add the executable entry point**

Create `main.py`:

```python
from codex_sokoban_tui.app import CodexSokobanApp


if __name__ == "__main__":
    CodexSokobanApp().run()
```

- [ ] **Step 5: Run the smoke test and verify it passes**

Run:

```bash
pytest tests/test_app.py::test_app_mounts_codex_pane_game_pane_and_status_bar -v
```

Expected: PASS

- [ ] **Step 6: Run the full automated test suite**

Run:

```bash
pytest -q
```

Expected: all tests PASS

- [ ] **Step 7: Manually verify the real app in a terminal**

Run:

```bash
python main.py
```

Manual checklist:

- left pane starts `codex`
- right pane is playable
- `F6` changes focus
- `Ctrl+C` still interrupts work in the left pane
- `Ctrl+Q` exits the host app
- resizing keeps both panes usable

- [ ] **Step 8: Update README with real setup notes if the manual run exposed gaps**

Add:

- Windows requirement note
- `codex` must be on `PATH`
- key bindings

- [ ] **Step 9: Commit the assembled app**

Run:

```bash
git add main.py README.md src/codex_sokoban_tui/app.py src/codex_sokoban_tui/widgets.py src/codex_sokoban_tui/terminal_adapter.py tests/test_app.py
git commit -m "feat: 集成 Codex 与推箱子双栏终端界面"
```

## Task 7: Final Repository Hygiene

**Files:**
- Modify: `README.md`

- [ ] **Step 1: Verify git status is clean except intended docs**

Run:

```bash
git status --short
```

Expected: no unexpected files

- [ ] **Step 2: Push the branch to GitHub**

Run:

```bash
git push -u origin main
```

Expected: branch published to `https://github.com/yg2224/codex-sokoban-tui`

- [ ] **Step 3: Record any manual verification caveats in `README.md`**

Add notes only if needed, for example:

- PTY support assumptions
- Windows-only current support
- tested terminal environments
