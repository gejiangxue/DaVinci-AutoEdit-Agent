#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
run_dsh.py — jianying-autoedit-agent 的 DSH 一键入口
=====================================================
把 skill 的「扫描 → 抽帧 → 蓝图 → 建草稿 → 审计」串成一条命令，
在 DSH 环境（有 ffmpeg + jianying-editor + 本地视觉桥）下开箱即用。

用法：
  python3 run_dsh.py <素材路径或目录> [多个] \
      --name "项目名" \
      [--width 1080 --height 1920] \
      [--blueprint 已有蓝图.json]
"""
from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

# 本脚本位于 <skill>/scripts/ 下
SCRIPTS = Path(__file__).resolve().parent
SKILL = SCRIPTS.parent


def run(cmd, **kw):
    print("  $", " ".join(str(c) for c in cmd))
    r = subprocess.run([str(c) for c in cmd], capture_output=True, text=True, **kw)
    if r.stdout:
        print(r.stdout)
    if r.stderr:
        sys.stderr.write(r.stderr[-500:])
    return r


def main() -> int:
    ap = argparse.ArgumentParser(description="jianying-autoedit-agent DSH 一键入口")
    ap.add_argument("media", nargs="+", help="素材路径/目录（可多个）")
    ap.add_argument("--name", default="DSH_自动剪辑", help="项目名(草稿名)")
    ap.add_argument("--run", default=".dsh_run", help="运行工作目录")
    ap.add_argument("--width", type=int, default=1080)
    ap.add_argument("--height", type=int, default=1920)
    ap.add_argument("--blueprint", default=None, help="已有蓝图则跳过前几步只用建草稿")
    ap.add_argument("--only-build", action="store_true",
                    help="只用已有 --blueprint 建草稿(跳过扫描/分析)")
    ap.add_argument("--stage-media", action="store_true",
                    help="建草稿前把蓝图素材复制到剪映可访问目录并改写蓝图路径,规避‘链接媒体’")
    args = ap.parse_args()

    run_dir = Path(args.run) / args.name
    run_dir.mkdir(parents=True, exist_ok=True)

    # ---- 环境检查 ----
    print("== ① check_setup ==")
    r = run([sys.executable, str(SCRIPTS / "check_setup.py")])
    if r.returncode != 0:
        print("⚠️ 环境检查未全通过，但仍继续（部分为可选依赖）")

    # ---- 蓝图 ----
    blueprint_path = Path(args.blueprint) if args.blueprint else run_dir / "edit-blueprint.json"
    if args.only_build:
        if not blueprint_path.exists():
            print(f"❌ --only-build 需要蓝图: {blueprint_path}")
            return 1
    else:
        print("\n== ② scan_media ==")
        scan_out = run_dir / "scan"
        cmd = [sys.executable, str(SCRIPTS / "scan_media.py")]
        for m in args.media:
            cmd += ["--input", str(Path(m).expanduser().resolve())]
        cmd += ["--output", str(scan_out)]
        run(cmd)
        manifest = scan_out / "media-manifest.json"
        if not manifest.exists():
            print("❌ 扫描未产出 media-manifest.json")
            return 1
        # 列出素材概览
        rows = json.loads(manifest.read_text(encoding="utf-8"))
        print(f"\n📦 扫描到 {len(rows)} 个素材:")
        for row in rows[:20]:
            probe = row.get("probe", {})
            w = probe.get("streams", [{}])[0] if probe.get("streams") else {}
            print(f"  [{row['media_type']}] {Path(row['path']).name} "
                  f"{w.get('width','?')}x{w.get('height','?')} "
                  f"{probe.get('format',{}).get('duration',0):.1f}s")

        print("\n③ 提示: 抽帧 -> 用 DSH 视觉桥分析 -> 生成蓝图(edit-blueprint.json)")
        print("   (可用 extract_frames.py 抽帧, analyze_frames_dsh.py 配合视觉桥)")
        print(f"   蓝图应写入: {blueprint_path}")
        print("   确认蓝图后, 重新运行本命令加 --only-build --blueprint <蓝图> 建草稿")
        return 0

    # ---- 媒体中转(规避剪映沙盒无权限访问 ~/Documents) ----
    if args.stage_media:
        print("\n== ③.5 stage-media: 复制素材到剪映目录 ==")
        jy_media = Path("/Users/lxy/Movies/JianyingPro/User Data/Projects/素材_jianying")
        jy_media.mkdir(parents=True, exist_ok=True)
        bp = json.loads(blueprint_path.read_text(encoding="utf-8"))
        remap = {}
        for clip in bp.get("clips", []):
            sp = clip.get("source_path", "")
            if not sp:
                continue
            src = Path(sp)
            if not src.exists():
                print(f"  ⚠️ 素材不存在(跳过): {src}")
                continue
            # 拷贝到剪映目录(保留同名)
            dest = jy_media / src.name
            if dest.exists() and dest.stat().st_size == src.stat().st_size:
                pass
            else:
                import shutil
                print(f"  + 复制 {src.name}")
                shutil.copy2(str(src), str(dest))
            remap[str(src)] = str(dest)
        if remap:
            for clip in bp.get("clips", []):
                sp = clip.get("source_path", "")
                if sp in remap:
                    clip["source_path"] = remap[sp]
            staged_bp = run_dir / "edit-blueprint.staged.json"
            staged_bp.write_text(json.dumps(bp, ensure_ascii=False, indent=2), encoding="utf-8")
            print(f"  ✅ 已改写蓝图素材路径到剪映目录, 存到: {staged_bp.name}")
            blueprint_path = staged_bp

    # ---- 建草稿 ----
    print(f"\n== ④ build_jianying_draft ==")
    report = run_dir / "build-report.json"
    cmd = [sys.executable, str(SCRIPTS / "build_jianying_draft.py"),
           str(blueprint_path), "--report", str(report),
           "--project-name", args.name]
    run(cmd)
    if not report.exists():
        print("❌ 未产出 build-report.json")
        return 1
    rep = json.loads(report.read_text(encoding="utf-8"))
    print(f"\n📋 build 结果: status={rep.get('status')} "
          f"clips={rep.get('added',{}).get('clips')} "
          f"captions={rep.get('added',{}).get('captions')} errors={len(rep.get('errors',[]))}")
    return 0 if rep.get("save", {}).get("status") == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
