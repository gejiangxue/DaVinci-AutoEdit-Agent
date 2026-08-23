from __future__ import annotations

import argparse
import json
import subprocess
from collections import Counter
from pathlib import Path


def probe_duration(path: Path) -> float | None:
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode:
        return None
    try:
        return float(result.stdout.strip())
    except ValueError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate an approved JianYing edit blueprint.")
    parser.add_argument("blueprint", type=Path)
    args = parser.parse_args()
    payload = json.loads(args.blueprint.read_text(encoding="utf-8"))
    clips = sorted(payload.get("clips", []), key=lambda item: float(item.get("timeline_in_seconds", 0)))
    errors: list[str] = []
    warnings: list[str] = []
    groups: Counter[str] = Counter()
    previous_source = ""
    previous_out: float | None = None

    for index, clip in enumerate(clips, start=1):
        label = clip.get("id", f"clip-{index}")
        source = Path(str(clip.get("source_path", ""))).expanduser().resolve()
        source_in = float(clip.get("source_in_seconds", 0))
        source_out = float(clip.get("source_out_seconds", 0))
        timeline_in = float(clip.get("timeline_in_seconds", 0))
        timeline_out = float(clip.get("timeline_out_seconds", 0))
        if not source.exists():
            errors.append(f"{label}: missing source {source}")
        if source_in < 0 or source_out <= source_in:
            errors.append(f"{label}: invalid source range")
        if timeline_out <= timeline_in:
            errors.append(f"{label}: non-positive timeline duration")
        actual_duration = probe_duration(source) if source.exists() else None
        if actual_duration is not None and source_out > actual_duration + 0.05:
            errors.append(f"{label}: source_out {source_out:.3f}s exceeds media duration {actual_duration:.3f}s")
        speed = clip.get("speed")
        if speed not in (None, 1, 1.0, "1", "1.0"):
            warnings.append(f"{label}: speed {speed} requires a supported JianYing speed operation or manual adjustment")
        elif abs((source_out - source_in) - (timeline_out - timeline_in)) > 0.05:
            warnings.append(f"{label}: source/timeline duration mismatch without speed declaration")
        if previous_out is not None:
            delta = timeline_in - previous_out
            if delta > 0.001:
                warnings.append(f"{label}: timeline gap {delta:.3f}s")
            elif delta < -0.001:
                errors.append(f"{label}: timeline overlap {-delta:.3f}s")
        if previous_source and str(source) == previous_source:
            warnings.append(f"{label}: adjacent reuse of source {source.name}")
        groups[str(clip.get("source_group", "unclassified"))] += timeline_out - timeline_in
        previous_source = str(source)
        previous_out = timeline_out

    for index, item in enumerate(payload.get("music", []), start=1):
        if not item.get("source_path") and not item.get("cloud_id"):
            errors.append(f"music-{index}: needs source_path or cloud_id")
        if item.get("source_path") and not Path(str(item["source_path"])).expanduser().exists():
            errors.append(f"music-{index}: missing source {item['source_path']}")

    report = {
        "schema_version": payload.get("schema_version", ""),
        "clip_count": len(clips),
        "errors": errors,
        "warnings": warnings,
        "duration_by_source_group_seconds": dict(groups),
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
