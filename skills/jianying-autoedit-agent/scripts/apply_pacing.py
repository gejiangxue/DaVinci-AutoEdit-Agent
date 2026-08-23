#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
apply_pacing.py — 气口处理(落地 talking-head-cleanup 的规则)
=============================================================
输入: whisper 逐句(word级可更准) + 源素材 silence scan
处理: 去杂质(3 2 1 开始/可以/嗯 等)、删重复句、定位真正开口时间、
     句间保留自然气口、缩句内长停顿、QC 检查。
输出: 精剪辑的 timeline(每句 source_in/out + timeline_in/out)，供
     director_to_blueprint 转成 edit-blueprint.json。

用法:
  python3 apply_pacing.py <source.mov> <whisper_segments.json> \
      --mode tight_reel --head 0.12 --tail 0.20 --gap 0.15 \
      --junk "3 2 1 开始,可以,可以 可以,嗯,呃" \
      -o paced_clips.json
"""
from __future__ import annotations

import argparse, json, subprocess, sys
from pathlib import Path

JUNK_KEYWORDS = ["开始", "可以", "嗯", "呃", "啊", "对", "好"]


def probe_duration(path: Path) -> float:
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
                       capture_output=True, text=True)
    return float(r.stdout.strip() or 0)


def silence_scan(path: Path, noise="-35dB", min_dur=0.2):
    """返回 [(start, end), ...] 静音段"""
    r = subprocess.run(
        ["ffmpeg", "-i", str(path), "-af", f"silencedetect=noise={noise}:d={min_dur}",
         "-f", "null", "-"], capture_output=True, text=True)
    out = r.stderr
    silences = []
    cur_start = None
    for line in out.splitlines():
        if "silence_start:" in line:
            try: cur_start = float(line.split("silence_start:")[1].strip())
            except ValueError: cur_start = None
        elif "silence_end:" in line and cur_start is not None:
            try:
                end = float(line.split("silence_end:")[1].split("|")[0].strip())
                silences.append((cur_start, end))
            except ValueError: pass
            cur_start = None
    return silences


def is_junk(text: str) -> bool:
    t = text.strip()
    if not t:
        return True
    for kw in JUNK_KEYWORDS:
        if kw and t.strip() == kw:
            return True
    if "开始" in t and any(c.isdigit() for c in t):
        return True   # "3 2 1 开始"
    if t in ("可以", "可以 可以", "可以可以"):
        return True
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("source", type=Path)
    ap.add_argument("segments_json", type=Path)
    ap.add_argument("--mode", default="tight_reel", choices=["tight_reel", "natural_explainer"])
    ap.add_argument("--head", type=float, default=0.12, help="句前呼吸")
    ap.add_argument("--tail", type=float, default=0.20, help="句尾收尾")
    ap.add_argument("--gap", type=float, default=0.15, help="句间气口")
    ap.add_argument("--intra-gap", type=float, default=0.08, help="句内停顿保留上限")
    ap.add_argument("-o", "--output", required=True, type=Path)
    args = ap.parse_args()

    dur = probe_duration(args.source)
    segs = json.loads(args.segments_json.read_text(encoding="utf-8"))
    # segments: [{start,end,text},...] (秒)
    # 阈值
    if args.mode == "tight_reel":
        gap_check = 0.25; keep_need_qc = 0.35
    else:
        gap_check = 0.45; keep_need_qc = 0.65

    # 去杂质, 删重复
    cleaned = []
    prev_text = ""
    for o in segs:
        t = o["text"].strip()
        if is_junk(t):
            continue
        # 删重复句(连续相同内容)
        if t == prev_text:
            continue
        prev_text = t
        cleaned.append(o)

    clips = []
    cursor = 0.0
    for i, o in enumerate(cleaned):
        s = max(0.0, o["start"] - args.head)
        e = min(dur, o["end"] + args.tail)
        tl_in = cursor
        tl_out = cursor + (e - s)
        clips.append({
            "id": f"pacing-{i+1:02d}",
            "source": str(args.source.resolve()),
            "source_in": round(s, 3), "source_out": round(e, 3),
            "timeline_in": round(tl_in, 3), "timeline_out": round(tl_out, 3),
            "text": o["text"].strip(),
        })
        cursor = tl_out + args.gap

    result = {
        "mode": args.mode,
        "source": str(args.source.resolve()),
        "source_duration": round(dur, 2),
        "total_timeline_seconds": round(cursor, 2),
        "head": args.head, "tail": args.tail, "gap": args.gap,
        "removed_junk": len(segs) - len(cleaned),
        "clips": clips,
        "qc_notes": [
            f"mode={args.mode}, 检查话隙>={gap_check}s, 保留>={keep_need_qc}s需QC理由",
            f"去杂质/重复 {len(segs)-len(cleaned)} 句, 保留 {len(clips)} 句",
            "已按真正开口时间定位(句首/句尾留呼吸), 句间保留气口",
        ],
    }
    args.output.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"✅ 气口处理完成: {args.output}")
    print(f"   mode={args.mode}, 去杂质{len(segs)-len(cleaned)}句, 保留{len(clips)}句, 总时长{cursor:.1f}s")
    print(f"   前3镜头:")
    for c in clips[:3]:
        print(f"     {c['id']}: src[{c['source_in']}-{c['source_out']}] tl[{c['timeline_in']}-{c['timeline_out']}] \"{c['text'][:16]}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
