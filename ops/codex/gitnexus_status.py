from __future__ import annotations

from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def main() -> int:
    gitnexus_dir = ROOT / ".gitnexus"
    run_script = gitnexus_dir / "run.cjs"
    config_path = Path.home() / ".codex" / "config.toml"

    print("GitNexus status")
    print(f"- repo index: {'OK' if gitnexus_dir.exists() else 'MISSING'} -> {gitnexus_dir}")
    print(f"- repo runner: {'OK' if run_script.exists() else 'MISSING'} -> {run_script}")
    print(f"- machine config: {'OK' if config_path.exists() else 'MISSING'} -> {config_path}")
    print("")
    print("Note:")
    print("- Repo-local index stores graph data for this project.")
    print("- Machine-level Codex config exposes the GitNexus MCP connector.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
