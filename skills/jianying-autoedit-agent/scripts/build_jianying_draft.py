from __future__ import annotations

import argparse
import importlib
import json
import os
import sys
from pathlib import Path
from typing import Any


def _candidate_skill_roots() -> list[Path]:
    project_root = Path(__file__).resolve().parents[3]
    current = Path.cwd().resolve()
    env_root = os.getenv("JY_SKILL_ROOT", "").strip()
    candidates = [
        Path(env_root) if env_root else None,
        current / ".agent/skills/jianying-editor",
        current / ".trae/skills/jianying-editor",
        current / ".claude/skills/jianying-editor",
        current / "skills/jianying-editor",
        project_root / "skills/jianying-editor",
        Path.home() / ".codex/skills/jianying-editor",
    ]
    return [p.resolve() for p in candidates if p]


def load_jy_project():
    attempted: list[str] = []
    for root in _candidate_skill_roots():
        scripts = root / "scripts"
        attempted.append(str(root))
        if (scripts / "jy_wrapper.py").exists():
            scripts_text = str(scripts)
            if scripts_text not in sys.path:
                sys.path.insert(0, scripts_text)
            try:
                module = importlib.import_module("jy_wrapper")
                return module.JyProject, root
            except Exception as exc:  # pragma: no cover - depends on local JianYing install
                raise RuntimeError(f"Found JianYing skill at {root}, but import failed: {exc}") from exc
    raise RuntimeError(
        "Could not find jianying-editor/scripts/jy_wrapper.py. Checked:\n- "
        + "\n- ".join(attempted)
    )


def seconds(value: Any) -> float:
    return float(value or 0)


def time_string(value: float) -> str:
    return f"{value:.6f}s"


def choose_start(project: Any, requested_seconds: float, track_name: str, cursors: dict[str, float]) -> str | None:
    cursor = cursors.get(track_name)
    if cursor is None:
        existing = project.get_track_duration(track_name)
        cursor = existing / 1_000_000 if existing else None
    if cursor is not None and abs(requested_seconds - cursor) <= 0.01:
        return None
    return time_string(requested_seconds)


def remember_end(project: Any, track_name: str, fallback_end: float, cursors: dict[str, float]) -> None:
    actual = project.get_track_duration(track_name)
    cursors[track_name] = actual / 1_000_000 if actual else fallback_end


def duration_for(item: dict[str, Any], start_key: str, end_key: str) -> float:
    if item.get("duration_seconds") is not None:
        return seconds(item["duration_seconds"])
    return max(0.0, seconds(item.get(end_key)) - seconds(item.get(start_key)))


def add_caption(project: Any, item: dict[str, Any], report: dict[str, Any], cursors: dict[str, float]) -> None:
    if item.get("srt_path"):
        importer = getattr(project, "import_srt", None)
        if not importer:
            report["unsupported"].append({"kind": "srt", "path": item["srt_path"], "reason": "wrapper has no import_srt"})
            return
        importer(str(Path(item["srt_path"]).expanduser().resolve()), track_name=item.get("track_name", "Subtitles"))
        return
    text = str(item.get("text", "")).strip()
    duration = duration_for(item, "start_time_seconds", "end_time_seconds")
    if not text or duration <= 0:
        report["errors"].append(f"caption {item.get('id', '<unnamed>')} needs text and positive duration")
        return
    track_name = item.get("track_name", "Subtitles")
    start_seconds = seconds(item.get("start_time_seconds"))
    project.add_text_simple(
        text=text,
        start_time=choose_start(project, start_seconds, track_name, cursors),
        duration=time_string(duration),
        track_name=track_name,
    )
    remember_end(project, track_name, start_seconds + duration, cursors)


