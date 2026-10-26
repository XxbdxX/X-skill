#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
SketchUp MCP 扩展一键自检 / one-shot health probe.

依次验证：端口 → 握手取版本 → 建标准件 → 出 PNG。
输出 JSON，退出码 0 = 全通过。

用法:
    python probe.py
    python probe.py --out ./probe.png --keep
    python probe.py --host 127.0.0.1 --port 9876
"""
import argparse
import json
import os
import socket
import sys
import time

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876

# SketchUp Ruby 内部单位是英寸，1 m = 39.3701 in
CUBE_IN = 39.3701


def rpc(payload, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=60):
    """单请求单连接。扩展读完一行就关闭。"""
    s = socket.create_connection((host, port), timeout=timeout)
    try:
        s.sendall((json.dumps(payload, ensure_ascii=False) + "\n").encode("utf-8"))
        buf = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\n"):
                break
        return buf.decode("utf-8", errors="replace").strip()
    finally:
        s.close()


def eval_ruby(code, rid=1, host=DEFAULT_HOST, port=DEFAULT_PORT):
    return rpc({"id": rid, "command": "eval_ruby",
                "parameters": {"code": code}}, host, port)


def text_of(resp):
    """从 JSON-RPC 响应里取出 text 字段。"""
    try:
        d = json.loads(resp)
    except Exception:
        return None, "响应不是 JSON: " + resp[:200]
    if "error" in d:
        return None, d["error"].get("message", "unknown error")
    res = d.get("result", {})
    if res.get("isError"):
        return None, json.dumps(res, ensure_ascii=False)[:300]
    content = res.get("content") or []
    if content and isinstance(content, list):
        return content[0].get("text", ""), None
    return json.dumps(res, ensure_ascii=False)[:300], None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--out", default=None, help="PNG 输出路径（纯 ASCII 更稳）")
    ap.add_argument("--keep", action="store_true", help="保留探针建的盒子")
    args = ap.parse_args()

    # 输出路径兜底：默认写到临时目录，避免中文路径
    out = args.out or os.path.join(
        os.environ.get("TEMP", "/tmp"), "sketchup_probe.png")
    out = out.replace("\\", "/")

    steps = []
    ok_all = True

    def add(name, ok, detail):
        nonlocal ok_all
        steps.append({"step": name, "ok": ok, "detail": str(detail)[:500]})
        if not ok:
            ok_all = False

    # ---- 1. 端口 ----
    t0 = time.time()
    try:
        s = socket.create_connection((args.host, args.port), timeout=5)
        s.close()
        add("port", True, f"{args.host}:{args.port} 可连 ({int((time.time()-t0)*1000)} ms)")
    except Exception as e:
        add("port", False, f"连不上 {args.host}:{args.port} → {e}")
        print(json.dumps({"ok": False, "steps": steps}, ensure_ascii=False, indent=2))
        print("\n提示: 扩展没加载 / 没 Start Server / SketchUp 进程被回收了。"
              "见 references/troubleshooting.md", file=sys.stderr)
        return 1

    # ---- 2. 握手 ----
    try:
        raw = eval_ruby("Sketchup.version.to_s + '|' + Sketchup.active_model.title", 2,
                        args.host, args.port)
        txt, err = text_of(raw)
        if err:
            add("handshake", False, err)
        else:
            add("handshake", True, f"SketchUp {txt}")
    except Exception as e:
        add("handshake", False, f"握手失败 → {e}")

    if not ok_all:
        print(json.dumps({"ok": False, "steps": steps}, ensure_ascii=False, indent=2))
        return 1

    # ---- 3. 建标准件（1 米立方体）----
    build = f"""
model = Sketchup.active_model
model.start_operation('Probe', true)
ents = model.active_entities
g = ents.add_group
g.name = '__probe_cube__'
f = g.entities.add_face([0,0,0],[{CUBE_IN},0,0],[{CUBE_IN},{CUBE_IN},0],[0,{CUBE_IN},0])
f.pushpull({CUBE_IN})
model.commit_operation
bb = g.bounds
"cube ok | %.3fm x %.3fm x %.3fm | solid=#{{g.manifold?}}" % [
  bb.width * 0.0254, bb.height * 0.0254, bb.depth * 0.0254]
"""
    try:
        raw = eval_ruby(build, 3, args.host, args.port)
        txt, err = text_of(raw)
        add("build_cube", err is None, txt if not err else err)
    except Exception as e:
        add("build_cube", False, f"建模失败 → {e}")

    if not ok_all:
        print(json.dumps({"ok": False, "steps": steps}, ensure_ascii=False, indent=2))
        return 1

    # ---- 4. 出图 ----
    shot = f"""
model = Sketchup.active_model
view  = model.active_view
g = nil
model.entities.each {{ |e| g = e if e.is_a?(Sketchup::Group) && e.name == '__probe_cube__' }}
view.zoom_extents
model.rendering_options['BackgroundColor'] = Sketchup::Color.new(247,249,251)
ok = view.write_image({{filename: '{out}', width: 1200, height: 1200,
                        antialias: true, compression: 0.95}})
ok.to_s
"""
    try:
        raw = eval_ruby(shot, 4, args.host, args.port)
        txt, err = text_of(raw)
        made = (err is None and txt and txt.strip().lower() == "true"
                and os.path.exists(out))
        add("export_png", made, f"{out} | 返回值={txt!r} | 文件存在={os.path.exists(out)}")
    except Exception as e:
        add("export_png", False, f"出图失败 → {e}")

    # ---- 清理探针物件（除非 --keep）----
    if not args.keep:
        try:
            eval_ruby("""
model = Sketchup.active_model
victims = []
model.entities.each { |e| victims << e if e.is_a?(Sketchup::Group) && e.name == '__probe_cube__' }
model.start_operation('Probe cleanup', true)
victims.each { |v| v.erase! }
model.commit_operation
"cleaned #{victims.size}"
""", 5, args.host, args.port)
        except Exception:
            pass

    result = {"ok": ok_all, "sketchup_png": out if os.path.exists(out) else None,
              "steps": steps}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
