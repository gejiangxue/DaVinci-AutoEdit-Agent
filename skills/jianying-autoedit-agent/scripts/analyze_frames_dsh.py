#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
analyze_frames_dsh.py — DSH 版帧视觉分析
==========================================
替代 skill 原生的 analyze_frames.py（它依赖 LLM_API_KEY）。
DSH 用本地视觉桥 modlens（modlens_read_image）读取画面，输出与
analyze_frames.py 兼容的 JSONL，以便下游 skill 流程直接消费。

用法（与原生脚本一致的输入）：
  python3 analyze_frames_dsh.py \
      --frames-index "<run>/review/frames/frames-index.json" \
      --output "<run>/review/frame-analysis.jsonl" \
      --topic "全食展"

说明：DSH 视觉桥在 agent 运行时调用，无法在本脚本纯 Python 里直接发起。
因此本脚本产出【待分析清单】+ 每帧的 base64 元数据，真正读图由 agent 用
modlens_read_image 完成后再回填。为兼容批量流程，这里默认生成一个
【帧清单】让 agent 用视觉桥逐帧读取，并提供一个合并器。
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    ap = argparse.ArgumentParser(description="DSH 版帧视觉分析（本地视觉桥）")
    ap.add_argument("--frames-index", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--topic", required=True)
    ap.add_argument("--mode", default="list",
                    help="list=输出待读帧清单; merge=把 agent 回填的 analysis 合并成 JSONL")
    ap.add_argument("--analysis-input", default="",
                    help="mode=merge 时, 传 agent 用 modlens 读后写回的 JSON 文件路径")
    args = ap.parse_args()

    rows = json.loads(args.frames_index.read_text(encoding="utf-8"))
    rows = [r for r in rows if r.get("ok")]

    args.output.parent.mkdir(parents=True, exist_ok=True)

    if args.mode == "merge":
        # agent 用 modlens 读完后, 把每帧的分析结果写回 analysis_input(JSON数组)
        if not args.analysis_input or not Path(args.analysis_input).exists():
            print("❌ merge 模式需要 --analysis-input 指向 agent 回填的 JSON")
            return 1
        filled = json.loads(Path(args.analysis_input).read_text(encoding="utf-8"))
        # filled: [{"image_path": "...", "analysis": {...}}, ...]
        by_path = {f["image_path"]: f.get("analysis", {}) for f in filled}
        with args.output.open("w", encoding="utf-8") as h:
            for row in rows:
                analysis = by_path.get(row.get("image_path"), {})
                h.write(json.dumps({**row, "analysis": analysis,
                                    "error": "" if analysis else "pending-visual-bridge"},
                                   ensure_ascii=False) + "\n")
        print(f"✅ 已合并 {len(rows)} 帧分析 -> {args.output}")
        return 0

    # list 模式: 输出待读帧清单 + 提示
    print(f"DSH 视觉桥待分析 {len(rows)} 帧。请用 modlens_read_image 逐帧读取，"
          f"每帧输出 JSON: description, visible_text, people, actions, setting, "
          f"emotion, technical_quality, suggested_uses, tags。")
    print(f"读取完成后存为 <output>.filled.json，再执行 --mode merge。")
    manifest = [{"image_path": r["image_path"], "index": r.get("index"),
                 "topic": args.topic} for r in rows]
    with args.output.open("w", encoding="utf-8") as h:
        json.dump(manifest, h, ensure_ascii=False, indent=2)
    print(f"✅ 待读帧清单 -> {args.output}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
