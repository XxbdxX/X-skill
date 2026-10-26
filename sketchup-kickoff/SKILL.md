---
name: sketchup-开工
slug: sketchup-kickoff
displayName: sketchup-开工
description: 把 AI 接到本机 SketchUp：拷扩展 + 打补丁、uvx 起桥、锁死版本组合、一键自检。不走 Extension Warehouse，不让用户打开 GitHub。连上后按用户给的任务做，没项目就做一件小演示。适用于任何能配本地 MCP 的客户端。
version: 1.1.0
---

# SketchUp 打通（第一步）

目标：让当前 Agent **真的连上本机 SketchUp**，能建一个形体并导出一张图。不是讲原理，不是建模教程。

**v1.1 修订说明（重要）：** v1.0 写于没装 SketchUp 的机器上，未验收。v1.1 在 **Windows 11 + SketchUp 2020 (20.1.229) + Python 3.13 + uv 0.13.5** 实测打通，修掉 5 个会让流程卡死的问题。**v1.0 里 `sketchup-mcp@latest` 那套配置今天直接跑不起来**，原因见第 3 节。

已验证和未验证分开标：

| 状态 | 内容 |
|---|---|
| ✅ 已实测 | 镜像源装 uv、扩展拷入、两个补丁、版本锁组合、explorer 启动、TCP 直连、eval_ruby 建模、PNG 出图 |
| ⚠️ 未实测 | 第 8 节三段演示代码（小房子/房间/景观）、Mac 路径、其他 SketchUp 年份 |

**禁止：** `git clone`、让用户打开 GitHub、Extension Warehouse 里搜 MCP、改走 `api.sketchup.com` 的官方云端 MCP。国内打不开 GitHub 时用随包文件，不要换路。

---

## 0. 先问（只问一次）

第一条消息把要问的一次问完，不要先讲原理。

**用户已经说要建什么**（比如「建个正二十面体」）→ 记下，直接开工，跳过职业询问，连上后立刻做。不要因为「流程规定」卡着他先答职业。

**用户没说建什么** → 问一次，只要这三选一：建筑设计 / 景观设计 / 室内设计。

环境（缺什么补什么，能自己测就别问）：

- 系统：Windows 还是 Mac
- SketchUp 年份和安装路径（**别猜**，见 1.1 的查找命令）
- 有没有 Python 3.10+ 和 `uvx`

缺 SketchUp → 停，让用户先装。

---

## 1. 装扩展 + 打补丁

### 1.1 找 Plugins 目录

按**已安装的年份**找，不要猜。Windows：

```bash
ls -d "/c/Program Files/SketchUp"*/SketchUp* "/d/Program Files/SketchUp"*/SketchUp* 2>/dev/null
find /c /d -maxdepth 4 -iname "SketchUp.exe" 2>/dev/null
```

用户配置目录（扩展真正要放的地方）：

- Windows：`%APPDATA%\SketchUp\SketchUp 20XX\SketchUp\Plugins\`
- Mac：`~/Library/Application Support/SketchUp 20XX/SketchUp/Plugins/`

拷完必须是这样（**不要只拷 main.rb**）：

```
Plugins/su_mcp.rb
Plugins/su_mcp/main.rb
```

### 1.2 打两个补丁（v1.1 新增，不打就连不上）

**补丁 A — 移除启动期的 `SKETCHUP_CONSOLE.show`。**
`main.rb` 里有 3 处（约 L7、L19、L24），在 SketchUp 2020 加载期调用会让进程**无提示直接退出**，表现为「启动一下就没了」。把这三处删掉或注释，`log` 方法改为写文件：

```ruby
def log(msg)
  begin
    File.open(@log_path, 'a') { |f| f.puts("[#{Time.now.strftime('%H:%M:%S')}] #{msg}") }
  rescue
  end
  puts "MCP: #{msg}"
