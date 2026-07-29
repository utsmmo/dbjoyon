---
name: sudo-super-kit
description: "Bootstrap a reusable Codex project kit with multi-agent roles, working memory, task queue, compact resume state, and repo-local docs automation. Use when setting up a new repository so Codex can ask only for unclear project details, scaffold the files, generate API docs, add a task/handoff system, and establish leader/FE/BE/DB/DevOps/Tester roles."
---

# Sudo Super Kit

Bootstrap a new repository with a reusable Codex operating kit.

## What this kit creates

- `.codex/config.toml`
- `.codex/agents/leader.toml`
- `.codex/agents/be.toml`
- `.codex/agents/fe.toml`
- `.codex/agents/db.toml`
- `.codex/agents/devops.toml`
- `.codex/agents/tester.toml`
- `AGENTS.md`
- `docs/WORKING_STANDARDS.md`
- `docs/DOCUMENT_MAP.md`
- `docs/MULTIAGENT_PLAYBOOK.md`
- `docs/TASK_HANDOFF_TEMPLATE.md`
- `docs/TASK_CURRENT_HANDOFF.md`
- `docs/WORKING_MEMORY.md`
- `docs/TASK_QUEUE.md`
- `docs/CONTEXT_SNAPSHOT.md`
- `docs/MODEL_ROLE_MATRIX.md`
- `docs/GITNEXUS_INTEGRATION.md`
- `ops/codex/generate_api_endpoint_docs.py`
- `ops/codex/check_api_doc_drift.py`
- `ops/codex/compact_work_state.py`
- `ops/codex/resume_checklist.py`
- `ops/codex/gitnexus_status.py`

## Workflow

1. Ask only the minimum missing details:
   - target path
   - project name
   - frontend path
   - backend path
   - database path
2. Run the bootstrap script in `scripts/`.
3. If the project has FastAPI routes, run the endpoint doc generator.
4. Explain GitNexus as a two-layer setup:
   - repo-local index
   - machine-level Codex connector
5. Run the resume checklist.
6. Tell the user the main commands they will use day to day.

## Commands

Use the bundled bootstrap script:

```powershell
python scripts/bootstrap.py --target D:\path\to\project --project-name "My Project" --frontend-path frontend --backend-path backend --db-path db
```

Compact the current state:

```powershell
python ops/codex/compact_work_state.py
```

Check resume files:

```powershell
python ops/codex/resume_checklist.py
```

## Reuse

This skill folder is intended to live in a Git repo so it can be pushed to GitHub and reused later.
Keep it repo-agnostic and ask the user only about missing project structure details.
