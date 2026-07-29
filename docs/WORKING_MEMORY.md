# Working Memory

Tai lieu nay la working memory dai han cho repo nay.
No duoc dung de tiep tuc cong viec khi context chat dai, khi doi thread, hoac khi can compact ma khong duoc quen giua chung.

## Current Product Goal

- TBD

## Stable Constraints

- Repo-local multi-agent rules only.
- Prefer incremental data loading over full reload.
- Keep API docs generated from code when possible.
- GitNexus index is repo-local; MCP connector is machine-level.

## Stable Decisions

- Use `leader`, `FE`, `BE`, `DB`, `DevOps`, `Tester` for role-based work.
- Use role-specific model defaults instead of one shared model for every agent.
- Use `docs/TASK_CURRENT_HANDOFF.md` for active cross-layer handoff.
- Use `docs/TASK_QUEUE.md` for actionable work items.
- Use `docs/CONTEXT_SNAPSHOT.md` as compact resume state.

## Known Risks

- GitNexus FTS/BM25 is currently disabled, so graph exploration works but text search is not at full strength.

## Resume Checklist

- Read `AGENTS.md`
- Read `docs/WORKING_STANDARDS.md`
- Read `docs/DOCUMENT_MAP.md`
- Read `docs/TASK_QUEUE.md`
- Read `docs/TASK_CURRENT_HANDOFF.md`
- Read `docs/CONTEXT_SNAPSHOT.md`
