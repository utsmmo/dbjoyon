# Working Standards

## Mục tiêu

Tài liệu này chuẩn hóa cách đọc tài liệu và phối hợp agent trong thư mục `D:\AutoCode\DB\Review`.
Tat ca quy tac trong file nay chi danh cho repo nay.

Mục tiêu là để:

- không bị lặp lại cùng một câu hỏi ở nhiều `README` và `docs`
- agent biết phải đọc tài liệu nào trước
- giảm việc nạp dư context và tốn token
- giữ một nguồn quyết định rõ ràng cho từng loại việc

## Thứ tự ưu tiên tài liệu

Khi có nhiều tài liệu cùng nói về một chủ đề, ưu tiên theo thứ tự này:

1. `AGENTS.md`
2. `docs/WORKING_STANDARDS.md`
3. `docs/DOCUMENT_MAP.md`
4. `docs/MULTIAGENT_PLAYBOOK.md`
5. tài liệu kiến trúc hoặc contract chuyên biệt trong `docs/`
6. `README.md` của repo hoặc subproject
7. tài liệu báo cáo, runbook, handoff, hoặc guide tác nghiệp

## Quy tắc đọc theo loại task

### Nếu task là cross-layer

Phải đọc trước:

- `AGENTS.md`
- `docs/WORKING_STANDARDS.md`
- `docs/DOCUMENT_MAP.md`
- `docs/MULTIAGENT_PLAYBOOK.md`
- `docs/WORKING_MEMORY.md`
- `docs/TASK_QUEUE.md`
- `docs/CONTEXT_SNAPSHOT.md`
- tài liệu chuyên biệt theo layer liên quan

### Nếu task là UX/UI

Phải đọc trước:

- `docs/DOCUMENT_MAP.md`
- `docs/MULTIAGENT_PLAYBOOK.md`
- `docs/WEBSITE_UI_ARCHITECTURE.md`
- `docs/WEBSITE_QUERY_GUIDE.md`
- `web-hotel-review/frontend-web/README.md`

### Nếu task là database

Phải đọc trước:

- `docs/DOCUMENT_MAP.md`
- `docs/MULTIAGENT_PLAYBOOK.md`
- `docs/WEBSITE_DB_HANDOFF.md`
- `docs/DASHBOARD_ANALYTICS_ARCHITECTURE.md`
- `README.md`
- `web-hotel-review/database/README.md`

### Nếu task là backend/API

Phải đọc trước:

- `docs/DOCUMENT_MAP.md`
- `docs/MULTIAGENT_PLAYBOOK.md`
- `docs/WEBSITE_QUERY_GUIDE.md`
- `docs/Crawl/POST_REVIEW_GUIDE.md`
- `docs/WEBSITE_DB_HANDOFF.md`
- `web-hotel-review/backend-api/README.md`
- `README.md`

### Nếu task là analytics

Phải đọc trước:

- `docs/DASHBOARD_ANALYTICS_ARCHITECTURE.md`
- `docs/BACKEND_ANALYTICS_TASK.md`
- `docs/ANALYTICS_BACKFILL_RUNBOOK.md`
- `docs/WEBSITE_QUERY_GUIDE.md`
- `docs/MULTIAGENT_PLAYBOOK.md`

## Quy tắc authority

Mỗi chủ đề chỉ nên có một nguồn quyết định chính.

- Quy tắc agent và phối hợp: `AGENTS.md`
- Quy tắc đọc tài liệu: `docs/WORKING_STANDARDS.md`
- Bản đồ tài liệu theo agent: `docs/DOCUMENT_MAP.md`
- Playbook multi-agent và cách gọi role: `docs/MULTIAGENT_PLAYBOOK.md`
- Kiến trúc UI web: `docs/WEBSITE_UI_ARCHITECTURE.md`
- Cách web lấy dữ liệu qua API: `docs/WEBSITE_QUERY_GUIDE.md`
- Handoff DB cho website: `docs/WEBSITE_DB_HANDOFF.md`
- Kiến trúc analytics/dashboard: `docs/DASHBOARD_ANALYTICS_ARCHITECTURE.md`
- API contract crawler/ingestion: `docs/Crawl/POST_REVIEW_GUIDE.md`

## Quy tắc khi tài liệu mâu thuẫn

- Nếu `README` mâu thuẫn với một tài liệu chuyên biệt trong `docs/`, ưu tiên tài liệu chuyên biệt.
- Nếu hai tài liệu trong `docs/` mâu thuẫn, ưu tiên tài liệu được chỉ định là `Primary` trong `docs/DOCUMENT_MAP.md`.
- Nếu vẫn chưa rõ, main agent phải ghi lại quyết định mới trong một tài liệu `docs/` liên quan thay vì chỉ giữ trong chat.

## Quy tắc giảm token

- Không nạp toàn bộ `docs/` cho mọi task.
- Chỉ đọc:
  - tài liệu chuẩn chung
  - tài liệu primary của layer liên quan
  - tối đa 1-2 tài liệu phụ khi thật sự cần
- Khi handoff giữa agents, chỉ truyền:
  - quyết định
  - contract thay đổi
  - file cần sửa
  - test cần chạy

## Quy tắc output của subagent

Mỗi subagent phải trả về đúng 5 phần:

- `Scope`
- `Decision`
- `Risks`
- `Files`
- `Tests`

Không đổ raw log dài vào main thread trừ khi lỗi đó là nội dung cần quyết định.
