# codex-snake

Packaging transition for a Windows Terminal launcher that will pair native `codex` with Snake.

## 安装与运行

```bash
python -m pip install -e .
codex-snake
```

当前这个入口已经切到新的 `codex-snake` 命令名，但完整的 `Windows Terminal` 分屏启动行为会在后续任务里补齐。

## 运行要求

- 仅支持 `Windows`。
- 需要安装并可用 `Windows Terminal`。
- `codex` 命令必须在 `PATH` 中可访问。
- Snake 控制说明：
  - `WASD` 移动
  - 方向键移动
  - `R` 重新开始关卡
  - `Q` 退出

## 注意

如果你修改过 `pyproject.toml` 的 packaging 配置，请在当前环境重新执行：

```bash
python -m pip install -e .
```

否则 `codex-snake` 可执行脚本可能不会刷新。
