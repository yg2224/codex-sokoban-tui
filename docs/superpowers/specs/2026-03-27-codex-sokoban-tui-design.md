# Codex + Sokoban Single-Terminal TUI Design

## Summary

Build a Python terminal application that starts in one terminal window and splits the screen into two panes:

- Left pane: a real interactive `codex` terminal session.
- Right pane: a playable Sokoban game.

The application is a launcher and host, not a modification of an already-running Codex session. Users enter this combined experience by starting the TUI directly.

## Goals

- Keep the left pane usable as a real `codex` session with no intentional feature loss.
- Keep the right pane instantly playable while the left pane is busy or waiting.
- Use one terminal window only.
- Make focus switching explicit and predictable.
- Keep the first version small and reliable.

## Non-Goals

- Reimplement the `codex` chat UI.
- Build a custom shell or terminal emulator beyond what is needed to host `codex`.
- Add mouse-heavy interactions.
- Build a Sokoban level editor, save system, or online features.

## User Experience

The user starts the program from the terminal, for example with `python main.py`.

After launch:

- The screen is split vertically.
- The left pane automatically starts `codex`.
- The right pane shows the current Sokoban level.
- The status bar shows the active pane, the `codex` process state, and the main hotkeys.

Keyboard focus is exclusive:

- `F6` switches focus between the left `codex` pane and the right game pane.
- When the left pane is focused, keyboard input is forwarded to `codex`.
- When the right pane is focused, `WASD` and arrow keys control the game.

Global key reservations must stay minimal so the hosted `codex` session keeps normal terminal behavior.

## Technical Approach

### Framework

Use Python with `Textual` as the outer TUI framework.

Reasons:

- Good support for pane layout and terminal redraw.
- Clean keyboard event handling.
- Practical structure for status bars, help overlays, and periodic refresh.
- Lower implementation risk than assembling a custom UI loop.

### Left Pane: Codex Host

The left pane is a terminal host for a real `codex` child process.

Responsibilities:

- Launch `codex` on app startup.
- Stream child-process output into the pane in real time.
- Forward keyboard input to the child process when the pane is focused.
- Propagate resize events so the hosted process sees the correct terminal size.
- Show explicit state when `codex` is missing, exits, or fails to start.

Implementation boundary:

- The app hosts `codex`; it does not replace or reinterpret `codex` behavior.
- The pane should behave as closely as practical to a normal terminal-backed `codex` session.

Platform note:

- On Windows, the implementation should use a real pseudo-terminal path compatible with the local environment.
- If the required pseudo-terminal capability is unavailable, fail clearly and explain why.

### Right Pane: Sokoban Game

The right pane runs a compact Sokoban implementation with a small built-in level set.

Supported features in v1:

- Player movement with `WASD` or arrow keys.
- Box pushing with standard Sokoban rules.
- Win detection when all boxes are on targets.
- Restart current level with `R`.
- Go to next level with `N`.
- Go to previous level with `P`.
- Toggle help with `?`.

Out-of-scope for v1:

- Save files.
- Procedural levels.
- Level editor.
- Score upload or multiplayer.

## Architecture

### Main Units

#### App Shell

Owns the top-level `Textual` app, layout, global hotkeys, and shutdown flow.

#### Codex Pane Adapter

Wraps child-process startup, terminal I/O, resize handling, and process-state reporting.

#### Game Engine

Pure Sokoban rules and level state:

- map parsing
- movement validation
- push rules
- win detection
- restart and level switching

This unit should be testable without the TUI.

#### Game View

Renders the current game state in the right pane and turns focused key input into game actions.

#### Status Bar

Displays:

- active focus
- current level
- move count
- push count
- `codex` process status
- key hints

## Data Flow

### Codex Pane Flow

1. App starts.
2. App launches `codex` through the terminal-host adapter.
3. Adapter reads stdout/stderr from the hosted session and updates the left pane.
4. When the left pane is focused, keypresses are sent to the hosted session.
5. On resize, the adapter updates the hosted terminal dimensions.

### Game Flow

1. App loads the current built-in level.
2. When the right pane is focused, game keys trigger movement or control actions.
3. Game engine returns the next state.
4. Game view redraws.
5. Status bar refreshes counts and completion state.

## Focus Model

Input ownership must be simple and deterministic.

- Only one pane owns keyboard input at a time.
- `F6` toggles focus.
- The status bar always indicates which pane is active.
- Keys meant for one pane must not leak into the other pane.
- App-level global shortcuts must be limited to keys that are unlikely to conflict with normal `codex` terminal use.

Reserved app-level shortcuts:

- `F6` for focus toggle.
- `Ctrl+Q` for quitting the host app.

Non-reserved keys:

- `Ctrl+C` must pass through to the hosted `codex` session when the left pane is focused.
- Regular text-entry and terminal control keys should remain available to `codex` unless explicitly reserved by the host app.

This avoids conflicts between:

- terminal editing and control keys on the left
- movement keys on the right

## Error Handling

### Codex Not Installed

If `codex` is not found:

- left pane shows a clear startup error
- status bar marks the pane unavailable
- help text explains how to install or expose `codex` on `PATH`

### Codex Exits

If the child process exits:

- left pane shows exit status
- the pane stops accepting forwarded input
- a restart shortcut may be offered if implementation cost is low

### PTY Failure

If the environment cannot create the hosted terminal correctly:

- fail clearly
- avoid pretending the left pane still behaves like a real session

### Window Resize

If a resize event arrives:

- relayout both panes
- recompute game rendering
- propagate terminal size to the hosted `codex` session

## Testing Strategy

### Automated Tests

Prioritize tests for the pure game logic:

- movement into empty tiles
- movement blocked by walls
- pushing one box into free space
- rejecting pushes into walls or another box
- level completion detection
- restart behavior
- next and previous level behavior

Add targeted UI-level tests where practical:

- focus toggle updates state
- game pane ignores movement keys when unfocused
- status bar reflects key state changes

### Manual Verification

Use manual checks for the hosted `codex` pane because real terminal-process behavior is environment-sensitive:

- app launches and opens both panes
- left pane starts `codex`
- focused typing reaches `codex`
- `F6` switches control reliably
- right pane remains playable while left pane keeps updating
- resize keeps both panes usable

## Implementation Risks

- Windows pseudo-terminal integration may be the hardest part.
- Terminal redraw under heavy `codex` output may require careful buffering.
- Some control sequences from `codex` may need handling or passthrough decisions.

## Recommended Delivery Scope

Deliver in this order:

1. App shell with split layout and focus model.
2. Pure Sokoban engine with tests.
3. Game pane rendering and controls.
4. Hosted `codex` pane with real process wiring.
5. Status bar, help overlay, and shutdown polish.

## Acceptance Criteria

- Starting the app opens one terminal UI with left and right panes.
- The left pane starts a real `codex` session.
- The right pane is a playable Sokoban game.
- `F6` switches focus between panes.
- Input goes only to the focused pane.
- `Ctrl+C` still works inside the hosted `codex` session when the left pane is focused.
- Basic Sokoban controls work across multiple built-in levels.
- The app handles missing `codex` or hosted-terminal failure with explicit errors.
