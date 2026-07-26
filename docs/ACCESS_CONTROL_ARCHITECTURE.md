# Đề Xuất Kiến Trúc Phân Quyền Cho Hotel Workspace

Tài liệu này mô tả kiến trúc quyền truy cập cho nền tảng nội bộ `Hotel Workspace`.

Mục tiêu:

- hỗ trợ nhiều khách sạn, nhiều phòng ban, nhiều nhóm người dùng
- dễ mở rộng theo module mới trong tương lai
- giới hạn chặt quyền truy cập theo đúng phạm vi dữ liệu
- tránh cấp quyền quá rộng cho manager hoặc staff
- tách rõ quyền nghiệp vụ, quyền cấu hình và quyền quản trị truy cập

Tài liệu này ưu tiên tính thực tế triển khai cho chuỗi khách sạn hơn là mô hình lý thuyết thuần túy.

## 1. Nguyên tắc kiến trúc quyền

### 1.1 Mô hình đề xuất

Không dùng role cứng kiểu:

- `Front Office` = một gói quyền cố định
- `Hotel Manager` = một gói quyền cố định

Thay vào đó dùng mô hình kết hợp:

- `RBAC`: role-based access control
- `Scoped permissions`: permission có ràng buộc theo phạm vi dữ liệu
- `Action-based permissions`: quyền theo hành động cụ thể
- `Overrides`: cho phép cấp thêm hoặc chặn riêng một số quyền ngoại lệ

### 1.2 Công thức quyền hiệu lực

Quyền thực tế của một user được tính từ:

1. role được gán cho user
2. permission đi kèm role
3. scope dữ liệu đi kèm role hoặc user
4. permission grant bổ sung
5. permission deny ngoại lệ

Có thể biểu diễn:

```text
Effective Access
= Role Permissions
+ Scoped Assignments
+ User Extra Grants
- Explicit Denies
```

### 1.3 Nguyên tắc cấp quyền

- Mặc định theo `least privilege`
- `view` tách khỏi `manage`
- `export` tách khỏi `view`
- `approve`, `assign`, `close` tách khỏi `update`
- `configure` tách khỏi `manage operational data`
- `manage_access` tách khỏi `settings.manage`

### 1.4 Ba lớp quyền cần tách riêng

#### A. Operational permissions

Ví dụ:

- xem giá
- xử lý review
- tạo task
- đóng task
- phản hồi review

#### B. Configuration permissions

Ví dụ:

- chỉnh rule cảnh báo giá
- chỉnh template phản hồi review
- chỉnh SOP
- chỉnh prompt library

#### C. Access-control permissions

Ví dụ:

- tạo user
- gán role
- chỉnh permission
- gán scope hotel / region
- chỉnh settings lõi

### 1.5 Nguyên tắc kỹ thuật bắt buộc

- Mọi API kiểm tra permission ở server-side
- Frontend chỉ ẩn menu, không phải nơi quyết định quyền
- Không hard delete dữ liệu nghiệp vụ quan trọng
- Các thay đổi nhạy cảm phải có audit log
- Các thao tác nhạy cảm nên có confirmation

## 2. Hierarchy tổ chức và phạm vi dữ liệu

## 2.1 Sơ đồ hierarchy đề xuất

```text
Organization
├── Brand
│   ├── Region
│   │   ├── Hotel
│   │   └── Hotel
│   └── Shared brand assets / templates / SOP
├── Departments
│   ├── Operations
│   ├── Front Office
│   ├── Revenue / Pricing
│   ├── Marketing
│   ├── Housekeeping
│   ├── HR / Training
│   └── IT / Admin
└── Users
```

## 2.2 Cách hiểu hierarchy

### Organization

- cấp công ty / tập đoàn
- là tenant gốc của toàn bộ hệ thống

### Brand

- dùng khi có nhiều thương hiệu khách sạn
- một số asset, guideline, SOP, prompt có thể áp theo brand

### Region

- nhóm nhiều hotel theo khu vực quản lý
- phù hợp cho Regional Manager, Pricing Manager, Operations Manager

### Hotel

