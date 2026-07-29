# Multi-Agent Playbook

## Mục tiêu

Tài liệu này định nghĩa cách dùng `leader`, `BE`, `FE`, `DB`, `DevOps`, và `Tester` trong repo `D:\AutoCode\DB\Review`.
Toan bo quy tac trong tai lieu nay chi ap dung cho repo nay, khong ap dung chung cho cac project khac.

## Role names

Các role đã được khai báo trong:

- `D:\AutoCode\DB\Review\.codex\agents\leader.toml`
- `D:\AutoCode\DB\Review\.codex\agents\be.toml`
- `D:\AutoCode\DB\Review\.codex\agents\devops.toml`
- `D:\AutoCode\DB\Review\.codex\agents\fe.toml`
- `D:\AutoCode\DB\Review\.codex\agents\db.toml`
- `D:\AutoCode\DB\Review\.codex\agents\tester.toml`

Tên role cần dùng:

- `leader`
- `BE`
- `DevOps`
- `FE`
- `DB`
- `Tester`

Nếu surface của Codex hỗ trợ mention theo `@`, có thể gọi:

- `@leader`
- `@BE`
- `@DevOps`
- `@FE`
- `@DB`
- `@Tester`

Nếu surface không hiện mention chip cho custom agent, hãy viết rõ trong prompt:

```text
Use leader.
Spawn BE, FE, DB, DevOps, and Tester.
```

## Trách nhiệm từng role

### `leader`

- điều phối multi-agent
- chọn subagents cần dùng
- chốt contract chung
- ngăn nhiều agent sửa cùng một file song song
- giữ `docs/TASK_CURRENT_HANDOFF.md` là shared state

### `BE`

- API, validation, service orchestration
- paging, filters, cursor, watermark
- contract giữa frontend và database ở tầng backend

### `FE`

- màn hình, component, trạng thái loading/empty/error
- mapping field API ra UI
- tránh full refetch nếu có thể invalidate một phần

### `DB`

- schema, migration, index
- upsert, dedup, sync strategy
- aggregate path, incremental path, rollback risk

### `DevOps`

- Dockerfile, docker-compose, env wiring
- deploy flow, runtime config, health checks
- backup/restore, release sequence, operational safety

### `Tester`

- test plan
- regression analysis
- command validation
- xác minh behavior thực tế sau thay đổi

## GitNexus trong repo này

GitNexus đã được index cho repo và đã cấu hình Codex MCP ở môi trường người dùng.

Repo-local artifacts hiện có:

