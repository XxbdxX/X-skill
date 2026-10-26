#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
向 SketchUp MCP 扩展发一段 Ruby 并取回结果（TCP 直连，不用 MCP 客户端）。

用途：MCP 配置改完但客户端还没重启时，这是唯一立刻可用的通道。

用法:
    python su_eval.py --code "Sketchup.version.to_s"
    python su_eval.py --file ./model.rb
    python su_eval.py --file ./model.rb --raw

注意:
    - 发给扩展的 Ruby 代码里不要写中文字面量（socket 按字节读，易踩编码）
    - SketchUp 内部单位是英寸，1 m = 39.3701 in
    - 单请求单连接，一个连接只处理一行 JSON
"""
import argparse
import json
import socket
import sys

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9876


def eval_ruby(code, host=DEFAULT_HOST, port=DEFAULT_PORT, timeout=120):
    s = socket.create_connection((host, port), timeout=timeout)
    try:
        payload = {"id": 1, "command": "eval_ruby",
                   "parameters": {"code": code}}
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


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--code", help="直接给一段 Ruby 表达式/脚本")
    g.add_argument("--file", help="从 .rb 文件读取")
    ap.add_argument("--host", default=DEFAULT_HOST)
    ap.add_argument("--port", type=int, default=DEFAULT_PORT)
    ap.add_argument("--timeout", type=int, default=120)
    ap.add_argument("--raw", action="store_true", help="打印原始 JSON 响应")
    args = ap.parse_args()

    code = args.code if args.code else open(
        args.file, encoding="utf-8").read()

    try:
        resp = eval_ruby(code, args.host, args.port, args.timeout)
    except ConnectionRefusedError:
        print(f"[X] 连不上 {args.host}:{args.port}", file=sys.stderr)
        print("    检查：SketchUp 是否在运行、扩展是否加载、是否 Start Server。",
              file=sys.stderr)
        return 2
    except socket.timeout:
        print("[X] 超时。可能是 Ruby 里抛了非 StandardError（如 SyntaxError），"
              "扩展没能回包。简化代码后再试。", file=sys.stderr)
        return 3

    if args.raw:
        print(resp)
        return 0

    try:
        d = json.loads(resp)
    except Exception:
        print(resp)
        return 0

    if "error" in d:
        print("[X] " + str(d["error"]), file=sys.stderr)
        return 1

    res = d.get("result", {})
    content = res.get("content") or []
    if content:
        print(content[0].get("text", ""))
    else:
        print(json.dumps(res, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