- đơn vị scope nghiệp vụ quan trọng nhất
- hầu hết review, task, pricing alerts đều gắn với hotel

### Department

- nên là thực thể cấp organization
- có thể map với hotel nếu cần quản lý team tại chỗ
- không nên ép mọi department nằm dưới hotel

### User

Một user có thể:

- thuộc nhiều department
- được gán nhiều hotel
- có 1 region chính hoặc nhiều vùng phụ trách
- có nhiều role
- có permission bổ sung hoặc deny ngoại lệ

## 3. Role chuẩn đề xuất

## 3.1 Super Admin

- Mục đích: quyền tối cao cấp platform
- Module: tất cả
- Actions: full manage, configure, manage access, integrations, audit
- Default scope: `organization`
- Tuyệt đối không nên thiếu: xem toàn bộ audit
- Cấp thêm khi: hầu như không cần

## 3.2 System Admin

- Mục đích: vận hành hệ thống hằng ngày
- Module: admin, hotels, users, roles, permissions, integrations, settings, audit
- Actions: quản trị hệ thống gần như đầy đủ
- Default scope: `organization`
- Tuyệt đối không nên có: quyền break-glass hoặc platform ownership nếu sau này có tách cấp
- Cấp thêm khi: cần hỗ trợ sâu module nghiệp vụ

## 3.3 Executive / Owner

- Mục đích: xem toàn cảnh điều hành
- Module: dashboard, pricing, reviews, tasks, reports, SOP
- Actions: `view`, `export`, một số `approve` nếu cần
- Default scope: `organization`
- Tuyệt đối không được có:
  - `admin.roles.manage`
  - `admin.permissions.manage`
  - `admin.hotels.manage`
  - `admin.settings.manage_core`
- Cấp thêm khi:
  - duyệt policy nội dung
  - duyệt template phản hồi cấp cao

## 3.4 Regional Manager

- Mục đích: quản lý nhiều hotel trong một region
- Module: pricing, reviews, tasks, reports, SOP
- Actions: view, assign, approve, close, export
- Default scope: `region`
- Tuyệt đối không được có:
  - full admin user access
  - role management
- Cấp thêm khi:
  - `pricing.alert.configure`
  - `reviews.template.manage`
  - `knowledge.sop.manage`

## 3.5 Hotel Manager

- Mục đích: vận hành một hoặc nhiều hotel được phân công
- Module: pricing, reviews, tasks, hotel dashboard, SOP
- Actions: view, assign, respond, close, export hotel-level
- Default scope: `selected_hotels`
- Tuyệt đối không được có:
  - region-wide full visibility nếu chưa được cấp
  - role / user manage
- Cấp thêm khi:
  - review template manage
  - non-core hotel settings manage

## 3.6 Revenue / Pricing Manager

- Mục đích: quản lý giá và cảnh báo giá
- Module: pricing, pricing reports, tasks
- Actions: view, export, manage rules, configure alerts
- Default scope: `region` hoặc `selected_hotels`
- Tuyệt đối không được có:
  - review moderation full access mặc định
  - user / role admin
- Cấp thêm khi:
  - tạo task từ pricing issue
  - cross-module analytics

## 3.7 Front Office Staff

- Mục đích: xem giá khách sạn mình, task được giao, SOP liên quan
- Module: pricing, limited reviews, assigned tasks, SOP
- Actions: view, update own task, comment
- Default scope: `hotel`
- Tuyệt đối không được có:
  - export
  - configure
  - assign người khác
  - admin settings
- Cấp thêm khi:
  - `reviews.review.respond` dạng draft support

## 3.8 Review Specialist / Guest Relations

- Mục đích: xử lý review và phản hồi khách
- Module: reviews, tasks, templates, limited reports
- Actions: view, assign, respond, close, track SLA
- Default scope: `selected_hotels` hoặc `region`
- Tuyệt đối không được có:
  - hotel admin
  - access control admin
- Cấp thêm khi:
  - manage review templates
  - approve response

## 3.9 Marketing Staff

- Mục đích: dùng AI Studio, prompt, asset, campaign
- Module: AI Studio, assets, prompt library, tasks, knowledge
- Actions: view, create, update trong phạm vi được giao
- Default scope: `selected_hotels`, `brand`, hoặc `organization`
- Tuyệt đối không được có:
  - pricing config
  - review close
  - access control admin
