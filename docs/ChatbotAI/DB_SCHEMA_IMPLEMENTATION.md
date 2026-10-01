# DB Schema Triển Khai Admin Bot Và RAG

## Mục tiêu

Tài liệu này chốt phần database cần làm để admin vận hành được BotAI và RAG.

Phạm vi của file này:

- chỉ nói về lớp dữ liệu chatbot
- không đụng vào dữ liệu review hiện tại
- dùng chung bảng `hotels` hiện có làm master
- các bảng chatbot phải tách riêng bằng prefix `chatbot_`

## Nguyên tắc thiết kế

1. Không tạo bảng khách sạn riêng cho chatbot.
2. Mọi dữ liệu chatbot phải map về `hotels.id`.
3. Knowledge source do admin quản lý phải tách khỏi bảng RAG target.
4. Runtime data như giá, tồn phòng, booking status không được nhồi vào knowledge tĩnh.
5. Chỉ `published` mới được sync sang bảng RAG.

## Nhóm bảng cần có

Nên chia thành 4 lớp:

### 1. Master dùng chung

- `hotels`

### 2. Admin source tables

- `chatbot_knowledge_sources`
- `chatbot_runtime_sources`
- `chatbot_hotel_bot_settings`

### 3. Chatbot operational tables

- `chatbot_hotel_channels`
- `chatbot_guests`
- `chatbot_conversations`
- `chatbot_messages`
- `chatbot_guest_memory`
- `chatbot_handoff_queue`
- `chatbot_feedback_learning`

### 4. RAG target tables

- `chatbot_knowledge_documents`
- `chatbot_knowledge_chunks`
- `chatbot_knowledge_sync_jobs`

## Bảng mới nên thêm cho admin

Ba bảng dưới đây là phần triển khai còn thiếu để admin vận hành bài bản.

## 1. `chatbot_hotel_bot_settings`

Mục tiêu:

- mỗi khách sạn có cấu hình bot riêng

### Cột đề xuất

- `id`
- `hotel_id`
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
- `created_at`
- `updated_at`

### Rule

- `hotel_id` unique
- `bot_status` chỉ nhận:
  - `draft`
  - `pilot`
  - `active`
  - `paused`
- `confidence_threshold` trong khoảng `0 -> 1`
- `handoff_threshold` trong khoảng `0 -> 1`

### Index

- unique `(hotel_id)`
- index `(bot_status)`

## 2. `chatbot_knowledge_sources`

Mục tiêu:

- đây là source of truth từ admin/web cho knowledge

### Cột đề xuất

- `id`
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
- `published_at`
- `published_by`
- `updated_by`
- `created_at`
- `updated_at`

### Rule

- `hotel_id` fk về `hotels.id`
- `status` chỉ nhận:
  - `draft`
  - `review`
  - `published`
  - `archived`
- `source_ref` là bắt buộc
- `version` là bắt buộc

### Unique đề xuất

- unique `(hotel_id, document_type, source_ref, version)`

### Index đề xuất

- index `(hotel_id, status, updated_at desc)`
- index `(hotel_id, document_type, status)`
- index `(status, published_at desc)`

## 3. `chatbot_runtime_sources`

Mục tiêu:

- registry nguồn runtime để bot biết lấy giá, tồn phòng, booking status ở đâu

### Cột đề xuất

- `id`
- `hotel_id`
- `source_group`
- `source_code`
- `source_type`
- `connection_name`
- `target_ref`
- `query_template`
- `mapping_json`
- `is_active`
- `last_checked_at`
- `last_status`
- `last_error_message`
- `created_at`
- `updated_at`

### Rule

- `source_group` chỉ nhận:
  - `price`
  - `inventory`
  - `booking_status`
- `source_type` chỉ nhận:
  - `table`
  - `view`
  - `api`
- `last_status` chỉ nhận:
  - `unknown`
  - `ok`
  - `error`

### Unique đề xuất

- unique `(hotel_id, source_group, source_code)`

