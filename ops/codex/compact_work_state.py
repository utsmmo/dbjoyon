from __future__ import annotations

import argparse
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
DOCS = ROOT / "docs"


def _section(path: Path, title: str) -> str:
    if not path.exists():
        return f"## {title}\n\n- Missing: `{path.relative_to(ROOT)}`\n"
    text = path.read_text(encoding="utf-8").strip()
    return f"## {title}\n\n{text}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Compact current work state into a resume snapshot.")
    parser.add_argument(
        "--output",
        default=str(DOCS / "CONTEXT_SNAPSHOT.md"),
        help="Snapshot output path.",
    )
    args = parser.parse_args()

    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)

    content = "\n".join(
        [
            "# Context Snapshot",
            "",
            "Tai lieu nay duoc sinh de compact tinh trang cong viec hien tai va giup resume nhanh khi context dai.",
            "",
            _section(DOCS / "WORKING_MEMORY.md", "Working Memory"),
            _section(DOCS / "TASK_QUEUE.md", "Task Queue"),
            _section(DOCS / "TASK_CURRENT_HANDOFF.md", "Current Handoff"),
        ]
    ).rstrip() + "\n"

    output.write_text(content, encoding="utf-8")
    print(f"Wrote {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