- Cấp thêm khi:
  - publish campaign

## 3.10 Marketing Manager

- Mục đích: quản trị tài nguyên marketing và brand governance
- Module: AI Studio, prompt library, assets, campaigns, reports, knowledge
- Actions: manage, approve, publish, export
- Default scope: `brand`, `region`, hoặc `organization`
- Tuyệt đối không được có:
  - core access control admin
- Cấp thêm khi:
  - manage training/knowledge liên quan marketing

## 3.11 Operations Manager

- Mục đích: giám sát task vận hành liên phòng ban
- Module: tasks, reviews, SOP, reports
- Actions: view, assign, approve, close, export
- Default scope: `region` hoặc `selected_hotels`
- Tuyệt đối không được có:
  - roles manage
  - system settings manage
- Cấp thêm khi:
  - SOP publish

## 3.12 Department Head

- Mục đích: quản lý team trong một department
- Module: tasks, SOP/training, limited reports
- Actions: view, assign nội bộ, approve completion
- Default scope: `department` và có thể kèm `hotel`
- Tuyệt đối không được có:
  - cross-department admin
  - organization-wide reports mặc định
- Cấp thêm khi:
  - training management

## 3.13 Training Manager

- Mục đích: quản trị SOP, đào tạo và completion tracking
- Module: knowledge, training, reports
- Actions: publish, assign training, track completion
- Default scope: `organization`, `brand`, hoặc `region`
- Tuyệt đối không được có:
  - pricing admin
  - review admin mặc định
- Cấp thêm khi:
  - department-specific governance

## 3.14 Standard Staff / Viewer

- Mục đích: truy cập hạn chế chỉ để xem
- Module: dashboard subset, assigned tasks, SOP
- Actions: view only
- Default scope: `own`, `assigned`, hoặc `hotel`
- Tuyệt đối không được có:
  - export
  - configure
  - assign
- Cấp thêm khi:
  - update own task

## 4. Permission naming convention

Chuẩn đề xuất:

```text
module.resource.action
```

Ví dụ:

```text
reviews.review.view
reviews.review.assign
reviews.review.respond
reviews.review.close
reviews.analytics.view
pricing.rate.view
pricing.rate.manage
pricing.alert.configure
tasks.task.create
tasks.task.assign
tasks.task.close
ai_studio.prompt.view
ai_studio.prompt.manage
knowledge.article.view
knowledge.article.publish
admin.users.manage
admin.hotels.manage
admin.roles.manage
admin.settings.manage
```

### 4.1 Action chuẩn nên dùng

- `view`
- `create`
- `update`
- `delete`
- `assign`
- `approve`
- `close`
- `reopen`
- `respond`
- `publish`
- `export`
- `configure`
- `manage`
- `manage_access`

### 4.2 Nguyên tắc phân loại action

#### View data

- chỉ xem, không thay đổi trạng thái

#### Create / update operational data

- tạo task
- cập nhật note
- chỉnh draft phản hồi

#### Assign / approve / close

- các bước có tác động nghiệp vụ rõ ràng
- cần tách khỏi update

#### Export

- là quyền nhạy cảm
- không mặc định đi kèm view

#### Configure

- chỉnh rule
- chỉnh template
- chỉnh alert threshold
- chỉnh integration config

#### Manage access control

- users
- roles
- permissions
- scope assignments

## 5. Permission catalog đề xuất

## 5.1 Dashboard / Reports

```text
dashboard.overview.view
dashboard.hotel.view
dashboard.region.view
dashboard.executive.view
reports.operations.view
reports.operations.export
reports.review_quality.view
reports.review_quality.export
reports.pricing.view
reports.pricing.export
```

## 5.2 Pricing

```text
pricing.rate.view
pricing.rate.export
pricing.rate.note_update
pricing.rate.manage
pricing.competitor.view
pricing.alert.view
pricing.alert.configure
pricing.rule.view
pricing.rule.manage
pricing.rule.approve
```

## 5.3 Reviews