### Index đề xuất

- index `(hotel_id, source_group, is_active)`
- index `(source_group, last_status, last_checked_at desc)`

## Bảng operational cần rà lại

## 1. `chatbot_hotel_channels`

### Bổ sung nếu thiếu

- `routing_notes`
- `is_active`
- `created_by`
- `updated_by`

### Rule

- 1 channel chỉ map về 1 khách sạn
- nếu dùng `page_id + inbox_id`, phải định nghĩa rõ case `inbox_id is null`

## 2. `chatbot_messages`

### Rà lại

- không nên để unique toàn cục chỉ theo `external_message_id`

### Khuyến nghị

Một trong hai cách:

- unique `(conversation_id, external_message_id)`
- hoặc unique `(channel_id, external_message_id)` nếu có denormalize `channel_id`

### Cột nên có

- `role`
- `content`
- `translated_content`
- `detected_language`
- `intent`
- `confidence_score`
- `risk_level`
- `handoff_flag`
- `handoff_reason`
- `sources_used`
- `raw_payload`
- `created_at`

## 3. `chatbot_handoff_queue`

### Cần đảm bảo có

- `risk_level`
- `status`
- `assigned_to`
- `resolved_at`
- `resolution_note`

## 4. `chatbot_feedback_learning`

### Cần đảm bảo có

- `updated_at`
- `feedback_type`
- `feedback_label`
- `corrected_answer`
- `reviewed_by`

## Luồng dữ liệu chuẩn

### 1. Knowledge

`chatbot_knowledge_sources`
-> publish
-> sync job
-> `chatbot_knowledge_documents`
-> chunk
-> `chatbot_knowledge_chunks`

### 2. Inbound chat

channel
-> `chatbot_hotel_channels`
-> hotel
-> `chatbot_guests`
-> `chatbot_conversations`
-> `chatbot_messages`
-> `chatbot_handoff_queue` nếu cần

### 3. QA

conversation
-> message
-> reviewer feedback
-> `chatbot_feedback_learning`

## Migration thứ tự khuyến nghị

1. bảng admin source:
   - `chatbot_hotel_bot_settings`
   - `chatbot_knowledge_sources`
   - `chatbot_runtime_sources`
2. patch các bảng operational nếu thiếu cột hoặc unique
3. seed mặc định cho từng khách sạn
4. test index và unique

## Seed tối thiểu nên có

Cho mỗi khách sạn pilot:

- 1 dòng `chatbot_hotel_bot_settings`
- 1 channel test trong `chatbot_hotel_channels`
- 3 knowledge source mẫu:
  - `faq`
  - `policy`
  - `facility`
- 1 runtime source placeholder cho:
  - `price`
  - `inventory`
  - `booking_status`

## Query kiểm tra nhanh

### Kiểm tra settings bot

```sql
select h.name, s.bot_status, s.confidence_threshold, s.handoff_threshold
from chatbot_hotel_bot_settings s
join hotels h on h.id = s.hotel_id
order by h.name;
```

### Kiểm tra knowledge source published

```sql
select h.name, ks.document_type, ks.title, ks.language, ks.version, ks.published_at
from chatbot_knowledge_sources ks
join hotels h on h.id = ks.hotel_id
where ks.status = 'published'
order by h.name, ks.document_type, ks.updated_at desc;
```

### Kiểm tra runtime source

```sql
select h.name, rs.source_group, rs.source_code, rs.source_type, rs.last_status, rs.last_checked_at
from chatbot_runtime_sources rs
join hotels h on h.id = rs.hotel_id
order by h.name, rs.source_group;
```

## Chốt ngắn

Nếu chỉ chọn 3 bảng để làm trước, hãy làm:

1. `chatbot_knowledge_sources`
2. `chatbot_hotel_bot_settings`
3. `chatbot_runtime_sources`

Ba bảng này là nền để admin vận hành bot mà không làm rối dữ liệu review cũ.
