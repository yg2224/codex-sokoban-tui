# codex-snake

`codex-snake` 是一个面向 Windows Terminal 的双 pane 启动器：

- 左侧运行原生 `codex`
- 右侧运行终端版 Snake
- 左侧默认约 `75%` 宽度，右侧 Snake 默认约 `25%`
- 无论你从哪个目录启动，两个 pane 都会使用你当前终端的工作目录

适合一边用 `codex` 干活，一边在旁边挂一个轻量小游戏。

## 环境要求

- Windows
- 已安装 `Windows Terminal`，并且命令 `wt` 可用
- 已安装 `codex`，并且命令 `codex` 可用
- Python `3.11+`

## 安装

在仓库根目录执行：

```bash
python -m pip install -e . --no-build-isolation
```

安装完成后，可以在任意目录直接运行：

```bash
codex-snake
```

## 启动效果

执行 `codex-snake` 后会打开一个新的 `Windows Terminal` 窗口：

- 左侧 pane：原生 `codex`
- 右侧 pane：Snake

当前实现使用垂直分屏，右侧 Snake pane 固定为约 `25%` 宽度。

## Snake 控制

- `WASD`：上下左右
- 方向键：上下左右
- `R`：重新开始
- `Q`：退出右侧 Snake pane
- `Alt+F`：切换左右 pane 焦点

游戏内顶部状态栏也会显示这些按键提示。

## 常见问题

### 1. `codex-snake` 无法识别

通常是当前 Python 环境还没有安装这个项目。回到仓库根目录重新执行：

```bash
python -m pip install -e . --no-build-isolation
```

如果你使用的是 Conda、虚拟环境或多个 Python，请确认安装和运行使用的是同一个环境。

### 2. 提示找不到 `wt`

说明 `Windows Terminal` 没有安装好，或者没有加入 `PATH`。

你可以先在 PowerShell 里检查：

```powershell
wt
```

### 3. 提示找不到 `codex`

说明 `codex` 当前不在 `PATH` 中。先确认下面命令能运行：

```powershell
codex
```

### 4. 右侧 Snake 没有聚焦，或者切换焦点不符合预期

本项目会在界面中提示使用 `Alt+F`。如果你的 `Windows Terminal` 本地快捷键配置不同，以你自己的终端配置为准。

## 开发

运行测试：

```bash
python -m pytest -v
```

当前核心覆盖包括：

- 启动命令生成
- 工作目录继承
- Snake 按键映射
- Snake 渲染
- 碰撞、得分、重开

## 当前限制

- 这是一个 Windows 优先的小工具，未做跨平台 pane 管理适配
- 当前会话里无法直接自动验证 `Windows Terminal` 图形界面的实际分屏效果，仍需要人工确认