```text
reviews.review.view
reviews.review.export
reviews.review.assign
reviews.review.respond
reviews.review.respond_approve
reviews.review.close
reviews.review.reopen
reviews.review.comment
reviews.analytics.view
reviews.analytics.export
reviews.template.view
reviews.template.manage
reviews.sla.configure
```

## 5.4 Tasks

```text
tasks.task.view
tasks.task.create
tasks.task.update
tasks.task.assign
tasks.task.close
tasks.task.reopen
tasks.task.approve
tasks.task.watch
tasks.task.export
tasks.checklist.manage
```

## 5.5 AI Studio / Marketing

```text
ai_studio.prompt.view
ai_studio.prompt.manage
ai_studio.prompt.publish
ai_studio.asset.view
ai_studio.asset.manage
ai_studio.asset.delete
ai_studio.campaign.view
ai_studio.campaign.manage
ai_studio.campaign.approve
ai_studio.brand_guideline.manage
```

## 5.6 Knowledge / SOP / Training

```text
knowledge.article.view
knowledge.article.create
knowledge.article.update
knowledge.article.publish
knowledge.article.archive
knowledge.sop.manage
knowledge.training.assign
knowledge.training.complete
knowledge.training.report_view
```

## 5.7 Hotels / Organization Structure

```text
admin.hotels.view
admin.hotels.manage
admin.brands.view
admin.brands.manage
admin.regions.view
admin.regions.manage
admin.departments.view
admin.departments.manage
```

## 5.8 Users / Roles / Access

```text
admin.users.view
admin.users.manage
admin.users.assign_scope
admin.roles.view
admin.roles.manage
admin.permissions.view
admin.permissions.manage
admin.access_override.manage
```

## 5.9 Settings / Integrations / Audit

```text
admin.settings.view
admin.settings.manage
admin.settings.manage_core
admin.integrations.view
admin.integrations.manage
admin.audit_logs.view
admin.audit_logs.export
```

## 6. Scope model

## 6.1 Scope types đề xuất

```text
own
assigned
department
hotel
selected_hotels
region
brand
organization
```

## 6.2 Ý nghĩa từng scope

### `own`

- chỉ dữ liệu do user tạo hoặc sở hữu
- ví dụ note riêng, draft riêng, completion riêng

### `assigned`

- chỉ dữ liệu được assign cho user
- ví dụ task được giao

### `department`

- dữ liệu thuộc đúng phòng ban user đang quản lý hoặc tham gia

### `hotel`

- dữ liệu của hotel user đang làm việc

### `selected_hotels`

- dữ liệu của một danh sách hotel được gán rõ ràng

### `region`

- toàn bộ hotel trong một region

### `brand`

- dữ liệu cấp thương hiệu

### `organization`

- dữ liệu toàn công ty

## 6.3 Ví dụ tình huống thực tế

- Lễ tân: `pricing.rate.view` với scope `hotel`
- Hotel Manager của 3 hotel: `reviews.review.view` với scope `selected_hotels`
- Regional Manager: `reviews.analytics.view` với scope `region`
- Marketing toàn công ty: `ai_studio.prompt.manage` với scope `organization`
- Executive: xem full organization nhưng không có `admin.roles.manage`

## 7. Permission matrix cho role chính

| Role | Scope mặc định | Giá | Review | Công việc | AI Studio | SOP / Đào tạo | Báo cáo | User / Role | Hotel / Settings |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Front Office Staff | `hotel` | View | View limited | View assigned, Update own | No access | View | No access | No access | No access |
| Hotel Manager | `selected_hotels` | Manage | View, Assign, Respond, Close | Create, Assign, Close | No access | View, limited Manage | View, Export hotel-level | No access | Limited Configure |
| Regional Manager | `region` | Manage, Configure regional rules | View, Assign, Approve, Export | Manage | No access | View, Manage regional | View, Export | No access | Limited Configure |
| Pricing Manager | `region` / `selected_hotels` | Manage, Configure, Approve | View analytics only | Create from pricing issues | No access | View | View, Export | No access | Limited pricing config |
| Marketing Staff | `selected_hotels` / `brand` | No access | No access or limited View | View assigned | Manage own-scope content | View | Limited View | No access | No access |
| Marketing Manager | `brand` / `organization` | No access | No access or limited View | Manage team tasks | Manage, Approve, Publish | Manage marketing knowledge | View, Export | No access | Limited content settings |
| Executive / Owner | `organization` | View, Export | View, Export | View | View | View | View, Export | No access | No access |
| System Admin | `organization` | Manage | Manage | Manage | Manage | Manage | View, Export | Manage | Manage |
| Super Admin | `organization` | Manage, Configure | Manage, Configure | Manage | Manage | Manage | Manage | Manage | Full Manage |

