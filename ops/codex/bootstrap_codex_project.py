from __future__ import annotations

import argparse
import shutil
from pathlib import Path


def ask(prompt: str, default: str) -> str:
    value = input(f"{prompt} [{default}]: ").strip()
    return value or default


def slugify(text: str) -> str:
    return "".join(ch.lower() if ch.isalnum() else "-" for ch in text).strip("-")


def write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def append_gitignore(target: Path) -> None:
    gitignore_path = target / ".gitignore"
    existing = gitignore_path.read_text(encoding="utf-8") if gitignore_path.exists() else ""
    lines = existing.splitlines()
    for entry in [".gitnexus/", ".codex-temp/"]:
        if entry not in lines:
            lines.append(entry)
    gitignore_path.write_text("\n".join([line for line in lines if line]).rstrip() + "\n", encoding="utf-8")


def copy_repo_local_scripts(target: Path) -> None:
    source_dir = Path(__file__).resolve().parent
    dest_dir = target / "ops" / "codex"
    dest_dir.mkdir(parents=True, exist_ok=True)
    for script_name in [
        "api_doc_support.py",
        "generate_api_endpoint_docs.py",
        "check_api_doc_drift.py",
        "compact_work_state.py",
        "resume_checklist.py",
        "gitnexus_status.py",
    ]:
        shutil.copy2(source_dir / script_name, dest_dir / script_name)


