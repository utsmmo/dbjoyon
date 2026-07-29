# Context Snapshot

Tai lieu nay duoc sinh de compact tinh trang cong viec hien tai va giup resume nhanh khi context dai.

## Working Memory

# Working Memory

Tai lieu nay la working memory dai han cho repo nay.
No duoc dung de tiep tuc cong viec khi context chat dai, khi doi thread, hoac khi can compact ma khong duoc quen giua chung.

## Current Product Goal

- TBD

## Stable Constraints

- Repo-local multi-agent rules only.
- Prefer incremental data loading over full reload.
- Keep API docs generated from code when possible.

## Stable Decisions

- Use `leader`, `FE`, `BE`, `DB`, `Tester` for role-based work.
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

## Task Queue

# Task Queue

Tai lieu nay la danh sach cong viec dang mo.
Moi item nen du nho de co the delegate cho 1 role hoac 1 lan implement.

## Active

- [ ] TBD

## Blocked

- [ ] None

## Waiting For Answer

- [ ] None

## Done Recently

- [x] Set up repo-local multi-agent roles
- [x] Add endpoint doc generator and drift checker
- [x] Add reusable bootstrap kit foundation

## Current Handoff

# Task Current Handoff

## Status

- No active cross-layer handoff yet.

## Scope

- TBD

## Decision

- TBD

## Risks

- TBD

## Files

- TBD

## Tests

- TBD
