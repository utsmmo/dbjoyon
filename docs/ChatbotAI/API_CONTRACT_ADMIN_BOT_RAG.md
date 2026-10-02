# API Contract Cho Admin Bot Và RAG

## Mục tiêu

Tài liệu này chốt các API backend cần có để frontend admin vận hành BotAI.

Nguyên tắc:

- chia API theo module rõ ràng
- admin source tách riêng với RAG target
- không cho frontend sửa trực tiếp bảng chunk
- frontend thao tác qua backend service

## Module 1. Hotel Bot Settings

## GET `/api/v1/chatbot/admin/hotels`

Mục tiêu:

- lấy danh sách khách sạn cho admin bot

### Response tối thiểu

- `id`
- `name`
- `code`
- `bot_status`
- `default_language`
- `supported_languages`
- `confidence_threshold`
- `handoff_threshold`

## GET `/api/v1/chatbot/admin/hotels/:hotelId/settings`

Mục tiêu:

- lấy cấu hình bot của 1 khách sạn

## PUT `/api/v1/chatbot/admin/hotels/:hotelId/settings`

### Request

- `bot_status`
- `default_language`
- `supported_languages`
- `confidence_threshold`
- `handoff_threshold`
- `allow_auto_reply`
- `allow_after_hours_reply`
- `allow_price_quote`
- `allow_inventory_lookup`
- `allow_booking_status_lookup`
- `handoff_channel_code`
- `handoff_target_ref`
- `business_hours_json`
- `notes`

### Validation

- `confidence_threshold` từ `0` đến `1`
- `handoff_threshold` từ `0` đến `1`
- `bot_status` thuộc danh sách cho phép

## Module 2. Knowledge Source

## GET `/api/v1/chatbot/admin/knowledge`

### Query params

- `hotel_id`
- `document_type`
- `status`
- `language`
- `q`
- `page`
- `page_size`

### Mục tiêu

- lấy danh sách knowledge source để admin sửa

## GET `/api/v1/chatbot/admin/knowledge/:id`

Mục tiêu:

- lấy chi tiết 1 knowledge source

## POST `/api/v1/chatbot/admin/knowledge`

### Request

- `hotel_id`
- `document_type`
- `title`
- `content`
- `language`
- `status`
- `source_ref`
- `version`
- `tags_json`
- `metadata_json`

## PUT `/api/v1/chatbot/admin/knowledge/:id`

Mục tiêu:

- sửa knowledge source

## POST `/api/v1/chatbot/admin/knowledge/:id/publish`

Mục tiêu:

- chuyển trạng thái thành `published`
- ghi `published_at`
- ghi `published_by`

## POST `/api/v1/chatbot/admin/knowledge/:id/archive`

Mục tiêu:

- archive tài liệu cũ

## POST `/api/v1/chatbot/admin/knowledge/:id/duplicate`

### Request

- `target_hotel_id`
- `new_source_ref`
- `new_version`

## Module 3. Knowledge Sync

## POST `/api/v1/chatbot/admin/knowledge/:id/sync`

Mục tiêu:

- sync 1 knowledge source sang `chatbot_knowledge_documents`

### Response

- `sync_job_id`
- `status`
- `document_id`

## POST `/api/v1/chatbot/admin/knowledge/:id/reindex`

Mục tiêu:

- tạo lại chunk cho document đã sync

## GET `/api/v1/chatbot/admin/sync-jobs`

### Query params

- `hotel_id`
- `status`
- `document_type`
- `page`
- `page_size`

## GET `/api/v1/chatbot/admin/sync-jobs/:id`

Mục tiêu:

- xem chi tiết log sync

## Module 4. Channel Mapping

## GET `/api/v1/chatbot/admin/channels`

### Query params

- `hotel_id`
- `channel_type`
- `status`
- `q`

## POST `/api/v1/chatbot/admin/channels`

### Request

- `hotel_id`
- `channel_type`
- `channel_name`
- `external_channel_key`
- `page_id`
- `inbox_id`
- `routing_notes`
- `is_active`

## PUT `/api/v1/chatbot/admin/channels/:id`

## DELETE `/api/v1/chatbot/admin/channels/:id`

Nên soft delete hoặc disable trước.

## POST `/api/v1/chatbot/admin/channels/:id/test`

Mục tiêu:

- test mapping đầu vào

## Module 5. Runtime Source Registry

## GET `/api/v1/chatbot/admin/runtime-sources`

### Query params

- `hotel_id`
- `source_group`
- `is_active`

## POST `/api/v1/chatbot/admin/runtime-sources`

### Request

- `hotel_id`
- `source_group`
- `source_code`
- `source_type`
- `connection_name`
- `target_ref`
- `query_template`
- `mapping_json`
- `is_active`

## PUT `/api/v1/chatbot/admin/runtime-sources/:id`

## POST `/api/v1/chatbot/admin/runtime-sources/:id/test`

### Response

- `status`
- `checked_at`
- `sample_result`
- `error_message`

## Module 6. Conversation QA

## GET `/api/v1/chatbot/admin/conversations`

### Query params

- `hotel_id`
- `channel_type`
- `status`
- `guest_name`
- `page`
- `page_size`

## GET `/api/v1/chatbot/admin/conversations/:id/messages`

### Query params

- `include_sources=true|false`

### Mục tiêu

- xem luồng chat và evidence bot đã dùng

## GET `/api/v1/chatbot/admin/messages`

### Query params

- `hotel_id`
- `handoff_flag`
- `risk_level`
- `intent`
- `q`
- `page`
- `page_size`

## POST `/api/v1/chatbot/admin/messages/:id/feedback`

### Request

- `feedback_type`
- `feedback_label`
- `corrected_answer`
- `note`

## Module 7. Handoff

## GET `/api/v1/chatbot/admin/handoffs`

### Query params

- `hotel_id`
- `status`
- `risk_level`
- `assigned_to`
- `page`
- `page_size`

## POST `/api/v1/chatbot/admin/handoffs/:id/assign`

### Request

- `assigned_to`

## POST `/api/v1/chatbot/admin/handoffs/:id/resolve`

### Request

- `resolution_note`

## POST `/api/v1/chatbot/admin/handoffs/:id/retry-notify`

Mục tiêu:

- gửi lại notify nếu Lark fail

## Chuẩn response chung

Danh sách nên trả về kiểu:

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 20
}
```

Chi tiết nên trả về kiểu:

```json
{
  "item": {}
}
```

Mutation nên trả về kiểu:

```json
{
  "success": true,
  "message": "updated successfully",
  "item": {}
}
```

## Validation backend bắt buộc

- không cho knowledge `published` nếu thiếu:
  - `hotel_id`
  - `document_type`
  - `title`
  - `content`
  - `language`
  - `source_ref`
  - `version`
- không cho tạo channel trùng `external_channel_key`
- không cho 1 runtime source active bị trùng `hotel_id + source_group + source_code`
- không cho user không phải admin sửa config nhạy cảm

## Thứ tự BE nên làm

1. hotel settings
2. knowledge source CRUD
3. publish + sync + reindex
4. channel mapping
5. runtime source registry
6. conversation QA
7. handoff APIs

## Chốt ngắn

Nếu cần MVP sớm, BE chỉ cần hoàn thành trước 4 cụm:

1. hotel settings
2. knowledge source CRUD
3. publish + sync
4. channel mapping