- `D:\AutoCode\DB\Review\.gitnexus\`
- `D:\AutoCode\DB\Review\.gitnexus\run.cjs`

Trạng thái hiện tại:

- repo đã được GitNexus index thành công
- `context`, `query`, `impact`, `trace`, và graph-based exploration dùng được
- FTS/BM25 hiện đang tắt vì extension FTS chưa được cài hoàn chỉnh trên máy này
- nếu cần repair FTS khi có mạng ổn định, chạy lại GitNexus với repair flow

Khi dùng GitNexus:

1. đọc repo context
2. query flow hoặc concept
3. đọc symbol context
4. chạy impact analysis trước khi sửa lớn

Nếu index stale hoặc vừa đổi code lớn, chạy lại:

```powershell
node .gitnexus/run.cjs analyze
```

Nếu cần repair FTS/BM25:

```powershell
node .gitnexus/run.cjs analyze --repair-fts
```

## Tài liệu mỗi role phải đọc

### `leader`

- `AGENTS.md`
- `docs/WORKING_STANDARDS.md`
- `docs/DOCUMENT_MAP.md`
- `docs/MULTIAGENT_PLAYBOOK.md`
- `docs/TASK_HANDOFF_TEMPLATE.md`

### `BE`

- `AGENTS.md`
- `docs/DOCUMENT_MAP.md`
- `docs/WEBSITE_QUERY_GUIDE.md`
- `docs/Crawl/POST_REVIEW_GUIDE.md`
- `docs/WEBSITE_DB_HANDOFF.md`
- `README.md`

### `FE`

- `AGENTS.md`
- `docs/DOCUMENT_MAP.md`
- `docs/WEBSITE_UI_ARCHITECTURE.md`
- `docs/WEBSITE_QUERY_GUIDE.md`
- `docs/WEBSITE_DB_HANDOFF.md`
- `web-hotel-review/frontend-web/README.md`

### `DB`

- `AGENTS.md`
- `docs/DOCUMENT_MAP.md`
- `docs/WEBSITE_DB_HANDOFF.md`
- `docs/DASHBOARD_ANALYTICS_ARCHITECTURE.md`
- `README.md`
- `web-hotel-review/database/README.md`

### `Tester`

- `AGENTS.md`
- `docs/WORKING_STANDARDS.md`
- `docs/DOCUMENT_MAP.md`
- `docs/TASK_CURRENT_HANDOFF.md` nếu đã có
- `README.md`
- `web-hotel-review/backend-api/README.md`
- `web-hotel-review/frontend-web/README.md`

### `DevOps`

- `AGENTS.md`
- `docs/DOCUMENT_MAP.md`
- `docs/MULTIAGENT_PLAYBOOK.md`
- `docs/DEPLOY_ONLINE_QUICKSTART.md`
- `docs/DB_BACKUP_GOOGLE_DRIVE.md`
- `docs/GOOGLE_SHEETS_EXPORT.md`
- `docker-compose.yml`
- `Dockerfile`

## Handoff protocol

Mọi subagent phải trả về đúng 5 phần:

- `Scope`
- `Decision`
- `Risks`
- `Files`
- `Tests`

Không được dump log dài vào main thread nếu chưa có quyết định cần chốt.

## Shared state

Shared state của task nằm ở:

- `docs/TASK_CURRENT_HANDOFF.md`
- `docs/ISSUE_TRIAGE_MATRIX.md` de khoanh owner dau tien khi co loi
- `docs/WORKING_MEMORY.md`
- `docs/TASK_QUEUE.md`
- `docs/CONTEXT_SNAPSHOT.md`

Chỉ ghi vào đó:

- contract hiện tại
- assumption đã đổi
- file ảnh hưởng
- trạng thái test/validation

Không dùng file này như nơi ghi reasoning dài dòng.

## Tu dong hoa trong repo nay

Scripts repo-local:

- `ops/codex/generate_api_endpoint_docs.py`
- `ops/codex/check_api_doc_drift.py`
- `ops/codex/bootstrap_codex_project.py`
- `ops/codex/compact_work_state.py`
- `ops/codex/resume_checklist.py`
- `ops/codex/gitnexus_status.py`

Cong dung:

- sinh `docs/API_ENDPOINTS.md` tu code route hien tai
- phat hien docs endpoint lech voi code
- scaffold nhanh bo multi-agent cho du an moi
- compact state hien tai de resume khi context dai
- kiem tra nhanh cac file memory can doc khi quay lai task
- kiem tra nhanh GitNexus dang o muc repo-local hay machine-level

Lenh dung:

```powershell
python ops/codex/generate_api_endpoint_docs.py
python ops/codex/check_api_doc_drift.py
python ops/codex/compact_work_state.py
python ops/codex/resume_checklist.py
python ops/codex/gitnexus_status.py
```

Neu can dung bo kit cho du an moi:

```powershell
python ops/codex/bootstrap_codex_project.py --target D:\path\to\new-project
```

Ten kit tai su dung cua bo nay la:

- `sudo super kit`
- skill folder: `sudo-super-kit`

## Model role defaults

Doc them:

- `docs/MODEL_ROLE_MATRIX.md`

Tat ca role khong dung chung mot model nua.
Kit nay co role-specific defaults de tiet kiem token.

## Prompt mẫu

```text
@leader Chúng ta làm task cross-layer cho repo này.

Đọc:
- AGENTS.md
- docs/WORKING_STANDARDS.md
- docs/DOCUMENT_MAP.md
- docs/MULTIAGENT_PLAYBOOK.md

Spawn:
- @BE
- @DevOps
- @FE
- @DB
- @Tester

Yêu cầu mỗi agent trả về:
- Scope
- Decision
- Risks
- Files
- Tests

Hãy cập nhật docs/TASK_CURRENT_HANDOFF.md, chốt contract chung, rồi chỉ định một agent tích hợp cuối.
```
