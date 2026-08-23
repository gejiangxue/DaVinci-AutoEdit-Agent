from __future__ import annotations

import json
import os
import shutil
import sys
from pathlib import Path

def candidate_roots() -> list[Path | None]:
    current = Path.cwd().resolve()
    repo_root = Path(__file__).resolve().parents[3]
    env_root = os.getenv("JY_SKILL_ROOT", "").strip()
    return [
        Path(env_root).expanduser() if env_root else None,
        current / ".agent/skills/jianying-editor",
        current / ".trae/skills/jianying-editor",
        current / ".claude/skills/jianying-editor",
        current / "skills/jianying-editor",
        repo_root / "skills/jianying-editor",
        Path.home() / ".codex/skills/jianying-editor",
    ]


def find_jy_root() -> str:
    for root in candidate_roots():
        if root and (root / "scripts/jy_wrapper.py").exists():
            return str(root.resolve())
    return ""


def main() -> int:
    jy_root = find_jy_root()
    report = {
        "python": sys.version.split()[0],
        "ffmpeg": shutil.which("ffmpeg") or "",
        "ffprobe": shutil.which("ffprobe") or "",
        "jianying_editor": {"skill_root": jy_root, "wrapper_found": bool(jy_root)},
        "llm": {
            "configured": bool(os.getenv("LLM_BASE_URL") and os.getenv("LLM_MODEL")),
            "has_api_key": bool(os.getenv("LLM_API_KEY")),
        },
        "tts": {
            "configured": bool(os.getenv("TTS_BASE_URL")),
            "has_api_key": bool(os.getenv("TTS_API_KEY")),
        },
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ffmpeg"] and report["ffprobe"] and report["jianying_editor"]["wrapper_found"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