end
```

并在 `initialize` 里加 `@log_path = File.join(File.dirname(__FILE__), 'mcp_server.log')`。

**补丁 B — 自动 Start Server。**
v1.0 让用户手点菜单，在 Agent 场景下等于断链（Agent 点不了菜单）。在 `su_mcp.rb` 的 `register_extension` 之后加：

```ruby
UI.start_timer(3.0, false) {
  begin
    srv = (defined?(SU_MCP) ? SU_MCP.instance_variable_get(:@server) : nil)
    srv.start if srv && !srv.instance_variable_get(:@running)
  rescue
  end
}
```

补丁前先 `cp main.rb main.rb.orig` 备份。改完**重启 SketchUp** 才生效。

---

## 2. 装 uv

检查：`uvx --version`。有就跳过。

Windows（PowerShell）：`pip install uv -i https://mirrors.aliyun.com/pypi/simple`
Mac 无 brew 时：`pip3 install uv -i https://mirrors.aliyun.com/pypi/simple`

装完记下 `uvx` 的**绝对路径**（Windows 上常不在 PATH 里，要写进 MCP 配置）。

---

## 3. 写 MCP 配置（必须锁版本，这是 v1.1 最关键的改动）

v1.0 的配置是 `"args": ["sketchup-mcp@latest"]`。**这个写法 2026-10-26 实测崩溃**：

1. `@latest` 拉到 `sketchup-mcp 0.1.17`，它声明 `mcp[cli]>=1.3.0` **没有上限**
2. 于是装到 `mcp 2.x`，而 2.x 把 `FastMCP` 改名成 `MCPServer` → `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`
3. 加 `mcp<2` 后，`mcp 1.15+` 的 `FastMCP.__init__` 又不认 `description` 参数
4. 退到 `mcp 1.12.0` 后，又撞 `pydantic 2.12` 移除了 `eval_type_backport`

**唯一能同时满足的组合就是这三个一起锁：**

```json
{
  "mcpServers": {
    "sketchup": {
      "command": "<uvx 的绝对路径>",
      "args": [
        "--from", "sketchup-mcp==0.1.17",
        "--with", "mcp[cli]==1.12.0",
        "--with", "pydantic<2.12",
        "sketchup-mcp"
      ],
      "env": {
        "UV_INDEX_URL": "https://mirrors.aliyun.com/pypi/simple"
      }
    }
  }
}
```

改配置前先备份原文件。常见落点：WorkBuddy `~/.workbuddy/mcp.json`、Cursor `.cursor/mcp.json`、Claude Desktop 设置里的 JSON。

**检查点：** 单独跑一次下面这条，看到 `SketchupMCPServer ... starting up` 加一条「连不上 SketchUp」的 WARNING 就算对——这时连不上是**正常**的，因为第 4 步还没做。

```bash
uvx --from sketchup-mcp==0.1.17 --with "mcp[cli]==1.12.0" --with "pydantic<2.12" sketchup-mcp --help
```

---

## 4. 启动 SketchUp（别用 shell 子进程）

**这是 v1.0 完全没写、但最容易浪费半小时的一条。**

用 Agent 的 shell / `Start-Process` 启动的 GUI 进程，会随那条命令结束**被会话回收**。表现是：命令里查还活着，下一条命令查就没了——极像「崩溃」，会让你误删刚装好的扩展。

Windows 用 explorer 转一手，进程才独立：

