# Đề Xuất Kiến Trúc Giao Diện Cho Hotel Workspace

Tài liệu này chốt hướng kiến trúc lại giao diện cho `Hotel Workspace` theo hướng:

- dễ đọc khi dùng lâu trên màn hình laptop
- ưu tiên tốc độ quét thông tin cho CRM nội bộ
- tách rõ layout, module, state và component để dễ mở rộng
- giữ UI đủ chuyên nghiệp nhưng không đi theo kiểu dashboard demo

Tài liệu này cũng bổ sung chuẩn typography/readability để team không lặp lại lỗi chữ quá nhỏ, quá nhạt hoặc quá mảnh.

## 1. Mục tiêu UI

Giao diện của `Hotel Workspace` không nên được tối ưu như landing page hoặc dashboard trình diễn.

Mục tiêu thực tế hơn:

- quản lý mở trang là đọc được nhanh
- staff xử lý review và task không bị mỏi mắt
- filter, table, detail panel phải ưu tiên tính rõ ràng hơn tính trang trí
- trạng thái, badge, warning và CTA phải có phân cấp mạnh
- layout phải đủ linh hoạt để gắn thêm module pricing, review, tasks, SOP, AI Studio

## 2. Nguyên tắc thiết kế tổng thể

### 2.1 Ưu tiên readability trước decoration

- không dùng font quá mảnh
- không dùng text dưới `12px`
- text phụ phải đủ contrast
- giảm lạm dụng uppercase + letter spacing rộng
- card và chart phải có hierarchy thị giác rõ

### 2.2 UI cho CRM nội bộ phải "dense vừa đủ"

- không để khoảng trắng lớn vô ích
- không nhồi quá nhiều số liệu cùng lúc
- giữ nhịp đọc theo khối:
  - page header
  - key actions / filters
  - core metrics
  - operational table / queue
  - detail panel

### 2.3 Trạng thái phải mang ý nghĩa vận hành

- đỏ: urgent / bad review / overdue / blocked
- cam: warning / needs attention
- xanh dương: info / navigation / active selection
- xanh lá: healthy / resolved / completed
- xám: secondary / metadata / coming soon

### 2.4 Không dùng visual style kiểu "AI-generated dashboard"

- không lạm dụng gradient
- không dùng quá nhiều badge như `Live`, `Incoming`
- không dùng pastel mờ làm mất contrast
- tránh card nào cũng cùng một cấp nhấn

## 3. Chuẩn Typography và Readability

## 3.1 Kết luận sử dụng

Phần chữ trong CRM cần được chuẩn hóa như sau:

| Thành phần | Cỡ chữ | Weight | Màu |
| --- | --- | --- | --- |
| Page title | `28-30px` | `600-700` | `#172033` |
| Card title | `16-18px` | `600` | `#172033` |
| Primary content / review title | `14px` | `500-600` | `#1F2937` |
| Secondary description | `13px` | `400-500` | `#52627A` |
| Filter / table label | `12px` | `600` | `#46556D` |
| Badge / metadata | `11-12px` | `600` | theo trạng thái |

## 3.2 Chuẩn body text

```css
body {
  font-family: Inter, Geist, ui-sans-serif, system-ui, sans-serif;
  color: #1f2937;
  font-size: 14px;
  line-height: 1.5;
}

.text-muted {
  color: #52627a;
}
```

## 3.3 Quy tắc bắt buộc

- không dùng text dưới `12px`
- không dùng `font-weight: 300` cho nội dung vận hành
- text phụ phải đạt contrast đủ rõ trên nền trắng
- uppercase chỉ nên dùng ở label ngắn hoặc badge nhỏ
- nếu dùng uppercase thì tracking phải vừa phải, không được quá rộng

## 3.4 Ứng dụng vào UI hiện tại

### Page title

- `text-[28px]`
- `font-semibold`
- `text-[#172033]`

### Card title

- `text-[16px]`
- `font-semibold`
- `text-[#172033]`

### Review title / main row content

- `text-[14px]`
- `font-medium`
- `text-[#1F2937]`

### Description / helper text

- `text-[13px]`
- `font-medium` hoặc `font-normal`
- `text-[#52627A]`

### Filter / table label

