---
name: sketchup-开工
slug: sketchup-kickoff
displayName: sketchup-开工
description: 把 AI 接到本机 SketchUp：把随包扩展拷进 Plugins、uvx 起桥、在菜单里 Start Server。不走 Extension Warehouse，也不让用户打开 GitHub。连上后先问职业，没项目就做一件小演示。适用于任何能配本地 MCP 的客户端。
version: 1.0.1
---

# SketchUp 打通（第一步）

目标：让当前 Agent **真的连上本机 SketchUp**，能建一个盒子并导出一张图。不是讲原理，不是建模教程。

适用：任何能配本地 MCP 的客户端（WorkBuddy、Claude Desktop、Claude Code、Cursor、Codex、Cline 等）。改的是「MCP 配置里的 sketchup 这一项」。

桥用 PyPI 的 **sketchup-mcp**（2026-10-26 查到的版本是 **0.1.17**）。扩展文件在本 skill 的 `extension/` 里，来自 `mhyrr/sketchup-mcp` 的 MIT 源码，不是 Extension Warehouse 上的包。仓库没有发布好的 rbz，所以不要让用户自己去下。

**禁止：** `git clone`、打开 GitHub、Extension Warehouse 里搜 MCP、改走 `api.sketchup.com` 的官方云端 MCP。官方那个是另一套，这份 skill 不覆盖。国内打不开 GitHub 时，用随包文件，不要换路。

**没在这台机器上跑过验收。** SketchUp 不在写这份 skill 的电脑上。连上之后必须做第 5 步，不要把文档写成已经打通。

## 0. 第一句就问

只问一次。第一条消息先问职业，同一条里把环境问完。不要先讲原理，不要先建模型。

职业（必问，只给这三个）：

- 建筑设计
- 景观设计
- 室内设计

环境（同一条里问，缺什么补什么）：

- 系统：Windows 还是 Mac
- SketchUp 是否已装，哪一年的版本
- 用的哪个 AI 客户端
- 有没有 Python 3.10+（`python --version` / `py --version`）

用户已经说了要建什么：记下，连上后再做，不要跳过打通。
缺 SketchUp：停，让用户先装。不要继续。
职业没答：先打通，打通后再问一次。

## 1. 装扩展（用随包文件，不走仓库）

本 skill 目录下有：

- `extension/su_mcp.rb`
- `extension/su_mcp/main.rb`

拷进该用户 **已安装那个年份** 的 Plugins 文件夹。找不到年份就问，不要猜。

常见落点：