def add_narration(project: Any, item: dict[str, Any], report: dict[str, Any], cursors: dict[str, float]) -> None:
    start_seconds = seconds(item.get("start_time_seconds"))
    track = item.get("track_name", "VoiceOver")
    start = choose_start(project, start_seconds, track, cursors)
    if item.get("audio_path"):
        path = Path(item["audio_path"]).expanduser().resolve()
        if not path.exists():
            report["errors"].append(f"missing narration audio: {path}")
            return
        project.add_audio_safe(str(path), start_time=start, duration=item.get("duration_seconds"), track_name=track)
        remember_end(project, track, start_seconds + seconds(item.get("duration_seconds")), cursors)
        if item.get("subtitle_text"):
            project.add_text_simple(
                text=str(item["subtitle_text"]),
                start_time=start,
                duration=time_string(seconds(item.get("duration_seconds"))),
                track_name=item.get("subtitle_track_name", "Subtitles"),
            )
        return
    text = str(item.get("text", "")).strip()
    if not text:
        report["errors"].append(f"narration {item.get('id', '<unnamed>')} needs text or audio_path")
        return
    project.add_narrated_subtitles(
        text=text,
        speaker=item.get("speaker", "zh_female_xiaopengyou"),
        start_time=start,
        track_name=item.get("subtitle_track_name", "Subtitles"),
    )


def set_volume(segment: Any, value: Any) -> None:
    if value is None:
        return
    try:
        segment.volume = float(value)
    except Exception:
        pass