- `text-[12px]`
- `font-semibold`
- `text-[#46556D]`

## 4. Design tokens đề xuất

## 4.1 Color tokens

```css
:root {
  --bg-app: #f4f7fb;
  --bg-panel: #ffffff;
  --bg-muted: #f7f9fc;
  --text-primary: #172033;
  --text-body: #1f2937;
  --text-muted: #52627a;
  --text-label: #46556d;
  --border-subtle: rgba(148, 163, 184, 0.18);
  --accent-blue: #2563eb;
  --accent-blue-soft: #eaf2ff;
  --accent-red: #dc2626;
  --accent-amber: #d97706;
  --accent-green: #059669;
  --shadow-card: 0 14px 34px rgba(15, 23, 42, 0.06);
}
```

## 4.2 Radius và shadow

- panel chính: `24px - 28px`
- input/button/filter: `12px - 16px`
- row active: nền xanh rất nhạt, không dùng gradient mạnh
- shadow nhẹ, ưu tiên border hơn shadow

## 5. Kiến trúc Information Architecture

## 5.1 Menu cấp 1 đề xuất

```text
OVERVIEW
- Dashboard

OPERATIONS
- Pricing
- Reviews
- Tasks
- Hotels

MARKETING
- AI Studio
- Prompt Library
- Assets / Campaigns

KNOWLEDGE
- SOP & Training

REPORTS
- Operations Reports
- Review Quality Reports
- Pricing Reports

ADMINISTRATION
- Users
- Departments
- Hotels / Regions / Brands
- Roles & Permissions
- Integrations
- Settings
- Audit Logs
```

## 5.2 Route strategy đề xuất

Frontend hiện tại mới có:

- `/`
- `/admin`

Về sau nên tách rõ:

```text
/dashboard
/reviews
/reviews/[id]
/pricing
/tasks
/knowledge
/marketing/ai-studio
/marketing/prompts
/reports/operations
/reports/reviews
/reports/pricing
/admin/users
/admin/hotels
/admin/roles
/admin/settings
```

Trong giai đoạn hiện tại có thể dùng:

- `/dashboard` cho overview
- `/reviews` cho review workspace

## 6. Layout architecture đề xuất

## 6.1 App shell

App shell nên cố định và tái sử dụng cho mọi module:

- Sidebar
- Top header
- Content container
- Right-side utility area hoặc detail drawer nếu cần

## 6.2 Page composition chuẩn

Mỗi page nên theo nhịp:

1. Page header
2. Key actions
3. Sticky filter bar nếu là workspace page
4. Metrics / highlights
5. Main content
6. Detail drawer hoặc side panel

## 6.3 Hai loại page nên tách rõ

### Summary page

Ví dụ:

- dashboard
- reports

Đặc điểm:

- metrics trước
- charts sau
- table tổng hợp phía dưới

### Workspace page

Ví dụ:

- reviews
- tasks
- pricing monitoring

Đặc điểm:

- filter bar và table là trung tâm
- detail panel / drawer rất quan trọng
- action phải gần row hoặc gần panel chi tiết

## 7. Kiến trúc lại frontend hiện tại

## 7.1 Vấn đề hiện tại

Hiện frontend đang có một component lớn:

- `web-hotel-review/frontend-web/components/review-dashboard.tsx`

Điểm yếu:

- layout, view state, metrics, filters, table, detail panel nằm chung một file
- khó mở rộng sang route và module khác
- duplicate filter blocks
- khó kiểm soát design consistency

## 7.2 Hướng tách component

Đề xuất tách theo tầng:

```text
app/
  dashboard/page.tsx
  reviews/page.tsx
  layout.tsx

components/
  app-shell/
    sidebar.tsx
    topbar.tsx
    page-header.tsx
  ui/
    panel.tsx
    metric-card.tsx
    empty-state.tsx
    status-badge.tsx
    filter-field.tsx
  dashboard/
    dashboard-metrics.tsx
    dashboard-analytics.tsx
    dashboard-insights.tsx
  reviews/
    review-filters.tsx
    review-table.tsx
    review-detail-panel.tsx
    review-row.tsx
```

## 7.3 Tầng state đề xuất

Hiện chưa cần state manager phức tạp nếu scope nhỏ, nhưng nên chuẩn bị theo hướng:

