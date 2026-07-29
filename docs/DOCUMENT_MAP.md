# Document Map

## Mục tiêu

Tài liệu này ghi rõ:

- agent nào dùng tài liệu nào
- tài liệu nào là nguồn chính
- tài liệu nào chỉ là tham khảo, handoff, hoặc runbook

## Global documents

### Primary

- `D:\AutoCode\DB\Review\AGENTS.md`
- `D:\AutoCode\DB\Review\docs\DOCS_QUICK_INDEX.md`
- `D:\AutoCode\DB\Review\docs\WORKING_STANDARDS.md`
- `D:\AutoCode\DB\Review\docs\DOCUMENT_MAP.md`
- `D:\AutoCode\DB\Review\docs\MULTIAGENT_PLAYBOOK.md`
- `D:\AutoCode\DB\Review\README.md`
- `D:\AutoCode\DB\Review\docs\ISSUE_TRIAGE_MATRIX.md`
- `D:\AutoCode\DB\Review\docs\MODEL_ROLE_MATRIX.md`
- `D:\AutoCode\DB\Review\docs\GITNEXUS_INTEGRATION.md`

### Dùng khi nào

- mọi task cross-layer
- mọi task cần quyết định giữa nhiều agent
- mọi task cần biết source of truth của tài liệu
- mọi task cần dùng `leader`, `BE`, `FE`, `DB`, `DevOps`, hoặc `Tester`

## UX/UI agent

### Primary

- `D:\AutoCode\DB\Review\docs\DOCS_QUICK_INDEX.md`
- `D:\AutoCode\DB\Review\docs\WEBSITE_UI_ARCHITECTURE.md`
- `D:\AutoCode\DB\Review\docs\WEBSITE_QUERY_GUIDE.md`
- `D:\AutoCode\DB\Review\web-hotel-review\frontend-web\README.md`

### Secondary

- `D:\AutoCode\DB\Review\docs\WEBSITE_DB_HANDOFF.md`
- `D:\AutoCode\DB\Review\docs\DASHBOARD_ANALYTICS_ARCHITECTURE.md`
- `D:\AutoCode\DB\Review\docs\MULTIAGENT_PLAYBOOK.md`

### Không nên dùng làm source chính

- `POST_REVIEW_GUIDE.md`
- các runbook backup/deploy

## Database agent

### Primary

- `D:\AutoCode\DB\Review\docs\DOCS_QUICK_INDEX.md`
- `D:\AutoCode\DB\Review\docs\WEBSITE_DB_HANDOFF.md`
- `D:\AutoCode\DB\Review\docs\DASHBOARD_ANALYTICS_ARCHITECTURE.md`
- `D:\AutoCode\DB\Review\README.md`
- `D:\AutoCode\DB\Review\web-hotel-review\database\README.md`

### Secondary

- `D:\AutoCode\DB\Review\docs\ANALYTICS_BACKFILL_RUNBOOK.md`
- `D:\AutoCode\DB\Review\docs\BACKEND_ANALYTICS_TASK.md`
- `D:\AutoCode\DB\Review\docs\MULTIAGENT_PLAYBOOK.md`

### Không nên dùng làm source chính

- `WEBSITE_UI_ARCHITECTURE.md`
- `GOOGLE_SHEETS_EXPORT.md`

## Backend agent

### Primary

- `D:\AutoCode\DB\Review\docs\DOCS_QUICK_INDEX.md`
- `D:\AutoCode\DB\Review\docs\WEBSITE_QUERY_GUIDE.md`
- `D:\AutoCode\DB\Review\docs\Crawl\POST_REVIEW_GUIDE.md`
- `D:\AutoCode\DB\Review\docs\WEBSITE_DB_HANDOFF.md`
- `D:\AutoCode\DB\Review\web-hotel-review\backend-api\README.md`
- `D:\AutoCode\DB\Review\README.md`

### Secondary

- `D:\AutoCode\DB\Review\docs\DASHBOARD_ANALYTICS_ARCHITECTURE.md`
- `D:\AutoCode\DB\Review\docs\REVIEW_CATEGORIES_GUIDE.md`
- `D:\AutoCode\DB\Review\docs\MULTIAGENT_PLAYBOOK.md`

### Không nên dùng làm source chính

