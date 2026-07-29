from __future__ import annotations

import runpy
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "ops" / "codex"


def main() -> int:
    source = SOURCE / "bootstrap_codex_project.py"
    if not source.exists():
        raise SystemExit(f"Missing source script: {source}")
    sys.argv = [str(source), *sys.argv[1:]]
    runpy.run_path(str(source), run_name="__main__")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