## 8. Scope matrix theo role

| Role | own | assigned | department | hotel | selected_hotels | region | brand | organization |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Front Office Staff | Yes | Yes | Optional | Yes | No | No | No | No |
| Hotel Manager | No | Yes | Optional | Optional | Yes | No | No | No |
| Regional Manager | No | Yes | Optional | Yes | Yes | Yes | No | No |
| Pricing Manager | No | Yes | Optional | Yes | Yes | Yes | Optional | No |
| Review Specialist | No | Yes | Optional | Yes | Yes | Yes | No | No |
| Marketing Staff | No | Yes | Yes | Optional | Yes | Optional | Yes | Optional |
| Marketing Manager | No | Yes | Yes | Optional | Yes | Yes | Yes | Yes |
| Operations Manager | No | Yes | Yes | Yes | Yes | Yes | No | No |
| Executive / Owner | No | No | No | Yes | Yes | Yes | Yes | Yes |
| System Admin | No | No | No | Yes | Yes | Yes | Yes | Yes |
| Super Admin | No | No | No | Yes | Yes | Yes | Yes | Yes |

## 9. Navigation theo quyền

## 9.1 Nguyên tắc render sidebar

- Chỉ hiển thị menu khi user có ít nhất 1 permission `view` vào module đó
- Chỉ hiển thị sub-page khi user có quyền vào đúng resource
- Không render menu “cho đủ chỗ”
- Nếu truy cập URL trực tiếp trái quyền:
  - API trả `403`
  - frontend hiển thị `Access denied`
  - không nên redirect âm thầm, vì dễ che lỗi cấu hình quyền

## 9.2 Sidebar cho từng nhóm role

### Front Office Staff

```text
Overview
- Dashboard

Operations
- Pricing
- My Tasks

Knowledge
- SOP & Training
```

### Hotel Manager

```text
Overview
- Dashboard

Operations
- Pricing
- Reviews
- Tasks
- Hotels

Reports
- Hotel Reports

Knowledge
- SOP & Training
```

### Regional Manager

```text
Overview
- Regional Dashboard

Operations
- Pricing
- Reviews
- Tasks
- Hotels

Reports
- Operations Reports
- Review Quality Reports
- Pricing Reports

Knowledge
- SOP & Training
```

### Marketing Staff

```text
Marketing
- AI Studio
- Prompt Library
- Assets / Campaigns

Operations
- My Tasks

Knowledge
- SOP & Training
```

### Marketing Manager

```text
Overview
- Marketing Dashboard

Marketing
- AI Studio
- Prompt Library
- Assets / Campaigns

Reports
- Marketing Reports

Knowledge
- SOP & Training
```

### Executive / Owner

```text
Overview
- Executive Dashboard

Operations
- Pricing
- Reviews
- Tasks

Reports
- Operations Reports
- Review Quality Reports
- Pricing Reports

Knowledge
- SOP & Training
```

### System Admin / Super Admin

```text
Overview
- Dashboard

Operations
- Pricing
- Reviews
- Tasks
- Hotels

Marketing
- AI Studio
- Prompt Library
- Assets / Campaigns

Knowledge
- SOP & Training

Reports
- Operations Reports
- Review Quality Reports
- Pricing Reports

Administration
- Users
- Departments
- Hotels / Regions / Brands
- Roles & Permissions
- Integrations
- Settings
- Audit Logs
```

## 10. Cấu trúc module và menu đề xuất

## 10.1 Module độc lập

