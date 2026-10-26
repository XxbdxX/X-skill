# 对随包扩展做的改动（PATCHES）

v1.1 在 Windows 11 + SketchUp 2020 (20.1.229) 实测时，对 `extension/` 里的原始文件做了 2 处修改。
原始文件来自 `mhyrr/sketchup-mcp`（MIT）。这里记录改了什么、为什么，方便上游更新后重新套用。

> 本 PR 已把打好补丁的 `main.rb` / `su_mcp.rb` 直接放进 `extension/` 作为随包文件，
> 落地即带补丁，不需要使用者再手改一遍。
> 上游原文看本仓库的 git 历史（本 PR 的父提交），不另存 `.orig` 副本。

---

## 补丁 A · `su_mcp/main.rb` 移除启动期打开 Ruby 控制台

### 位置 1：文件头（约 L6–L7）

```ruby
# 原
puts "MCP Extension loading..."
SKETCHUP_CONSOLE.show rescue nil

# 改
puts "MCP Extension loading..."
# [PATCH] 启动期调用 SKETCHUP_CONSOLE.show 会让 SketchUp 2020 无提示退出
```

### 位置 2：`Server#initialize`（约 L17–L26）

```ruby
# 原
# Try multiple ways to show console
begin
  SKETCHUP_CONSOLE.show
rescue
  begin
    Sketchup.send_action("showRubyPanel:")
  rescue
    UI.start_timer(0) { SKETCHUP_CONSOLE.show }
  end
end

# 改
# [PATCH] 移除启动期打开控制台的三种尝试（SketchUp 2020 会崩溃）
@log_path = File.join(File.dirname(__FILE__), 'mcp_server.log')
```

### 位置 3：`Server#log`（约 L29–L36）

```ruby
# 原
def log(msg)
  begin
    SKETCHUP_CONSOLE.write("MCP: #{msg}\n")
  rescue
    puts "MCP: #{msg}"
  end
  STDOUT.flush
end

# 改
def log(msg)
  begin
    File.open(@log_path, 'a') { |f| f.puts("[#{Time.now.strftime('%H:%M:%S')}] #{msg}") }
  rescue
  end
  puts "MCP: #{msg}"
end
```

### 为什么

`SKETCHUP_CONSOLE.show` 在扩展**加载期**调用，SketchUp 2020 会直接退出：

- 不是 Ruby 异常 → `rescue` 拦不住
- 不写任何日志、不留崩溃事件 → 排查时完全没线索
- 现象是「SketchUp 启动一下就没了」，极易误判成扩展文件损坏

改成写文件后，日志在 `Plugins/su_mcp/mcp_server.log`，出问题能直接看。

### 副作用

Ruby 控制台不再自动弹出。需要时手动 `Window > Ruby Console` 打开。
对 Agent 场景无影响（本来也不靠人看控制台）。

---

## 补丁 B · `su_mcp.rb` 自动 Start Server

### 位置：`register_extension` 之后

```ruby
Sketchup.register_extension(ex, true)
file_loaded(__FILE__)

# [PATCH] 自动启动 MCP Server，省去每次手点 Plugins > MCP Server > Start Server
UI.start_timer(3.0, false) {
  begin
    srv = (defined?(SU_MCP) ? SU_MCP.instance_variable_get(:@server) : nil)
    srv.start if srv && !srv.instance_variable_get(:@running)
  rescue
  end
}
```

### 为什么

原版要求用户手点菜单。但在 Agent 场景下，Agent **点不了 GUI 菜单**——这等于流程断在这里，除非每次都让人来点一下。

3 秒延迟是为了等模型窗口初始化完成（加载期直接起服务时窗口还没就绪）。

### 副作用

打开 SketchUp 就会占用 9876。如果同时开两个 SketchUp 实例，第二个的 `TCPServer.new` 会抛 `EADDRINUSE`，被 `rescue` 吞掉，第二个实例就没服务。
单实例使用无影响。要多实例需要给每个实例不同端口（原版写死 9876，需要改）。

---

## 未修改但值得知道的地方

| 位置 | 现象 | 说明 |
|---|---|---|
| `handle_jsonrpc_request` | 不支持 `tools/list` | 工具清单由 Python 桥定义，扩展只实现 `tools/call` / `resources/list` / `prompts/list` |
| `rescue StandardError` | `SyntaxError` 不会被捕获 | Ruby 代码有语法错时，客户端会**干等到超时**而不是收到错误 |
| 连接模型 | 单请求单连接 | `client.gets` 读一行即处理并关闭，批量请求要一条一个连接 |
| `@port = 9876` | 写死 | 想换端口要改源码，没有环境变量入口（对比 Rhino MCP 有 `RHINO_MCP_PORT`） |
