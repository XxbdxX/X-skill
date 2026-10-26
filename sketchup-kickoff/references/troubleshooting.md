# 故障树 · SketchUp 打通

按**症状**查。每条都是 v1.1 实测踩过的。

---

## A. 起桥阶段（`uvx sketchup-mcp` 自己就报错）

### A1. `ModuleNotFoundError: No module named 'mcp.server.fastmcp'`

**原因**：装到了 `mcp 2.x`。2.x 把 `FastMCP` 改名 `MCPServer`，模块也搬了。
`sketchup-mcp 0.1.17` 声明 `mcp[cli]>=1.3.0`，**没有上限**，于是被拉到 2.x。

**做法**：锁版本。

```bash
uvx --from sketchup-mcp==0.1.17 --with "mcp[cli]==1.12.0" --with "pydantic<2.12" sketchup-mcp --help
```

### A2. `TypeError: FastMCP.__init__() got an unexpected keyword argument 'description'`

**原因**：在 A1 基础上只加了 `mcp<2`，装到 `mcp 1.15+`。这些版本 `FastMCP` 已不接受 `description`。

**做法**：降到 `1.12.0`（见 A1 的命令）。

### A3. `ImportError: cannot import name 'eval_type_backport' from 'pydantic._internal._typing_extra'`

**原因**：`pydantic ≥ 2.12` 移除了这个内部函数，而 `mcp 1.x` 还在用。

**做法**：加 `--with "pydantic<2.12"`。

> **三个错误是连锁的，必须一次锁死三个包。** 只修其中一个会掉进下一个。

### A4. 版本矩阵速查

| sketchup-mcp | mcp | pydantic | 结果 |
|---|---|---|---|
| 0.1.17 | 2.x | any | ❌ A1 |
| 0.1.17 | 1.15+ | any | ❌ A2 |
| 0.1.17 | 1.3–1.12 | ≥2.12 | ❌ A3 |
| **0.1.17** | **1.12.0** | **<2.12** | ✅ 实测可用 |

> 换 `sketchup-mcp` 版本要重测这张表。上游哪天给依赖加上限，这里就能放宽。

---

## B. SketchUp 进程阶段

### B1. 启动后几秒就没了，任务管理器里查无此进程，**事件日志也没有崩溃记录**

**原因**：不是崩溃。是用 Agent 的 shell / `Start-Process` 启动的 GUI 进程**跟着那条命令一起被会话回收**了。表现极具误导性——命令里查还活着，下一条命令查就没了。

**做法**：Windows 用 explorer 转一手，进程才独立于会话：

```powershell
Start-Process -FilePath "C:\Windows\explorer.exe" -ArgumentList "`"D:\...\SketchUp.exe`""
```

Mac：`open -a "SketchUp 2020"`。

**判据**：启动后**单独开一条命令**查，进程仍在 + 标题是 `无标题.skp - SketchUp Pro 2020`。

### B2. 启动后立刻消失，扩展刚装好，**连欢迎窗口都看不到完整**

**原因**：扩展 `main.rb` 加载期调用 `SKETCHUP_CONSOLE.show`，SketchUp 2020 会无提示退出。

**做法**：见 SKILL.md 补丁 A。主文件有 3 处（约 L7、L19、L24）。

**为什么没有错误提示**：这是原生层退出，不是 Ruby 异常，`rescue` 拦不住，也不写日志。

### B3. 想确认扩展到底加载没加载

在 `su_mcp.rb` 最前面临时插一段探针：

```ruby
begin
  File.open('C:/temp/load_probe.log', 'a') { |f| f.puts("[#{Time.now}] loaded") }