```powershell
Start-Process -FilePath "C:\Windows\explorer.exe" -ArgumentList "`"<SketchUp.exe 绝对路径>`""
```

Mac：`open -a "SketchUp 2020"`。

**检查点：** 启动后单开一条命令查，进程还在 + 标题变成 `无标题.skp - SketchUp Pro 2020`，且 `netstat -ano | grep 9876` 有 LISTENING。三条都满足才往下走。

---

## 5. 一键验收

跑 `scripts/probe.py`，它会依次验：端口 → 握手取版本 → 建标准件 → 出 PNG，输出 JSON。

```bash
python scripts/probe.py --out ./probe.png
```

全绿才算打通。任一步失败 → 跳第 6 节对应分支。

**手验版**（一行一条）：

```python
# 建一个约 1 米的盒子（SketchUp 内部单位是英寸！1 m = 39.3701 in）
{"id":1,"command":"eval_ruby","parameters":{"code":"..."}}
```

**单位坑：** Ruby 里所有长度都是**英寸**。想要 1 米就写 `39.37`，写成 `1000` 会得到一根针。

**编码坑（中文用户必踩）：** 发给扩展的 Ruby 代码里**不要出现中文字面量**。socket 按字节读、不走声明编码，中文字符可能让整个脚本语法错。注释和返回值都用英文，用户看的是图不是日志。

---

## 6. 故障树

按症状查。详细版见 `references/troubleshooting.md`。

| 症状 | 原因 | 做法 |
|---|---|---|
| `ModuleNotFoundError: mcp.server.fastmcp` | 装到了 mcp 2.x | 按第 3 节锁 `mcp==1.12.0` |
| `FastMCP.__init__() got an unexpected keyword 'description'` | mcp ≥1.15 | 降到 `1.12.0` |
| `cannot import name 'eval_type_backport'` | pydantic ≥2.12 | 加 `pydantic<2.12` |
| SketchUp 启动后几秒消失、无崩溃日志 | 进程被 shell 会话回收 | 改用 `explorer.exe` 启动 |
| SketchUp 一启动就退、无任何日志 | `SKETCHUP_CONSOLE.show` | 打补丁 A |
| 9876 拒绝连接 | 没 Start Server / 进程没了 | 补丁 B；确认进程在 |
| 端口 LISTENING 但握手超时 | 上一请求没关闭连接 | 重连；单请求单连接 |
| 建模出来是根针 | 按毫米传了英寸 | 除以 25.4 |
| `tools/list` 返回 `Method not found` | 扩展本身不实现，由 Python 桥提供 | 走 MCP 客户端列工具；直连 TCP 时用 `eval_ruby` 探 |

---

## 7. 打通之后

**先看当前模型里有没有既有物体。有就新建，不要删用户的旧东西。** 遮挡视线的东西用 `hidden = true` 而不是删除，用户能自己恢复。

**⚠️ 配置生效需要重启客户端。** Agent 不能重启自己，所以配好 MCP 后当前会话里工具可能还没出现。此时有两条路：

1. 让用户重启客户端，之后用原生工具
2. **降级走 TCP 直连**（立刻可用，不等重启）：`scripts/su_eval.py` 往 `127.0.0.1:9876` 发一行 JSON

别因为「工具没出现」就判定没打通——端口通了就是通了。

扩展支持的指令：`create_component`(cube/cylinder/sphere/cone)、`delete_component`、`transform_component`、`get_selection`、`set_material`、`export`/`export_scene`(skp/obj/dae/stl/png/jpg)、`boolean_operation`(union/difference/intersection)、`chamfer_edges`、`fillet_edges`、`eval_ruby`。

**`eval_ruby` 是最强的**，其余工具不够用时直接写 Ruby。不要做榫卯、燕尾榫、指接——工具在包里，但这份 skill 不用。

---

## 8. 默认演示（用户没点名要建什么时）

按职业只做一件。用 `eval_ruby`，失败就留下盒子、截图、停。数字已是英寸。

⚠️ 本节三段代码 **v1.1 未实测**，来自 v1.0。跑不通就如实说，不要为了补全重装。

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

### B · 室内：一间房加桌子

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

### C · 景观：地面线 + 尺度人

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

做完 `export_scene` 出 PNG，然后停，问用户要做自己的还是再看另一个。

---

## 附：出图建议

`export_scene` 之外的稳妥写法（可直接 `eval_ruby`）：

```ruby
view = Sketchup.active_model.active_view
view.zoom_extents
view.write_image({filename: 'C:/path/out.png', width: 1600, height: 1600,
                  antialias: true, compression: 0.95})
```

- 输出路径用**纯 ASCII**，中文路径容易失败
- 出图前把背景调浅：`model.rendering_options['BackgroundColor'] = Sketchup::Color.new(247,249,251)`
- 模板自带的 2D 人物会挡画面，`hidden = true` 掉
