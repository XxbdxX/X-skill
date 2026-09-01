---
name: RhinoMCP开工
description: 把 AI 接到 Rhino：装插件、uvx 起桥、mcpstart，不走 GitHub。
version: 1.1.0
---

# RhinoMCP 打通（第一步）

目标：让当前 Agent **真的连上本机 Rhino**，能建几何、截视口。不是讲原理。

适用：任何能配本地 MCP 的客户端（WorkBuddy、Claude Desktop、Claude Code、Cursor、Codex、Cline 等）。改的是「MCP 配置里的 rhino 这一项」，不是某个软件专属流程。

默认用社区包 **jingcheng-chen / rhinomcp 0.3.x**（Rhino Package Manager 搜 `rhinomcp`）。不要装 McNeel 官方 `RhinoMCP`，两套插件不要混。

**禁止：** `git clone`、访问 GitHub、`Please install https://github.com/jingcheng-chen/rhinomcp`。国内会卡死。也不要用 ghproxy。

## 0. 先问环境

只问一次，缺什么补什么：

- 系统：Windows 还是 Mac
- Rhino 是否已装（7 或更新）
- 用的哪个 AI 客户端（能配 MCP 即可）
- 有没有 Python 3.10+（`python --version` / `py --version`）

缺 Rhino：停，让用户先装 Rhino。不要继续。

## 1. 装 Rhino 插件（不走 GitHub）

在 **Rhino** 里：

1. 命令 `PackageManager`（或 Tools → Package Manager）
2. 搜 **rhinomcp**，Install
3. **重启 Rhino**

装完重启前不要做第 4 步。

## 2. 装 uv（给 `uvx rhinomcp` 用）

检查：`uvx --version`。有就跳过。

没有时 **按这个顺序**，不要用 `curl github.com` / `irm https://astral.sh/uv/install.ps1`：

**Mac**

```bash
brew install uv
```

没有 brew 时：

```bash
pip3 install uv -i https://mirrors.aliyun.com/pypi/simple
```

**Windows**（PowerShell）

```powershell
pip install uv -i https://mirrors.aliyun.com/pypi/simple
```

或已有 `winget`：`winget install astral-sh.uv`

装完确认 `uvx --version`。`uvx` 不在 PATH 时，用完整路径（常见：`%APPDATA%\Python\Python3x\Scripts\uvx.exe` 或 `%USERPROFILE%\.local\bin\uvx.exe`）。

跑 MCP 前先设国内源（当前会话即可）：

```bash
set UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
```

PowerShell：`$env:UV_INDEX_URL="https://mirrors.aliyun.com/pypi/simple"`

先单独试一次：`uvx rhinomcp` 能启动就算桥可用。不要去 clone 源码。

## 3. 写入客户端的 MCP 配置

标准片段（各客户端字段名可能是 `mcpServers`）：

```json
{
  "mcpServers": {
    "rhino": {
      "command": "uvx",
      "args": ["rhinomcp"],
      "env": {
        "RHINO_MCP_HOST": "127.0.0.1",
        "UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple"
      }
    }
  }
}
```

Windows 上若 `uvx` 不是一条命令，把 `command` 改成 `uvx.exe` 的绝对路径，`args` 仍为 `["rhinomcp"]`。

常见落点（以用户本机为准，找不到就问）：

- **Claude Code / Codex：** `claude mcp add rhino -- uvx rhinomcp` 或 `codex mcp add rhino --env RHINO_MCP_HOST=127.0.0.1 -- uvx rhinomcp`（加国内源时用手动 JSON）
- **Claude Desktop：** 设置里的 MCP 配置 JSON
- **Cursor：** `.cursor/mcp.json` 或 Settings → MCP
- **WorkBuddy：** `~/.workbuddy/mcp.json`（Windows：`%USERPROFILE%\.workbuddy\mcp.json`），或 连接器 / MCP → 自定义连接器

写入后重启该客户端（或关掉再开 MCP 连接）。同一时间只开一个连 Rhino 的 MCP 客户端。

## 4. 打开桥

