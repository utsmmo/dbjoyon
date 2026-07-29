from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
FILES = [
    ROOT / "AGENTS.md",
    ROOT / "docs" / "WORKING_STANDARDS.md",
    ROOT / "docs" / "DOCUMENT_MAP.md",
    ROOT / "docs" / "WORKING_MEMORY.md",
    ROOT / "docs" / "TASK_QUEUE.md",
    ROOT / "docs" / "TASK_CURRENT_HANDOFF.md",
    ROOT / "docs" / "CONTEXT_SNAPSHOT.md",
]


def main() -> int:
    print("Resume checklist")
    for path in FILES:
        status = "OK" if path.exists() else "MISSING"
        print(f"- [{status}] {path.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
