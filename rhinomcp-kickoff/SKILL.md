---
name: RhinoMCP开工
description: 把 AI 接到 Rhino：装插件、uvx 起桥、mcpstart，不走 GitHub。
version: 1.0.0
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