rescue
end
```

重启后看文件在不在。用完删掉。

---

## C. 连接阶段（进程在、但不通）

### C1. `ConnectionRefusedError: [WinError 10061]`

按顺序查：

1. SketchUp 没开 → 开
2. 进程在但没 Start Server → 打补丁 B，或手动点 Plugins → MCP Server → Start Server
3. 扩展没拷全（只拷了 `main.rb`，缺 `su_mcp.rb`）→ 补齐
4. 装了扩展但没重启 SketchUp → 重启
5. 端口被别的程序占 → `netstat -ano | findstr 9876`

判据：`netstat -ano | grep 9876` 出现 `LISTENING`。

### C2. 端口 LISTENING，但发请求没响应 / 超时

**原因 1**：Ruby 代码里有 `SyntaxError` 或非 `StandardError` 的异常。扩展只 `rescue StandardError`，这类错误会让它**回不了包**，客户端干等到超时。

→ 把代码拆短，逐步试，定位是哪一句。

**原因 2**：一次连接发了多个请求。扩展是**单请求单连接**，读完一行就关。批量请求要一条一个连接。

### C3. `tools/list` 返回 `Method not found`

**不是故障。** 扩展本身只实现 `tools/call`、`resources/list`、`prompts/list`。工具清单是 Python 桥（`sketchup-mcp`）那层定义的。

- 走 MCP 客户端 → 能正常列工具
- 直连 TCP → 没有 `tools/list`，用 `eval_ruby` 探活

---

## D. 建模阶段

### D1. 建出来的东西是根针 / 尺寸差 25 倍

**原因**：SketchUp Ruby 内部单位是**英寸**。传了毫米数。

| 想要 | 传什么 |
|---|---|
| 1 m | `39.3701` |
| 3 m 层高 | `118.11` |
| 100 mm | `3.937` |

### D2. 脚本明明没中文，还是报编码错 / 语法错

**原因**：发给扩展的 Ruby 里混了中文字面量。socket 按字节读、不走声明编码，多字节字符可能让整段脚本解析失败。

**做法**：注释、`puts`、返回值全用英文。中文只放在**返回给用户之前的 Python 侧**。

### D3. 面朝内、渲染发黑

**原因**：`add_face` 的顶点顺序决定法线方向。

**做法**：建完统一修正。

```ruby
origin = Geom::Point3d.new(0, 0, 0)
ents.grep(Sketchup::Face).each do |f|
  f.reverse! if f.normal.dot(f.bounds.center - origin) < 0
end
```

（`origin` 换成实际体心。）

### D4. `grp.manifold?` 返回 false

不是闭合实体。常见原因：面没缝合（顶点有微小偏差）、重复面、少一个面。

多面体类形体先查欧拉公式：`V - E + F = 2`。

> 注意：`entities.grep(Sketchup::Vertex)` **恒为 0**，因为 Entities 迭代不含 Vertex。要从 Edge 收集：
> `vs = {}; entities.grep(Sketchup::Edge).each { |e| vs[e.start] = 1; vs[e.end] = 1 }; vs.size`

---

## E. 出图阶段

### E1. `write_image` 返回 true 但文件不存在

**原因**：路径含中文，或目录不存在。

**做法**：输出到纯 ASCII 路径（如 `%TEMP%`），成功后再由 Python 侧复制到中文目录。

### E2. 图里混进模板自带的 2D 人物

**做法**：出图前把非目标实体隐藏，**不要删**（用户可能还要）。

```ruby
entities.each do |e|
  next if e.is_a?(Sketchup::Group) && e.name == 'Target'
  e.hidden = true
end
```

### E3. 构图偏、主体不居中

先隐藏干扰物再 `view.zoom_extents`——`zoom_extents` 会把隐藏对象排除在外。顺序反了就会连人物一起框进去。

---

## F. 配置生效阶段

### F1. MCP 配置写好了，但 Agent 里没有 `sketchup` 的工具

**原因**：MCP 配置只在客户端**启动时**读取。Agent 不能重启自己。

**做法**（两条都行）：

1. 让用户重启客户端 → 之后走原生工具
2. **立刻可用**：`scripts/su_eval.py` 直连 TCP

别因为工具没出现就判定"没打通"。**端口通了就是通了。**

---

## G. 通用排查顺序

```
1. tasklist | grep SketchUp        → 进程在？
2. netstat -ano | grep 9876        → LISTENING？
3. su_eval.py --code "1+1"         → 握手通？
4. su_eval.py --code "Sketchup.version"  → 拿到版本？
5. probe.py                        → 建件+出图？
```

前一步不过，别跳下一步。第 3 步就挂了，问题一定在 B 或 C。
