#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
director_to_blueprint.py — 编导脚本 JSON → 剪映 edit-blueprint.json
====================================================================
融合层：把 video-director-breakdown 产出的「脚本 JSON」
（reference: script-json-schema.md）转换成 jianying-autoedit-agent
可直接消费的 edit-blueprint.json。

两种素材映射方式：
  1) 显式:   --map "shot-1=素材0,0,6.5;shot-2=素材1,0,14.4"  (shot=源索引,source_in,source_out)
  2) 自动:   不传 --map，则按 shots 顺序依次使用 --素材 里的第 N 个文件，
             每段 source_in=0, source_out=min(该素材时长, 该shot时长)

用法：
  python3 director_to_blueprint.py <脚本JSON> \
      --素材 /abs/m0.mp4 /abs/m1.mp4 ... \
      [--map "shot-1=0,0,6.5;..."] \
      [--name 项目名] [--width 1080 --height 1920] \
      [--duration-shots]  # 用shots自带的timeline时长作为每个clip时长
      -o <edit-blueprint.json>
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def probe_duration(path: Path) -> float:
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
            capture_output=True, text=True,
        )
        return float(r.stdout.strip() or 0)
    except Exception:
        return 0.0


def parse_map(spec: str, shots: list[dict]) -> dict:
    """'shot-1=0,0,6.5;shot-2=1,0,14.4' -> {'shot-1': (0,0.0,6.5), ...}"""
    result: dict[str, tuple[int, float, float]] = {}
    if not spec:
        return result
    for token in spec.split(";"):
        token = token.strip()
        if not token or "=" not in token:
            continue
        shot_id, rest = token.split("=", 1)
        parts = rest.split(",")
        try:
            src_idx = int(parts[0])
            src_in = float(parts[1]) if len(parts) > 1 else 0.0
            src_out = float(parts[2]) if len(parts) > 2 else None
            result[shot_id.strip()] = (src_idx, src_in, src_out)
        except (ValueError, IndexError):
            continue
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description="编导脚本JSON → 剪映蓝图")
    ap.add_argument("script_json", type=Path, help="编导 skill 产出的脚本 JSON")
    ap.add_argument("--素材", nargs="+", default=[], help="源素材文件(绝对路径)")
    ap.add_argument("--map", default="", help="显式 shot→源 映射, 见文件头说明")
    ap.add_argument("--name", default=None, help="项目名(默认取脚本title)")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--duration-shots", action="store_true",
                    help="clip时长严格按shots自带的timeline时长(可能变速/有转场缺失)")
    ap.add_argument("-o", "--output", required=True, type=Path)
    args = ap.parse_args()

    script = json.loads(args.script_json.read_text(encoding="utf-8"))
    shots = script.get("shots", [])
    materials = [str(Path(m).expanduser().resolve()) for m in args.素材]
    name = args.name or script.get("title") or "从编导脚本生成"
    width = int(script.get("width", args.width))
    height = int(script.get("height", args.height))

    # 预探素材时长
    mat_dur = [probe_duration(Path(m)) for m in materials]
    mapping = parse_map(args.map, shots)

    clips = []
    captions = []
    cursor = 0.0
    notes = []
    for idx, shot in enumerate(shots):
        shot_id = str(shot.get("id", f"shot-{idx+1}"))
        tl_in = float(shot.get("timeline_in_seconds", cursor))
        tl_out = float(shot.get("timeline_out_seconds", tl_in + 3.0))
        if not args.duration_shots:
            # 默认每段紧接上一段, 用 shot 时长
            shot_dur = max(0.1, tl_out - tl_in)
            tl_in = cursor
            tl_out = cursor + shot_dur
        dur = tl_out - tl_in

        src_idx, src_in, src_out = None, 0.0, None
        if shot_id in mapping:
            src_idx, src_in, src_out = mapping[shot_id]
        elif materials:
            # 自动: 按顺序给素材
            src_idx = idx if idx < len(materials) else None

        if src_idx is None or src_idx >= len(materials):
            notes.append(f"{shot_id}: 缺源素材(待配)")
            cursor = tl_out
            continue

        src_path = materials[src_idx]
        max_dur = mat_dur[src_idx]
        if src_out is None:
            src_out = min(max_dur, src_in + dur)
        else:
            src_out = min(src_out, max_dur)
        # 源时长不足则按实际缩，保证 source_out<=max
        s_dur = max(0.1, src_out - src_in)

        clips.append({
            "id": shot_id,
            "media_type": "video",
            "source_path": src_path,
            "source_in_seconds": round(src_in, 4),
            "source_out_seconds": round(src_in + s_dur, 4),
            "timeline_in_seconds": round(tl_in, 4),
            "timeline_out_seconds": round(tl_in + s_dur, 4),
            "track_name": "VideoTrack",
            "purpose": str(shot.get("purpose", shot.get("visual", "")))[:120],
            "audio_policy": "keep_source_audio",
            "source_group": str(shot.get("source_group", "")) or f"src-{src_idx}",
            "confidence": float(shot.get("confidence", 0.8)),
        })
        # 字幕: 从 caption 字段
        cap = str(shot.get("caption", "")).strip()
        if cap:
            captions.append({
                "id": f"{shot_id}-cap",
                "text": cap,
                "start_time_seconds": round(tl_in, 4),
                "duration_seconds": round(dur, 4),
                "track_name": "Subtitles",
            })
        cursor = tl_out

    blueprint = {
        "schema_version": "jianying-1.0",
        "project": {
            "name": name,
            "width": width,
            "height": height,
            "target_duration_seconds": round(cursor, 2),
        },
        "clips": clips,
        "narration": [],
        "music": [],
        "captions": captions,
        "effects": [],
        "transitions": [],
        "notes": notes + ["由 director_to_blueprint 从编导脚本生成"],
    }

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(blueprint, ensure_ascii=False, indent=2),
                           encoding="utf-8")
    print(f"✅ 已生成蓝图: {args.output}")
    print(f"   clips={len(clips)} captions={len(captions)} 总时长={cursor:.1f}s")
    print(f"   画布={width}x{height} 项目名={name}")
    if notes:
        print("   ⚠️ 待配素材:")
        for n in notes:
            print(f"      - {n}")
    return 0


if __name__ == "__main__":
    sys.exit(main())  # noqa: F821  (needs import sys)