- Mac：`~/Library/Application Support/SketchUp 20XX/SketchUp/Plugins/`
- Windows：`%APPDATA%\SketchUp\SketchUp 20XX\SketchUp\Plugins\`

拷完应是：

- `Plugins/su_mcp.rb`
- `Plugins/su_mcp/main.rb`

不要只拷 `main.rb`。拷完让用户自己重启 SketchUp 一次。代理不要 `kill`、`quit`、`osascript quit`、`taskkill`，也不要反复 `open`。重启前不要做第 4 步。

## 2. 装 uv（给 `uvx sketchup-mcp@latest` 用）

检查：`uvx --version`。有就跳过。

没有时按这个顺序，不要用 `curl github.com`：

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

跑 MCP 前先设国内源（当前会话即可）：

```bash
set UV_INDEX_URL=https://mirrors.aliyun.com/pypi/simple
```

PowerShell：`$env:UV_INDEX_URL="https://mirrors.aliyun.com/pypi/simple"`

先单独试一次：`uvx sketchup-mcp@latest` 能启动就算桥的包可用。这时还连不上 SketchUp 是正常的，因为第 4 步还没做。`@latest` 是为了不要停在第一次下到的旧版。

## 3. 写入客户端的 MCP 配置

```json
{
  "mcpServers": {
    "sketchup": {
      "command": "uvx",
      "args": ["sketchup-mcp@latest"],
      "env": {
        "UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple"
      }
    }
  }
}
```

桥写死连 `localhost:9876`。不要改端口，不要加 Rhino 那种 `RHINO_MCP_HOST`。

Windows 上若 `uvx` 不是一条命令，把 `command` 改成 `uvx.exe` 的绝对路径，`args` 仍为 `["sketchup-mcp@latest"]`。

常见落点：

- **Claude Code / Codex：** `claude mcp add sketchup -- uvx sketchup-mcp@latest` 或 `codex mcp add sketchup -- uvx sketchup-mcp@latest`
- **Claude Desktop：** 设置里的 MCP 配置 JSON
- **Cursor：** `.cursor/mcp.json` 或 Settings → MCP
- **WorkBuddy：** `~/.workbuddy/mcp.json`（Windows：`%USERPROFILE%\.workbuddy\mcp.json`），或 连接器 / MCP → 自定义连接器

写入后重启该客户端。同一时间只开一个连 SketchUp 的 MCP 客户端。

## 4. 打开桥

1. 打开 SketchUp（重启扩展后的那次）
2. 菜单 **Plugins → MCP Server → Start Server**
3. 中文界面里 Plugins 可能显示成「插件」或「扩展程序」。子菜单名是英文 **MCP Server**，不要去找「SketchupMCP」
4. 停用：**Stop Server**

没有这一步，Agent 会连不上。扩展在 `127.0.0.1:9876` 听。代理点不到这个菜单就停，让用户自己点。不要关闭 SketchUp 再打开。

## 5. 连通验收（必须做）

连上后立刻做，不要先讲大项目。PyPI 0.1.17 的工具是这些，不要调用 README 里写过、包里没有的 `get_scene_info`：

`create_component`、`delete_component`、`transform_component`、`get_selection`、`set_material`、`export_scene`、`eval_ruby`

验收：

1. 列出工具，确认有 `create_component` 和 `export_scene`
2. `create_component`，`type` 为 `cube`。SketchUp Ruby 内部单位是英寸。要大约 1 米的盒子，`dimensions` 用 `[39.37, 39.37, 39.37]`，不要按毫米传，否则会变成一根针
3. `export_scene`，`format` 为 `png`，把图给用户看

三步都成功才算打通。失败时按下面排，不要重装 SketchUp。

## 6. 打不通时

按顺序查，改一处再测。SketchUp 已经开着时，禁止再启动或关闭它。连不上就停，把缺的那一步告诉用户。

1. SketchUp 没开：让用户打开一次。已经开着就不要再开
2. 没点 **Start Server**：让用户点。不要用重启代替点击
3. Plugins 里缺 `su_mcp.rb` 或 `su_mcp/main.rb`：补文件后让用户重启一次，只此一次
4. 客户端里 `sketchup` 没亮：重启的是 AI 客户端，不是 SketchUp
5. `uvx sketchup-mcp@latest` 自己跑不起来：换阿里云 PyPI 源；确认 Python ≥ 3.10
6. 端口被占：关掉另一个 AI 客户端里的同一套 sketchup MCP，或让用户点 Stop Server 后再 Start Server
7. 不要改去官方云端 MCP 凑数

## 7. 打通之后怎么用（一句）

用户用中文说要建什么。先看当前模型里有没有既有物体；有就新建，不要删用户的旧东西。做完用 `export_scene` 出 png。不要一上来建整栋楼。

用户没说要建什么：不要空停，走第 8 节，只做一件。

不要做榫卯、燕尾榫、指接。那些工具在包里，但这份 skill 不用。

## 8. 连上后的默认演示（用户没点名要建什么时）

第 5 步盒子成功、用户还没给项目时：**按职业只做一件。** 用 `eval_ruby`。失败就留下盒子，截图，停。不要为了补全去重装。

单位仍是英寸。下面脚本里的数字已经换成英寸。

- **建筑设计**：小房子
- **室内设计**：一间房加一张桌子
- **景观设计**：三条地面线加一个约 1.7 米的尺度人（盒子加球，不要写实人体）
- **没选 / 说不清**：做小房子

做完 `export_scene` format `png`，然后停，问要做自己的还是再看另一个。

### A · 建筑：小房子

```ruby
model = Sketchup.active_model
model.start_operation('MCP_Demo', true)
ents = model.active_entities
def box(ents, x0, y0, z0, x1, y1, z1)
  g = ents.add_group
  f = g.entities.add_face([x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0])
  f.pushpull(z1 - z0)
  g
end
box(ents, 0, 0, 0, 236, 157, 118)
box(ents, 100, -16, 0, 136, 20, 83)
box(ents, -12, -12, 118, 248, 169, 142)
model.commit_operation
```

布尔挖门失败就留下门洞方块。不要重试整栋楼。

### B · 室内：一间房

```ruby
model = Sketchup.active_model
model.start_operation('MCP_Demo', true)
ents = model.active_entities
def box(ents, x0, y0, z0, x1, y1, z1)
  g = ents.add_group
  f = g.entities.add_face([x0,y0,z0],[x1,y0,z0],[x1,y1,z0],[x0,y1,z0])
  f.pushpull(z1 - z0)
  g
end
box(ents, 0, 0, -3, 157, 118, 0)
box(ents, 0, 0, 0, 55, 7, 106)
box(ents, 90, 0, 0, 157, 7, 106)
box(ents, 0, 111, 0, 157, 118, 106)
box(ents, 0, 0, 0, 7, 118, 106)
box(ents, 150, 0, 0, 157, 118, 106)
box(ents, 47, 43, 0, 110, 75, 30)
model.commit_operation
```

看点：门洞和一张桌子。不要加沙发、灯、材质包。

### C · 景观：线 + 尺度人

```ruby
model = Sketchup.active_model
model.start_operation('MCP_Demo', true)
ents = model.active_entities
ents.add_curve([[0,0,0],[236,31,0],[472,16,0]])
ents.add_curve([[20,-79,0],[197,-24,0],[433,8,0]])
ents.add_curve([[0,98,0],[276,126,0],[512,87,0]])
g = ents.add_group
f = g.entities.add_face([308,54,0],[322,54,0],[322,64,0],[308,64,0])
f.pushpull(57)
ents.add_circle([315,59,63], [0,0,1], 4)
model.commit_operation
```

看点：路是线，人是尺度。圆没有推拉成球也行，不要为了补一个球重做。