1. 打开 Rhino（重启插件后的那次）
2. 命令行输入 **mcpstart**（大小写不敏感）
3. 每个 Rhino 会话做一次；停用：**mcpstop**

没有这一步，Agent 会连不上。

## 5. 连通验收（必须做）

连上后立刻做，不要先讲大项目：

1. 列出 Rhino MCP 工具，确认有几何/视口类工具
2. 读当前文档信息（物体数量即可）
3. 建一个边长 1000mm 的盒子
4. 截一张 perspective 视口图给用户看

四步都成功才算打通。失败时按下面排，不要重装整个 Rhino。

## 6. 打不通时

按顺序查，改一处再测：

1. Rhino 没开，或没跑 **mcpstart**
2. 插件不是 Package Manager 里的 `rhinomcp`，或没重启 Rhino
3. 客户端里 `rhino` 没亮 / 没重启客户端
4. `uvx rhinomcp` 自己跑不起来：换阿里云 PyPI 源；确认 Python ≥ 3.10
5. Windows 找不到 `uvx`：改成绝对路径
6. 端口被占：关掉另一个 AI 客户端里的同一套 rhino MCP，或 `mcpstop` 后再 `mcpstart`

## 7. 打通之后怎么用（一句）

用户用中文说要建什么（尺寸用毫米）。先读场景再建模；改完截同一机位视口。不要一上来建整栋楼。

McNeel 官方 RhinoMCP 仍是 WIP，这份 skill 不要去装它。

## 8. 连上后的默认演示（用户没点名要建什么时）

第 5 步盒子验收成功、用户还没给项目时：**不要空停，也不要建整栋楼。** 做「开场三连」，让人一眼看到 AI 不只会画盒子。

规则：

- 几何只放新图层 `MCP_Demo`，不要动用户已有模型
- 已有重要模型时：只加图层，禁止 boolean / 全选删除
- 每个任务做完立刻截 `perspective`（`zoom_to_fit=True`）给用户看，再做下一个
- 三个都做完就停，问还要不要可选项
- 尺寸一律毫米。某个工具当前客户端没有：跳过该项，改下一项，不要卡死

### A · Loft 花瓶（曲面，不是盒子）

1. `CIRCLE`：圆心 `(0,0,0)` 半径 `400`
2. `CIRCLE`：圆心 `(0,0,800)` 半径 `180`
3. `loft` 这两根曲线（普通 loft 即可）
4. 上色，截透视

看点：两条圆一 loft，花瓶形体出来。这是「高级建模」而不是堆 primitive。

### B · 文字 + 尺寸标注（图纸感）

rhinomcp 通常没有独立的 dimension 工具，用 `execute_rhinoscript_python_code`：

```python
import rhinoscriptsyntax as rs
rs.AddText("1000 mm", (500, -250, 0), 80)
rs.AddLinearDimension((0, 0, 0), (1000, 0, 0), (500, -180, 0))
```

看点：视口里同时出现模型和标注。很多人不知道 MCP 能标尺寸。

失败就跳过，不要为标注重装插件。

### C · Grasshopper 三层楼（拖 slider 会变）

1. `gh_create_document(new_if_missing=True, make_active=True)`
2. `gh_build_graph` 搭最少节点：`XY Plane` + 层数 `Number Slider`(默认 3) + `Series` + `Vector XYZ` + `Move` + `Center Box`（平面尺寸约 8000×6000，层高 3500）
3. `recompute=True`，截 GH 预览或 Rhino 透视

看点：告诉用户去 Grasshopper 拖「层数」slider，楼会变高。这是参数化，不是死模型。

连线失败时不要硬撑吸引子/逐顶点变形。退回 A 的 loft 即可。

### 可选（用户说「再来」时，每次只做一个）

- **Pipe 栏杆**：一条折线/曲线 + `pipe`（半径 40）。看点：家具/扶手，不是体块。
- **布尔挖洞**：盒子减一个圆柱/球。看点：空心、洞口。
- **GH 嵌套玻璃球**：`Mesh Sphere Ex` + 多层半径 Series（不要做 sin 逐顶点，MCP 走不通）。看点：参数化好看，不是建筑。

不要默认跑可选三项。三连已经够「这也行」。