- Dashboard
- Pricing
- Reviews
- Tasks
- AI Studio
- SOP & Training
- Administration

## 10.2 Sub-pages nên nằm trong module

### Pricing

- Price Check
- Competitor Comparison
- Pricing Alerts
- Pricing Rules

### Reviews

- Review Queue
- Analytics
- Templates
- SLA Tracking

### Tasks

- My Tasks
- Team Tasks
- Checklists

### AI Studio

- Prompt Library
- Assets
- Campaigns
- Brand Guidelines

### Administration

- Users
- Departments
- Hotels / Regions / Brands
- Roles & Permissions
- Integrations
- Settings
- Audit Logs

## 10.3 MVP / Phase 2 / Phase 3

### MVP

- Scoped Dashboard
- Reviews
- Tasks
- Pricing view/check
- SOP & Training basic
- Users
- Hotels / Regions / Brands
- Roles & Permissions
- Audit Logs basic

### Phase 2

- Pricing rule management
- Alert configuration
- Review AI response templates
- Review SLA automation
- Department workflows
- AI Studio
- Prompt Library
- Integration management nâng cao
- Training completion tracking

### Phase 3

- Full campaign / asset lifecycle
- Brand governance sâu
- Approval chains nhiều cấp
- Permission policy builder
- Cross-module automation engine
- Advanced anomaly detection
- Enterprise BI export layer

## 11. Data model / database schema khuyến nghị

## 11.1 Core organization tables

### `organizations`

- `id`
- `name`
- `code`
- `status`
- `created_at`
- `updated_at`

### `brands`

- `id`
- `organization_id`
- `name`
- `code`
- `status`

### `regions`

- `id`
- `organization_id`
- `brand_id` nullable
- `name`
- `code`
- `status`

### `hotels`

- `id`
- `organization_id`
- `brand_id`
- `region_id`
- `name`
- `code`
- `timezone`
- `country_code`
- `city`
- `status`
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

### `departments`

- `id`
- `organization_id`
- `name`
- `code`
- `type`
- `status`

## 11.2 User and access tables

### `users`

