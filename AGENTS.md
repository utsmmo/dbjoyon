# AGENTS.md

## Purpose

This repository uses Codex as a coordinated teammate across `frontend`, `backend`, and `database` work.
The main thread owns requirements, decisions, and final integration.
Subagents are used for parallel analysis, testing, and review, not for uncontrolled concurrent code edits.

## Repo map

- `app/`: FastAPI backend for the hotel review data platform.
- `db/`: PostgreSQL init scripts and migrations.
- `docs/`: contracts, guides, and operational notes.
- `web-hotel-review/frontend-web/`: Next.js frontend.
- `web-hotel-review/backend-api/`: NestJS backend API.
- `web-hotel-review/database/`: web app database layer and schema assets.

## Team roles

- `UX/UI agent`
  - Reviews user flows, screen states, filters, tables, loading, empty, and error states.
  - Defines only the data contract the UI needs.
- `Database agent`
  - Reviews schema, migrations, indexes, deduplication, upsert strategy, and rollback risk.
  - Must call out write amplification and query impact.
- `Backend agent`
  - Owns endpoint shape, validation, auth, paging, filtering, and service orchestration.
  - Must align responses to the UI contract and DB constraints.
- `Main agent`
  - Merges decisions from all agents.
  - Is the only agent that should perform final cross-layer integration unless the task is explicitly split by directory and guaranteed conflict-free.

## Coordination rules

- Do not ask multiple agents to edit the same files in parallel.
- Use parallel agents for exploration, test design, bug triage, schema review, and log analysis.
- Each subagent must return a short handoff:
  - `Scope`
  - `Decision`
  - `Risks`
  - `Files touched or proposed`
  - `Tests needed`
- If agents disagree, the main agent must summarize the conflict and resolve it before implementation continues.

## Incremental data rules

When a dataset changes, prefer loading only the delta instead of refetching the whole dataset.

- Prefer `updated_at`, `source_updated_at`, `last_synced_at`, or a monotonic cursor as the sync watermark.
- For reviews, preserve and use the existing upsert model with deduplication and `sync_version`.
- Fetch by time or cursor windows such as:
  - `updated_at > :last_seen_updated_at`
  - `source_updated_at > :last_source_updated_at`
  - `id > :last_seen_id` when IDs are monotonic
- Return paginated or sliced results for large tables.
- For dashboards, separate:
  - full snapshot endpoints
  - incremental change endpoints
- Do not send full raw payloads to downstream agents or UI when only summaries or changed fields are required.

## Shared-state pattern for agents

Subagents do not communicate peer-to-peer. They communicate through the main thread and shared artifacts.

- Keep the main thread as the source of truth for final decisions.
- Before starting a cross-layer task, read:
  - `docs/WORKING_STANDARDS.md`
  - `docs/DOCUMENT_MAP.md`
- If a task spans layers, create or update a short document in `docs/` that records:
  - API request and response shape
  - DB fields affected
  - frontend assumptions
  - open questions
- Prefer summaries over raw logs.
- Only pass the minimum changed context back into the next step.

## Done criteria

A change is not done until Codex has, when relevant:

- updated or added tests
- run the smallest meaningful checks
- confirmed the changed behavior
- reviewed the diff for regressions and risky patterns

## Validation commands

Choose the smallest set that matches the files changed.

- Root Python API:
  - `docker compose up -d`
  - `docker compose ps`
- Web frontend:
  - `cd web-hotel-review/frontend-web && pnpm lint`
  - `cd web-hotel-review/frontend-web && pnpm build`
- Web backend:
  - `cd web-hotel-review/backend-api && pnpm test`
  - `cd web-hotel-review/backend-api && pnpm lint`
  - `cd web-hotel-review/backend-api && pnpm build`

## Review focus

Reviews should prioritize:

- broken data contracts between frontend, backend, and DB
- full reloads where incremental fetch would work
- missing pagination, cursors, or watermarks
- migration safety and rollback gaps
- duplicate writes and token-heavy payload passing

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **dbjoyon** (1914 symbols, 2760 relationships, 69 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> Index stale? Run `node .gitnexus/run.cjs analyze` from the project root — it auto-selects an available runner. No `.gitnexus/run.cjs` yet? `npx gitnexus analyze` (npm 11 crash → `npm i -g gitnexus`; #1939).

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows. For regression review, compare against the default branch: `detect_changes({scope: "compare", base_ref: "main"})`.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `query({search_query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `context({name: "symbolName"})`.
- For security review, `explain({target: "fileOrSymbol"})` lists taint findings (source→sink flows; needs `analyze --pdg`).

## Never Do

- NEVER edit a function, class, or method without first running `impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `rename` which understands the call graph.
- NEVER commit changes without running `detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/dbjoyon/context` | Codebase overview, check index freshness |
| `gitnexus://repo/dbjoyon/clusters` | All functional areas |
| `gitnexus://repo/dbjoyon/processes` | All execution flows |
| `gitnexus://repo/dbjoyon/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
