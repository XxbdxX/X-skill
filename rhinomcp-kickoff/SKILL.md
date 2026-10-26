---
name: rhino-开工
slug: rhinomcp-kickoff
displayName: rhino-开工
description: 把 AI 接到本机 Rhino：装 rhinomcp 插件、uvx 起桥、跑 mcpstart，全程不走 GitHub，国内网络也能通。连上后先问职业，没项目就做一件小演示，让你一眼看到 AI 真能建东西。适用于任何能配本地 MCP 的客户端。
version: 1.4.0
---

# RhinoMCP 打通（第一步）

目标：让当前 Agent **真的连上本机 Rhino**，能建几何、截视口。不是讲原理。

适用：任何能配本地 MCP 的客户端（WorkBuddy、Claude Desktop、Claude Code、Cursor、Codex、Cline 等）。改的是「MCP 配置里的 rhino 这一项」，不是某个软件专属流程。

默认装 Rhino Package Manager 里的最新 **rhinomcp**（搜这个名字，点 Install）。不要锁死 0.3.x。2026-09-14 的发布是 **0.4.1.1**。插件和下面的 `uvx` 桥必须同一代，不要一个新一个旧。不要装 McNeel 官方 `RhinoMCP`，两套插件不要混。

**禁止：** `git clone`、访问 GitHub、`Please install https://github.com/jingcheng-chen/rhinomcp`。国内会卡死。也不要用 ghproxy。

## 0. 第一句就问

只问一次。第一条消息先问职业，同一条里把环境问完。不要先讲原理，不要先建模型。

职业（必问，只给这三个，不要改成开放长问）：

- 建筑设计
- 景观设计
- 室内设计

环境（同一条里问，缺什么补什么）：

- 系统：Windows 还是 Mac
- Rhino 是否已装（7 或更新）
- 用的哪个 AI 客户端（能配 MCP 即可）
- 有没有 Python 3.10+（`python --version` / `py --version`）

用户已经说了要建什么：记下，连上后再做，不要跳过打通。
缺 Rhino：停，让用户先装 Rhino。不要继续。
职业没答：先打通，打通后再问一次。不要为了等职业卡住安装。

## 1. 装 Rhino 插件（不走 GitHub）

在 **Rhino** 里：

1. 命令 `PackageManager`（或 Tools → Package Manager）
2. 搜 **rhinomcp**，Install
3. **重启 Rhino**

装完重启前不要做第 4 步。

## 2. 装 uv（给 `uvx rhinomcp@latest` 用）

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

先单独试一次：`uvx rhinomcp@latest` 能启动就算桥可用。`@latest` 是为了每次启动重新解析，不要停在第一次下到的旧版。不要去 clone 源码。

## 3. 写入客户端的 MCP 配置

标准片段（各客户端字段名可能是 `mcpServers`）：

```json
{
  "mcpServers": {
    "rhino": {
      "command": "uvx",
      "args": ["rhinomcp@latest"],
      "env": {
        "RHINO_MCP_HOST": "127.0.0.1",
        "UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple"
      }
    }
  }
}
```

Windows 上若 `uvx` 不是一条命令，把 `command` 改成 `uvx.exe` 的绝对路径，`args` 仍为 `["rhinomcp@latest"]`。

常见落点（以用户本机为准，找不到就问）：

- **Claude Code / Codex：** `claude mcp add rhino -- uvx rhinomcp@latest` 或 `codex mcp add rhino --env RHINO_MCP_HOST=127.0.0.1 -- uvx rhinomcp@latest`（加国内源时用手动 JSON）
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
4. `uvx rhinomcp@latest` 自己跑不起来：换阿里云 PyPI 源；确认 Python ≥ 3.10。若提示插件和桥版本不一致，两边都换成 Package Manager / PyPI 的最新版，不要退回 0.3.x
5. Windows 找不到 `uvx`：改成绝对路径
6. 端口被占：关掉另一个 AI 客户端里的同一套 rhino MCP，或 `mcpstop` 后再 `mcpstart`

## 7. 打通之后怎么用（一句）

用户用中文说要建什么（尺寸用毫米）。先读场景再建模；改完截同一机位视口。不要一上来建整栋楼。