- `id`
- `organization_id`
- `email`
- `full_name`
- `status`
- `primary_region_id` nullable
- `primary_hotel_id` nullable
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`

### `user_departments`

- `id`
- `user_id`
- `department_id`
- `is_primary`

### `roles`

- `id`
- `organization_id`
- `name`
- `code`
- `description`
- `is_system_role`
- `status`

### `permissions`

- `id`
- `module`
- `resource`
- `action`
- `code` unique
- `description`
- `is_sensitive`

### `role_permissions`

- `id`
- `role_id`
- `permission_id`
- `scope_type_default`
- `constraints_json`

### `user_roles`

- `id`
- `user_id`
- `role_id`
- `assigned_by`
- `assigned_at`
- `expires_at` nullable

### `user_scopes`

- `id`
- `user_id`
- `scope_type`
- `target_type`
- `target_id`
- `granted_by`
- `granted_at`
- `revoked_at` nullable

Giá trị `scope_type`:

- `own`
- `assigned`
- `department`
- `hotel`
- `selected_hotels`
- `region`
- `brand`
- `organization`

Giá trị `target_type`:

- `organization`
- `brand`
- `region`
- `hotel`
- `department`
- `self`

### `user_permission_overrides`

- `id`
- `user_id`
- `permission_id`
- `effect` (`allow` hoặc `deny`)
- `scope_type`
- `target_type`
- `target_id`
- `reason`
- `granted_by`
- `granted_at`
- `expires_at` nullable

## 11.3 Config and audit tables

### `modules`

- `id`
- `code`
- `name`
- `status`
- `is_mvp`

### `settings`

- `id`
- `organization_id`
- `scope_type`
- `scope_target_id`
- `key`
- `value_json`
- `is_core`
- `updated_by`
- `updated_at`

### `integrations`

- `id`
- `organization_id`
- `hotel_id` nullable
- `provider`
- `config_json`
- `status`
- `last_sync_at`

### `audit_logs`

- `id`
- `organization_id`
- `actor_user_id`
- `action_code`
- `resource_type`
- `resource_id`
- `scope_type`
- `scope_target_id`
- `before_json`
- `after_json`
- `metadata_json`
- `ip_address`
- `user_agent`
- `created_at`

## 11.4 Metadata nên có ở bảng nghiệp vụ

Các bảng nghiệp vụ như:

- reviews
- pricing alerts
- tasks
- templates
- assets
- SOP

nên có tối thiểu:

- `organization_id`
- `hotel_id` nếu có hotel scope
- `region_id` nếu cần query nhanh
- `created_by`
- `updated_by`
- `created_at`
- `updated_at`
- `deleted_at` nullable

## 11.5 Khuyến nghị authorization engine

- Có thể cache `effective_permissions` theo user để tăng tốc
- Nhưng nguồn gốc phải truy vết được từ:
  - `user_roles`
  - `role_permissions`
  - `user_scopes`
  - `user_permission_overrides`
- `deny` phải thắng `allow` nếu cùng permission và cùng scope target

## 12. Audit log và bảo mật

## 12.1 Hành động bắt buộc audit

- ai thay đổi giá hoặc pricing rule
- ai chỉnh alert threshold
- ai assign / close / respond review
- ai chỉnh review template
- ai tạo / sửa / xóa task quan trọng
- ai chỉnh SOP, prompt, asset
- ai tạo / khóa / mở user
- ai đổi role, permission, scope
- ai export dữ liệu
- ai đổi hotel assignment của user
- ai đổi settings hoặc integration

## 12.2 Nguyên tắc bảo mật

- Không hard delete nghiệp vụ quan trọng
- Settings lõi phải tách permission riêng
- Export dữ liệu phải được log
- Các thao tác nhạy cảm cần confirmation
- Nếu có thể, dùng soft revoke thay vì hard remove để còn truy vết lịch sử

## 13. Tình huống kiểm thử phân quyền thực tế

1. Lễ tân của Hotel A mở URL pricing của Hotel B
- Kỳ vọng: `403`
- Không thấy Hotel B trong filter

2. Hotel Manager được assign 3 hotel vào review queue
- Kỳ vọng: chỉ thấy dữ liệu của 3 hotel đó
- Không thấy hotel ngoài phạm vi

3. Regional Manager có `reviews.analytics.view` scope `region`
- Kỳ vọng: xem được analytics của region
- Không truy cập được `Roles & Permissions`

4. Executive xem dashboard toàn hệ thống
- Kỳ vọng: xem và export được report
- Không chỉnh được users, roles, hotels, core settings

5. Marketing Staff scope `brand`
- Kỳ vọng: chỉ thấy prompt và asset của brand đó
- Không thấy tài nguyên restricted cấp organization nếu chưa được cấp

6. Review Specialist có `reviews.review.respond` nhưng không có `reviews.review.respond_approve`
- Kỳ vọng: tạo draft được
- Không thể approve hoặc mark final response

7. Manager được cấp thêm `reviews.template.manage`
- Kỳ vọng: chỉnh được review template
- Không chỉnh được `admin.settings.manage_core`

8. System Admin đổi scope hotel của một user
- Kỳ vọng: thay đổi có hiệu lực ngay
- Audit log lưu đầy đủ `before_json` và `after_json`

9. User có role cho phép `pricing.rate.view` nhưng có override `deny` tại Hotel X
- Kỳ vọng: vẫn xem được hotel khác
- Hotel X bị chặn

10. Front Office Staff có task được assign từ review housekeeping issue
- Kỳ vọng: xem và cập nhật task đó được
- Không xem được task của department khác nếu không assigned

## 14. Kết luận

Kiến trúc phù hợp nhất cho `Hotel Workspace` là:

- role-based nhưng không role-cứng
- permission theo action rõ ràng
- scope là lớp bắt buộc
- cho phép override có kiểm soát
- tách rõ quyền vận hành, quyền cấu hình, và quyền quản trị truy cập

Hướng này giúp hệ thống:

- đủ chặt để dùng cho nhiều hotel và nhiều phòng ban
- đủ mềm để cấp quyền theo tình huống thực tế
- đủ sạch để team backend, frontend và product cùng triển khai về sau