def build(plan: dict[str, Any], args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    JyProject, skill_root = load_jy_project()
    project_config = plan.get("project", {})
    project_name = str(args.project_name or project_config.get("name") or "JianYing AutoEdit")
    width = int(project_config.get("width", 1920))
    height = int(project_config.get("height", 1080))
    drafts_root = Path(args.drafts_root or os.getenv("JY_DRAFTS_ROOT", "")).expanduser().resolve() if (args.drafts_root or os.getenv("JY_DRAFTS_ROOT")) else None

    if drafts_root and (drafts_root / project_name).exists() and not args.overwrite:
        raise RuntimeError(f"Draft already exists: {drafts_root / project_name}. Choose a new name or pass --overwrite after approval.")

    project = JyProject(
        project_name,
        width=width,
        height=height,
        drafts_root=str(drafts_root) if drafts_root else None,
        overwrite=args.overwrite,
    )
    report: dict[str, Any] = {
        "status": "BUILDING",
        "project": project.name,
        "draft_path": str(project.draft_dir),
        "jianying_skill_root": str(skill_root),
        "errors": [],
        "unsupported": [],
        "warnings": [],
        "added": {"clips": 0, "music": 0, "narration": 0, "captions": 0, "effects": 0, "transitions": 0},
    }
    cursors: dict[str, float] = {}

    for clip in sorted(plan.get("clips", []), key=lambda x: seconds(x.get("timeline_in_seconds"))):
        source = Path(str(clip.get("source_path", ""))).expanduser().resolve()
        if not source.exists():
            report["errors"].append(f"missing clip source: {source}")
            continue
        source_duration = seconds(clip.get("source_out_seconds")) - seconds(clip.get("source_in_seconds"))
        timeline_duration = seconds(clip.get("timeline_out_seconds")) - seconds(clip.get("timeline_in_seconds"))
        if source_duration <= 0 or timeline_duration <= 0:
            report["errors"].append(f"invalid duration for clip {clip.get('id', source.name)}")
            continue
        if clip.get("speed") not in (None, 1, 1.0, "1", "1.0"):
            report["unsupported"].append({"kind": "speed", "id": clip.get("id"), "value": clip.get("speed")})
        track = clip.get("track_name") or ("AudioTrack" if clip.get("media_type") == "audio" else "VideoTrack")
        start_seconds = seconds(clip.get("timeline_in_seconds"))
        start = choose_start(project, start_seconds, track, cursors)
        duration = time_string(timeline_duration)
        if clip.get("media_type") == "audio":
            segment = project.add_audio_safe(str(source), start_time=start, duration=duration, track_name=track)
        else:
            segment = project.add_media_safe(
                str(source),
                start_time=start,
                duration=duration,
                track_name=track,
                source_start=time_string(seconds(clip.get("source_in_seconds"))),
            )
        if segment is None:
            report["errors"].append(f"JianYing rejected clip import: {source}")
        else:
            report["added"]["clips"] += 1
            remember_end(project, track, start_seconds + timeline_duration, cursors)

    for item in plan.get("music", []):
        if item.get("source_path"):
            path = Path(str(item["source_path"])).expanduser().resolve()
            if not path.exists():
                report["errors"].append(f"missing music source: {path}")
                continue
            track = item.get("track_name", "BGM")
            start_seconds = seconds(item.get("start_time_seconds"))
            segment = project.add_audio_safe(str(path), start_time=choose_start(project, start_seconds, track, cursors), duration=item.get("duration_seconds"), track_name=track)
            remember_end(project, track, start_seconds + seconds(item.get("duration_seconds")), cursors)
        elif item.get("cloud_id"):
            track = item.get("track_name", "BGM")
            start_seconds = seconds(item.get("start_time_seconds"))
            segment = project.add_cloud_music(str(item["cloud_id"]), start_time=choose_start(project, start_seconds, track, cursors), duration=item.get("duration_seconds"), track_name=track)
            remember_end(project, track, start_seconds + seconds(item.get("duration_seconds")), cursors)
        else:
            report["errors"].append(f"music {item.get('id', '<unnamed>')} needs source_path or cloud_id")
            continue
        set_volume(segment, item.get("volume", 0.6))
        report["added"]["music"] += int(segment is not None)

    for item in plan.get("narration", []):
        try:
            add_narration(project, item, report, cursors)
            report["added"]["narration"] += 1
        except Exception as exc:
            report["errors"].append(f"narration {item.get('id', '<unnamed>')}: {exc}")

    for item in plan.get("captions", []):
        try:
            add_caption(project, item, report, cursors)
            report["added"]["captions"] += 1
        except Exception as exc:
            report["errors"].append(f"caption {item.get('id', '<unnamed>')}: {exc}")

    for item in plan.get("effects", []):
        try:
            effect = project.add_effect_simple(
                str(item["name"]),
                start_time=time_string(seconds(item.get("start_time_seconds"))),
                duration=time_string(seconds(item.get("duration_seconds"))),
                track_name=item.get("track_name", "EffectTrack"),
            )
            if effect is None:
                report["unsupported"].append({"kind": "effect", "name": item.get("name")})
            else:
                report["added"]["effects"] += 1
        except Exception as exc:
            report["errors"].append(f"effect {item.get('name', '<unnamed>')}: {exc}")

    for item in plan.get("transitions", []):
        report["unsupported"].append({"kind": "transition", "item": item, "reason": "requires a concrete adjacent segment mapping"})

    if report["errors"]:
        report["status"] = "FAILED_BEFORE_SAVE"
        return report, 1

    save_result = project.save()
    report["save"] = save_result
    report["status"] = "SAVED"
    report["track_summary"] = []
    for name, track in getattr(project.script, "tracks", {}).items():
        track_type = getattr(getattr(track, "type", None), "name", str(getattr(track, "type", "")))
        segments = getattr(track, "segments", []) or []
        report["track_summary"].append({"name": name, "type": track_type, "segment_count": len(segments)})

    video_segments = sum(
        item["segment_count"]
        for item in report["track_summary"]
        if "video" in item["type"].lower() or item["name"] == "VideoTrack"
    )
    if video_segments < 1:
        report["status"] = "FAILED_ACCEPTANCE"
        report["errors"].append("saved draft has no video track segment")
        return report, 1
    return report, 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Build a JianYing draft from an approved edit blueprint.")
    parser.add_argument("blueprint", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--project-name")
    parser.add_argument("--drafts-root")
    parser.add_argument("--overwrite", action="store_true", help="Replace an existing draft only after explicit approval.")
    args = parser.parse_args()
    plan = json.loads(args.blueprint.read_text(encoding="utf-8"))
    report, code = build(plan, args)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