def render_agents(project_name: str, frontend_path: str, backend_path: str, db_path: str) -> dict[str, str]:
    return {
        "leader.toml": f'''name = "leader"
description = "Project orchestrator for {project_name}. Use for multi-agent planning, cross-layer coordination, conflict resolution, and final integration decisions."
model = "gpt-5.6"
model_reasoning_effort = "high"
developer_instructions = """
Lead this repository like an engineering lead.
Read AGENTS.md, docs/WORKING_STANDARDS.md, docs/DOCUMENT_MAP.md, and docs/MULTIAGENT_PLAYBOOK.md before cross-layer work.
Use FE, BE, DB, DevOps, and Tester as bounded specialist agents.
Keep shared state in docs/TASK_CURRENT_HANDOFF.md.
Require every subagent to return Scope, Decision, Risks, Files, and Tests.
"""
''',
        "be.toml": f'''name = "BE"
description = "Backend specialist for API, services, and contracts in {project_name}."
model = "gpt-5.6"
model_reasoning_effort = "medium"
developer_instructions = """
Read docs/MULTIAGENT_PLAYBOOK.md and docs/DOCUMENT_MAP.md first.
Own backend behavior, API contracts, pagination, filters, validation, and service wiring.
Primary backend path: {backend_path}
Return only Scope, Decision, Risks, Files, and Tests.
"""
''',
        "fe.toml": f'''name = "FE"
description = "Frontend specialist for UI, data mapping, and interaction behavior in {project_name}."
model = "gpt-5.6-terra"
model_reasoning_effort = "medium"
developer_instructions = """
Read docs/MULTIAGENT_PLAYBOOK.md and docs/DOCUMENT_MAP.md first.
Own interface behavior, loading states, empty states, error states, and frontend data needs.
Primary frontend path: {frontend_path}
Return only Scope, Decision, Risks, Files, and Tests.
"""
''',
        "db.toml": f'''name = "DB"
description = "Database specialist for schema, migrations, indexing, and sync strategy in {project_name}."
model = "gpt-5.6"
model_reasoning_effort = "high"
developer_instructions = """
Read docs/MULTIAGENT_PLAYBOOK.md and docs/DOCUMENT_MAP.md first.
Own schema, migrations, indexes, watermarks, cursors, and rollback risk.
Primary database path: {db_path}
Return only Scope, Decision, Risks, Files, and Tests.
"""
''',
        "devops.toml": '''name = "DevOps"
description = "DevOps specialist for Docker, deployment, runtime configuration, and release safety."
model = "gpt-5.6-terra"
model_reasoning_effort = "medium"
developer_instructions = """
Read docs/MULTIAGENT_PLAYBOOK.md and docs/DOCUMENT_MAP.md first.
Own Docker, deploy config, environment wiring, health checks, and release/runtime safety.
Return only Scope, Decision, Risks, Files, and Tests.
"""
''',
        "tester.toml": '''name = "Tester"
description = "Testing and regression specialist."
model = "gpt-5.4"
model_reasoning_effort = "high"
developer_instructions = """
Own validation strategy, regression checks, reproducibility, and release confidence.
Return only Scope, Decision, Risks, Files, and Tests.
"""
''',
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Bootstrap a Codex multi-agent kit for a project.")
    parser.add_argument("--target", help="Target project directory.")
    parser.add_argument("--project-name", help="Project display name.")
    parser.add_argument("--frontend-path", help="Primary frontend path.")
    parser.add_argument("--backend-path", help="Primary backend path.")
    parser.add_argument("--db-path", help="Primary database path.")
    args = parser.parse_args()

    target = Path(args.target or ask("Target project path", str(Path.cwd()))).resolve()
    project_name = args.project_name or ask("Project name", target.name)
    frontend_path = args.frontend_path or ask("Frontend path", "frontend")
    backend_path = args.backend_path or ask("Backend path", "backend")
    db_path = args.db_path or ask("Database path", "db")

    write(target / ".codex" / "config.toml", """project_root_markers = [".git", "AGENTS.md"]\n\n[agents]\nenabled = true\nmax_concurrent_threads_per_session = 6\ndefault_subagent_model = "gpt-5.6-terra"\ndefault_subagent_reasoning_effort = "medium"\ninterrupt_message = true\n""")
    for filename, content in render_agents(project_name, frontend_path, backend_path, db_path).items():
        write(target / ".codex" / "agents" / filename, content)

    write(
        target / "AGENTS.md",
        f"""# AGENTS.md

## Purpose

This repository uses Codex as a coordinated teammate across frontend, backend, and database work.
The main thread owns requirements, decisions, and final integration.

## Repo map

- Frontend: `{frontend_path}`
- Backend: `{backend_path}`
- Database: `{db_path}`

## Core rules

- Use `leader` for cross-layer work.
- Use `FE`, `BE`, `DB`, `DevOps`, and `Tester` as bounded specialist agents.
- Do not let multiple agents edit the same files in parallel.
- Keep shared state in `docs/TASK_CURRENT_HANDOFF.md`.
- Prefer incremental data loading over full reloads where possible.
""",
    )
    write(
        target / "docs" / "WORKING_STANDARDS.md",
        """# Working Standards

Read order:
1. AGENTS.md
2. docs/WORKING_STANDARDS.md
3. docs/DOCUMENT_MAP.md
4. docs/MULTIAGENT_PLAYBOOK.md
5. layer-specific docs

Every subagent must return:
- Scope
- Decision
- Risks
- Files
- Tests
""",
    )
    write(
        target / "docs" / "DOCUMENT_MAP.md",
        f"""# Document Map

## Primary

- `AGENTS.md`
- `docs/WORKING_STANDARDS.md`
- `docs/DOCUMENT_MAP.md`
- `docs/MULTIAGENT_PLAYBOOK.md`
- `docs/MODEL_ROLE_MATRIX.md`
- `docs/GITNEXUS_INTEGRATION.md`

## FE

- primary path: `{frontend_path}`

## BE

- primary path: `{backend_path}`

## DB

- primary path: `{db_path}`
""",
    )
    write(
        target / "docs" / "MULTIAGENT_PLAYBOOK.md",
        """# Multi-Agent Playbook

Roles:
- leader
- FE
- BE
- DB
- DevOps
- Tester

Shared state:
- docs/TASK_CURRENT_HANDOFF.md
- docs/WORKING_MEMORY.md
- docs/TASK_QUEUE.md
- docs/CONTEXT_SNAPSHOT.md

Prompt shape:
- use leader
- spawn FE, BE, DB, DevOps, Tester
- require Scope, Decision, Risks, Files, Tests
""",
    )
    write(
        target / "docs" / "MODEL_ROLE_MATRIX.md",
        """# Model Role Matrix

| Role | Model | Reasoning |
| --- | --- | --- |
| leader | gpt-5.6 | high |
| BE | gpt-5.6 | medium |
| FE | gpt-5.6-terra | medium |
| DB | gpt-5.6 | high |
| DevOps | gpt-5.6-terra | medium |
| Tester | gpt-5.4 | high |
""",
    )
    write(
        target / "docs" / "GITNEXUS_INTEGRATION.md",
        """# GitNexus Integration

## Two layers

- Repo-local: `.gitnexus/` index and `node .gitnexus/run.cjs analyze`
- Machine-level: GitNexus MCP connector in the user's Codex config

## Important note

GitNexus is a source of truth for code relationships, not for business data rows.
""",
    )
    write(
        target / "docs" / "TASK_HANDOFF_TEMPLATE.md",
        """# Task Handoff Template

## Scope
## Decision
## Risks
## Files
## Tests
""",
    )
    write(
        target / "docs" / "TASK_CURRENT_HANDOFF.md",
        """# Task Current Handoff

## Status

- No active cross-layer handoff yet.
""",
    )
    write(
        target / "docs" / "WORKING_MEMORY.md",
        """# Working Memory

## Current Product Goal

- TBD

## Stable Constraints

- TBD
- GitNexus index is repo-local; MCP connector is machine-level.

## Stable Decisions

- Use leader, FE, BE, DB, DevOps, Tester.
- Use role-specific model defaults instead of one shared model for every agent.
- Keep active handoff in docs/TASK_CURRENT_HANDOFF.md.
- Keep queue in docs/TASK_QUEUE.md.
- Keep compact resume state in docs/CONTEXT_SNAPSHOT.md.
""",
    )
    write(
        target / "docs" / "TASK_QUEUE.md",
        """# Task Queue

## Active

- [ ] TBD

## Blocked

- [ ] None

## Waiting For Answer

- [ ] None
""",
    )
    write(
        target / "docs" / "CONTEXT_SNAPSHOT.md",
        """# Context Snapshot

## Snapshot Status

- No compact snapshot generated yet.
""",
    )
    copy_repo_local_scripts(target)
    append_gitignore(target)
    print(f"Bootstrapped Codex kit for {project_name} at {target}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
