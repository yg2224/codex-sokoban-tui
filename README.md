# codex-sokoban-tui

Run a single-terminal `Textual` app with a real `codex` session on the left and Sokoban on the right.

## Requirements

- Windows is the current target environment.
- `codex` must be available on `PATH`.
- Python `3.12+`

## Development

```bash
python -m pip install -e .[dev]
python main.py
pytest -q
```

## Key Bindings

- `F6`: switch focus between the Codex pane and the Sokoban pane
- `Ctrl+C`: forward interrupt to the Codex pane when it is focused
- Arrow keys / `WASD`: move in Sokoban when the game pane is focused

## Notes

- The app is interactive and keeps running until you quit it.
- Tests use fake adapters and do not start a real `codex` process.