用户没说要建什么：不要空停，走第 8 节，只做一件。

McNeel 官方 RhinoMCP 仍是 WIP，这份 skill 不要去装它。

## 8. 连上后的默认演示（用户没点名要建什么时）

第 5 步盒子验收成功、用户还没给项目时：**按职业只做一件。** 不要做开场三连，不要建整栋楼，不要建写实的人。

规则：

- 几何只放新图层 `MCP_Demo`，不要动用户已有模型
- 已有重要模型时：只加图层，禁止 boolean 用户的旧物体 / 全选删除
- 做完立刻截 `perspective`（`zoom_to_fit=True`）给用户看，然后停
- 停的时候问：要做你自己的，还是再看另一个
- 尺寸一律毫米
- 某个脚本失败：留下已经建成的部分，截图，不要为了补全去重装插件

职业对应：

- **建筑设计**：小房子（外观体块）
- **室内设计**：一间房（墙 + 门洞 + 一张桌子）。不要做整套户型，也不要做外观体块
- **景观设计**：两三根地面曲线 + 一个高 1700mm 的尺度人。尺度人只要球头加身体，不要写实人体
- **没选 / 说不清**：做小房子

### A · 建筑：小房子

用 `execute_rhinoscript_python_code`：

```python
import rhinoscriptsyntax as rs

layer = "MCP_Demo"
if not rs.IsLayer(layer):
    rs.AddLayer(layer)
rs.CurrentLayer(layer)

def box(x0, y0, z0, x1, y1, z1):
    return rs.AddBox([
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ])

walls = box(0, 0, 0, 6000, 4000, 3000)
door = box(2550, -400, 0, 3450, 500, 2100)
try:
    rs.BooleanDifference(walls, door, True)
except Exception:
    pass
box(-300, -300, 3000, 6300, 4300, 3600)
```

看点：底盘、门洞、屋面板。这是一栋能认出的小房子，不是盒子堆。布尔失败就留下门洞方块，不要重试整栋楼。

### B · 室内：一间房

```python
import rhinoscriptsyntax as rs

layer = "MCP_Demo"
if not rs.IsLayer(layer):
    rs.AddLayer(layer)
rs.CurrentLayer(layer)

def box(x0, y0, z0, x1, y1, z1):
    return rs.AddBox([
        [x0, y0, z0], [x1, y0, z0], [x1, y1, z0], [x0, y1, z0],
        [x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1],
    ])

box(0, 0, -80, 4000, 3000, 0)
box(0, 0, 0, 1400, 180, 2700)
box(2300, 0, 0, 4000, 180, 2700)
box(0, 2820, 0, 4000, 3000, 2700)
box(0, 0, 0, 180, 3000, 2700)
box(3820, 0, 0, 4000, 3000, 2700)
box(1200, 1100, 0, 2800, 1900, 750)
```

看点：门洞和一张桌子。不要加沙发、灯、材质包。

### C · 景观：线 + 尺度人

```python
import rhinoscriptsyntax as rs

layer = "MCP_Demo"
if not rs.IsLayer(layer):
    rs.AddLayer(layer)
rs.CurrentLayer(layer)

rs.AddCurve([[0, 0, 0], [6000, 800, 0], [12000, 400, 0]])
rs.AddCurve([[500, -2000, 0], [5000, -600, 0], [11000, 200, 0]])
rs.AddCurve([[0, 2500, 0], [7000, 3200, 0], [13000, 2200, 0]])
rs.AddBox([
    [7820, 1380, 0], [8180, 1380, 0], [8180, 1620, 0], [7820, 1620, 0],
    [7820, 1380, 1450], [8180, 1380, 1450], [8180, 1620, 1450], [7820, 1620, 1450],
])
rs.AddSphere([8000, 1500, 1590], 110)
```

看点：路是线，人是尺度，不是角色建模。

### 用户说「再来」时，每次只做一个

- 另一职业的那一件（没看过的小房子 / 房间 / 线加人）
- 不要默认跑 Loft 花瓶、尺寸标注、Grasshopper 三层楼

三件都看过就停，让用户说自己的项目。
