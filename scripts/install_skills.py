from __future__ import annotations

import argparse
import os
import shutil
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Install all bundled Codex skills.")
    parser.add_argument(
        "--dest",
        type=Path,
        default=Path(os.getenv("CODEX_HOME", Path.home() / ".codex")) / "skills",
        help="Codex skills directory.",
    )
    parser.add_argument("--force", action="store_true", help="Replace existing copies.")
    args = parser.parse_args()

    repo = Path(__file__).resolve().parents[1]
    source_root = repo / "skills"
    args.dest.mkdir(parents=True, exist_ok=True)

    for source in sorted(source_root.iterdir()):
        if not source.is_dir() or not (source / "SKILL.md").exists():
            continue
        target = args.dest / source.name
        if target.exists():
            if not args.force:
                print(f"skip {source.name}: already exists (use --force)")
                continue
            shutil.rmtree(target)
        shutil.copytree(source, target)
        print(f"installed {source.name} -> {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
