# codex-snake

`codex-snake` 是一个 Windows Terminal 启动器，左边原生 `codex`，右边 Snake。

```bash
python -m pip install -e .
codex-snake
```

`main.py` 的本地执行流程已走 `launcher` 入口，保证本地便捷运行仍然接入 launcher，而非旧的 hosted-shell 入口。

- 左边原生 `codex`
- 右边 `snake_terminal`

## 运行要求

- 安装并可执行 `wt`（Windows Terminal）。
- `codex` 必须在 `PATH` 中可调用。
- 建议在仓库根目录执行 `codex-snake`。

## 控制说明

- `WASD`：上下左右
- 方向键扩展（`\xE0` 前缀）：
  - 上：`\xE0h`
  - 下：`\xE0p`
  - 左：`\xE0k`
  - 右：`\xE0m`
- `R`：重开
- `Q`：退出

## 人工验证与阻塞

- 已完成自动化测试回归。
- 当前环境可执行 `wt` 与 `codex` 命令，但无法直接在非交互会话中观察双分屏的终端 UI，存在人工验证限制。
- 阻塞说明：无法在该会话直接截图或人工确认 `Windows Terminal` 左右分屏的实时运行状态。