- `server data`
  - hotels
  - reviews
  - analytics
- `ui state`
  - active view
  - selected review
  - current page
  - open dropdown
- `filter state`
  - draft filters
  - applied filters

Nếu tiếp tục mở rộng, nên tách:

- `filter store`
- `selection store`
- `layout store`

## 8. Module UI nên hoàn thiện trước

## 8.1 MVP UI layer

- Dashboard
- Review workspace
- Shared sidebar/header
- Shared filter controls
- Shared panels/cards/empty states

## 8.2 Phase 2 UI

- Pricing workspace
- Task workspace
- SOP pages
- Marketing AI Studio shell

## 8.3 Phase 3 UI

- Full administration workspace
- Advanced report builder
- Asset/campaign library
- Training completion workflows

## 9. Cấu trúc page đề xuất cho Review module

## 9.1 Review Overview

- page header
- top metrics
- summary analytics
- operational insights
- compact review table

## 9.2 Review Queue

- sticky filter bar
- result count + actions
- table
- right-side detail panel hoặc drawer

## 9.3 Review Detail Panel

Thứ tự ưu tiên:

1. review title
2. translated review body
3. original review
4. hotel / guest / source metadata
5. operational state
6. future actions: assign / respond / close

## 10. Bảng ưu tiên visual hierarchy

| Khu vực | Mức ưu tiên | Ghi chú |
| --- | --- | --- |
| Active filters | Cao | user phải hiểu ngay đang xem cái gì |
| Review title / selected row | Cao | nội dung vận hành chính |
| Count / status / alert badges | Cao | phục vụ quyết định nhanh |
| Card helpers / chart helper text | Trung bình | phải rõ nhưng không lấn át |
| Metadata phụ | Trung bình thấp | đủ đọc nhưng không tranh vai |
| Decorative labels | Thấp | nếu không tăng readability thì bỏ |

## 11. Nguyên tắc cho chart và table

## 11.1 Charts

- title chart: `16px semibold`
- helper text chart: `13px`
- label/bar/legend không dưới `12px`
- nếu dữ liệu ít, ưu tiên bar/list hơn chart phức tạp
- chart phải phục vụ đọc nhanh, không phải trưng bày

## 11.2 Tables

- header table: `12px semibold`
- row title: `14px medium`
- preview text: `13px`
- metadata: `12px`
- row active phải nổi rõ hơn hover
- màu chỉ dùng ở trạng thái quan trọng, không tô màu toàn bảng

## 12. Nguyên tắc component library nội bộ

Nên chuẩn hóa reusable components sớm:

- `Panel`
- `MetricCard`
- `StatusBadge`
- `SectionHeader`
- `FilterField`
- `SelectControl`
- `InputControl`
- `EmptyState`
- `LoadingState`

Mỗi component cần:

- typography mặc định rõ
- spacing nhất quán
- focus state rõ
- không tự nhúng quá nhiều logic domain

## 13. Checklist khi mình kiến trúc lại giao diện

Khi triển khai lại UI, mình sẽ bám checklist này:

1. Không dùng text nhỏ hơn `12px`
2. Không dùng text phụ có contrast quá thấp
3. Không dùng font quá mảnh cho nội dung đọc thường xuyên
4. Tách route `dashboard` và `reviews`
5. Tách app shell ra khỏi module logic
6. Tách filters, metrics, analytics, table, detail panel thành component riêng
7. Giảm toàn bộ badge và micro-label không có giá trị vận hành
8. Giữ design system đủ chắc để các module sau dùng lại
9. Ưu tiên workspace usability hơn visual effect
10. Mọi thay đổi UI phải giữ nguyên logic đang hoạt động

## 14. Kết luận

Hướng đúng cho `Hotel Workspace` là:

- typography mạnh và rõ hơn
- layout gọn, ít noise
- module hóa frontend sớm
- phân tách rõ dashboard page và workspace page
- review translation chỉ áp vào nội dung review, không ép toàn bộ UI sang tiếng Việt

Từ thời điểm này, mình sẽ là người kiến trúc lại giao diện theo các nguyên tắc trong tài liệu này, thay vì chỉ chỉnh lẻ màu hoặc spacing từng chỗ.