- `DEPLOY_ONLINE_QUICKSTART.md`
- `DB_BACKUP_GOOGLE_DRIVE.md`

## Analytics agent

### Primary

- `D:\AutoCode\DB\Review\docs\DASHBOARD_ANALYTICS_ARCHITECTURE.md`
- `D:\AutoCode\DB\Review\docs\BACKEND_ANALYTICS_TASK.md`
- `D:\AutoCode\DB\Review\docs\ANALYTICS_BACKFILL_RUNBOOK.md`

### Secondary

- `D:\AutoCode\DB\Review\docs\WEBSITE_DB_HANDOFF.md`
- `D:\AutoCode\DB\Review\docs\WEBSITE_QUERY_GUIDE.md`
- `D:\AutoCode\DB\Review\docs\REVIEW_API_TIMEOUT_REPORT_2026-07-26.md`
- `D:\AutoCode\DB\Review\docs\MULTIAGENT_PLAYBOOK.md`

## Crawler or ingestion agent

### Primary

- `D:\AutoCode\DB\Review\docs\Crawl\POST_REVIEW_GUIDE.md`
- `D:\AutoCode\DB\Review\docs\Crawl\CRAWLER_DOC_START_HERE.md`
- `D:\AutoCode\DB\Review\docs\API_ENDPOINTS.md`

### Secondary

- `D:\AutoCode\DB\Review\README.md`
- `D:\AutoCode\DB\Review\docs\LEGACY_BOOKING_CLEANUP.md`

## DevOps agent

### Primary

- `D:\AutoCode\DB\Review\docs\DOCS_QUICK_INDEX.md`
- `D:\AutoCode\DB\Review\docs\DEPLOY_ONLINE_QUICKSTART.md`
- `D:\AutoCode\DB\Review\docs\DB_BACKUP_GOOGLE_DRIVE.md`
- `D:\AutoCode\DB\Review\docs\GOOGLE_SHEETS_EXPORT.md`
- `D:\AutoCode\DB\Review\docker-compose.yml`
- `D:\AutoCode\DB\Review\Dockerfile`

### Secondary

- `D:\AutoCode\DB\Review\README.md`
- `D:\AutoCode\DB\Review\docs\MULTIAGENT_PLAYBOOK.md`

## Admin or access-control agent

### Primary

- `D:\AutoCode\DB\Review\docs\ACCESS_CONTROL_ARCHITECTURE.md`
- `D:\AutoCode\DB\Review\docs\WEBSITE_DB_HANDOFF.md`

### Secondary

- `D:\AutoCode\DB\Review\README.md`

## Document roles

### Architecture

- `WEBSITE_UI_ARCHITECTURE.md`
- `DASHBOARD_ANALYTICS_ARCHITECTURE.md`
- `ACCESS_CONTROL_ARCHITECTURE.md`

### Contract and handoff

- `WEBSITE_DB_HANDOFF.md`
- `Crawl/POST_REVIEW_GUIDE.md`

### Query and usage guide

- `WEBSITE_QUERY_GUIDE.md`
- `REVIEW_CATEGORIES_GUIDE.md`

### Runbook and operations

- `ANALYTICS_BACKFILL_RUNBOOK.md`
- `DEPLOY_ONLINE_QUICKSTART.md`
- `DB_BACKUP_GOOGLE_DRIVE.md`
- `GOOGLE_SHEETS_EXPORT.md`
- `LEGACY_BOOKING_CLEANUP.md`
- `MULTIAGENT_PLAYBOOK.md`
- `TASK_HANDOFF_TEMPLATE.md`

### Triage and ownership

- `ISSUE_TRIAGE_MATRIX.md`

### Runtime coordination and role defaults

- `MODEL_ROLE_MATRIX.md`
- `GITNEXUS_INTEGRATION.md`

### Reports and point-in-time references

- `REVIEW_API_TIMEOUT_REPORT_2026-07-26.md`

## Quy tắc bảo trì

- Khi tạo tài liệu mới trong `docs/`, phải thêm nó vào file này.
- Nếu tài liệu mới thay thế một tài liệu cũ, phải ghi rõ tài liệu nào là `Primary`.
- Nếu một `README` của subproject trở thành nơi chứa quyết định kiến trúc, nên tách quyết định đó sang `docs/` rồi giữ `README` cho setup và developer onboarding.
