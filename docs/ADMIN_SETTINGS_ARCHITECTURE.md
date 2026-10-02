# Admin Settings Architecture

## Muc tieu

Chot mot noi luu va quan ly runtime settings cho web admin.

Settings hien tai tap trung vao:

- review AI
- notification webhook

## Source of truth

- bang DB: `system_settings`
- giao dien quan ly: `Administration > Settings`
- frontend doc settings qua API web:
  - `GET /api/admin/settings`
  - `PUT /api/admin/settings/{setting_key}`
- backend goc doc settings qua API:
  - `GET /api/v1/admin/settings`
  - `PUT /api/v1/admin/settings/{setting_key}`

## Bang DB

Bang moi:

- `system_settings`

Field chinh:

- `setting_key`
- `group_code`
- `label`
- `description`
- `value_text`
- `value_type`
- `is_secret`
- `is_editable`
- `updated_by_user_id`
- `updated_at`

## Rule hien thi

- secret khong tra raw value ra frontend
- frontend chi nhan:
  - `masked_value`
  - `value = null`
- neu admin muon doi secret thi nhap lai gia tri moi
- neu de trong thi giu secret cu

## Runtime da noi vao settings

Da noi truc tiep:

- `review_ai.base_url`
- `review_ai.api_key`
- `review_ai.model`
- `review_ai.timeout_ms`

Frontend `/api/review-insights` hien tai khong doc env AI nua.
No proxy ve backend:

- `POST /api/v1/review-insights`

Backend se doc config tu `system_settings` truoc.
Neu DB chua co gia tri, baseline co the seed tu env hien tai de migrate an toan.

## Quyen

- chi role co `settings.view` moi thay settings
- chi role co `settings.manage` moi sua duoc
- default hien tai: `admin` co quyen nay

## Luu y hien tai

- backend admin API hien chua co auth server-side token dung nghia
- quyen hien dang duoc chan o tang web/admin session
- neu sau nay can harden production, can bo sung auth server-side cho admin endpoints
