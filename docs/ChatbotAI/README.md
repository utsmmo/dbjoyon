# Chatbot AI PostgreSQL Guide

## Mục tiêu

Tài liệu này là bản duy nhất để bên chatbot làm việc với database của dự án review hiện tại.

Chốt cứng:

- Dự án này dùng `PostgreSQL`
- Không dùng `MySQL`
- Không tạo lại danh sách khách sạn mới
- Dùng chung bảng `hotels` làm nguồn sự thật
- Chatbot chỉ tham chiếu `hotel_id`

## Kết nối database

Bot chỉ cần kết nối vào chính database PostgreSQL đang chạy của dự án này.

Ví dụ format:

```env
DATABASE_URL=postgresql://hotel_admin:hotel_admin_123@postgres:5432/hotel_review_db
```

Nếu chạy ngoài Docker thì đổi host `postgres` thành IP hoặc domain PostgreSQL thực tế.

Ví dụ:

```env
DATABASE_URL=postgresql://hotel_admin:hotel_admin_123@<db-host>:5432/hotel_review_db
```

## Nguyên tắc dữ liệu

1. Không tạo bảng khách sạn riêng cho chatbot nếu chỉ trùng danh sách khách sạn.
2. Bảng `hotels` hiện tại là master.
3. Mọi dữ liệu chatbot phải map về `hotel_id`.
4. Không để chatbot tự tạo khách sạn mới.
5. Nếu cần tách riêng sau này thì chỉ tách phần bảng chatbot, không tách `hotels` trước.

## Cách tổ chức an toàn

Khuyến nghị tạo nhóm bảng riêng cho chatbot theo prefix `chatbot_`.

Ví dụ:

- `chatbot_hotel_channels`
- `chatbot_guests`
- `chatbot_conversations`
- `chatbot_messages`
- `chatbot_knowledge_documents`
- `chatbot_knowledge_chunks`
- `chatbot_guest_memory`
- `chatbot_handoff_queue`
- `chatbot_feedback_learning`
- `chatbot_knowledge_sync_jobs`

## Các bảng chatbot nên có

### 1. `chatbot_hotel_channels`

Dùng để map từng page, inbox, OTA, hoặc nguồn chat về đúng khách sạn.

Trường tối thiểu:

- `id`
- `hotel_id`
- `channel_type`
- `channel_name`
- `external_channel_key`
- `status`
- `created_at`
- `updated_at`

Ràng buộc bắt buộc:

- foreign key `hotel_id -> hotels.id`
- unique `external_channel_key`
- index `(hotel_id, channel_type, status)`

### 2. `chatbot_guests`

Dùng để lưu khách nhắn tin.

Trường tối thiểu:

- `id`
- `external_guest_key`
- `display_name`
- `phone`
- `email`
- `created_at`
- `updated_at`

Ràng buộc bắt buộc:

- unique `external_guest_key`
- index `(display_name)`
- index `(phone)`
- index `(email)`

### 3. `chatbot_conversations`

Dùng để lưu từng phiên chat.

Trường tối thiểu:

- `id`
- `hotel_id`
- `channel_id`
- `guest_id`
- `external_conversation_id`
- `status`
- `last_message_at`
- `metadata_json`
- `created_at`
- `updated_at`

Ràng buộc bắt buộc:

- foreign key `hotel_id -> hotels.id`
- foreign key `channel_id -> chatbot_hotel_channels.id`
- foreign key `guest_id -> chatbot_guests.id`
- unique `(channel_id, external_conversation_id)`
- index `(hotel_id, status, last_message_at desc)`

### 4. `chatbot_messages`

Dùng để lưu toàn bộ tin nhắn guest, bot, hoặc staff.

Trường tối thiểu:

- `id`
- `conversation_id`
- `external_message_id`
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

Giải thích thêm:

- `role`: chỉ nên dùng 1 trong 4 giá trị `guest`, `bot`, `staff`, `system`
- `risk_level`: low, medium, high để biết mức độ rủi ro của câu trả lời
- `handoff_reason`: lý do bot đẩy sang người thật
- `sources_used`: bot đã dùng tài liệu hoặc nguồn nào để trả lời

Ràng buộc bắt buộc:

- foreign key `conversation_id -> chatbot_conversations.id`
- unique `external_message_id`
- index `(conversation_id, created_at)`
- index `(handoff_flag, risk_level, created_at desc)`

Chuẩn dữ liệu khuyến nghị:

- `role` chỉ nhận: `guest`, `bot`, `staff`, `system`
- `risk_level` chỉ nhận: `low`, `medium`, `high`
- `confidence_score` nên giới hạn trong khoảng `0 -> 1`

### 5. `chatbot_knowledge_documents`

Dùng để lưu tài liệu nguồn cho bot.

Trường tối thiểu:

- `id`
- `hotel_id`
- `document_type`
- `title`
- `language`
- `source`
- `source_ref`
- `content_raw`
- `version`
- `is_active`
- `metadata_json`
- `created_at`
- `updated_at`

Ràng buộc bắt buộc:

- foreign key `hotel_id -> hotels.id`
- unique `(hotel_id, document_type, source_ref, version)`
- index `(hotel_id, document_type, is_active)`

### 6. `chatbot_knowledge_chunks`

Dùng để lưu chunk phục vụ retrieval.

Trường tối thiểu:

- `id`
- `document_id`
- `hotel_id`
- `language`
- `chunk_order`
- `chunk_text`
- `vector_ref`
- `keywords`
- `metadata_json`
- `created_at`

Ghi chú:

- Nếu sau này dùng `pgvector` thì có thể thêm cột `embedding`
- Hiện tại chưa bắt buộc

Ràng buộc bắt buộc:

- foreign key `document_id -> chatbot_knowledge_documents.id`
- foreign key `hotel_id -> hotels.id`
- unique `(document_id, chunk_order)`
- index `(hotel_id, language)`

### 7. `chatbot_guest_memory`

Dùng để lưu memory dài hạn của khách theo từng khách sạn.

Trường tối thiểu:

- `id`
- `guest_id`
- `hotel_id`
- `language_preference`
- `special_preferences`
- `important_notes`
- `last_stay_info`
- `memory_version`
- `updated_by`
- `created_at`
- `updated_at`

Ràng buộc bắt buộc:

- foreign key `guest_id -> chatbot_guests.id`
- foreign key `hotel_id -> hotels.id`
- unique `(guest_id, hotel_id)`
- index `(hotel_id, updated_at desc)`

### 8. `chatbot_handoff_queue`

Dùng để lưu các case bot phải chuyển sang người thật.

Trường tối thiểu:

- `id`
- `conversation_id`
- `hotel_id`
- `message_id`
- `reason`
- `confidence_score`
- `risk_level`
- `priority`
- `status`
- `assigned_to`
- `assigned_at`
- `resolved_at`
- `resolution_note`
- `created_at`
- `updated_at`

Ràng buộc bắt buộc:

- foreign key `conversation_id -> chatbot_conversations.id`
- foreign key `hotel_id -> hotels.id`
- foreign key `message_id -> chatbot_messages.id`
- index `(hotel_id, status, priority, created_at desc)`
- index `(assigned_to, status, created_at desc)`

Chuẩn dữ liệu khuyến nghị:

- `status` chỉ nhận: `queued`, `sent_to_lark`, `acknowledged`, `resolved`, `cancelled`
- `risk_level` chỉ nhận: `low`, `medium`, `high`
- `confidence_score` nên giới hạn trong khoảng `0 -> 1`

### 9. `chatbot_feedback_learning`

Dùng để lưu phản hồi đúng hoặc sai để cải thiện bot sau này.

Trường tối thiểu:

- `id`
- `hotel_id`
- `conversation_id`
- `message_id`
- `bot_answer`
- `staff_corrected_answer`
- `outcome`
- `improvement_type`
- `root_cause`
- `notes`
- `reviewed_by`
- `created_at`

Ràng buộc bắt buộc:

- foreign key `hotel_id -> hotels.id`
- foreign key `conversation_id -> chatbot_conversations.id`
- foreign key `message_id -> chatbot_messages.id`
- index `(hotel_id, outcome, created_at desc)`

Chuẩn dữ liệu khuyến nghị:

- `outcome` chỉ nhận: `correct`, `partial`, `wrong`
- `improvement_type` nên dùng tập giá trị ổn định như:
  - `knowledge`
  - `prompt`
  - `routing`
  - `policy`
  - `runtime_data`

### 10. `chatbot_knowledge_sync_jobs`

Dùng để theo dõi các job sync dữ liệu từ website hoặc admin sang knowledge của chatbot.

Trường tối thiểu:

- `id`
- `hotel_id`
- `job_type`
- `source_name`
- `source_ref`
- `status`
- `input_ref`
- `output_ref`
- `error_message`
- `started_at`
- `finished_at`
- `created_at`
- `updated_at`

Ràng buộc bắt buộc:

- foreign key `hotel_id -> hotels.id`
- index `(hotel_id, job_type, status, created_at desc)`
- index `(source_name, source_ref, created_at desc)`

## Unique, foreign key, và index phải chốt ngay từ đầu

Đây là các rule tối thiểu không được bỏ qua khi thiết kế schema:

- `chatbot_hotel_channels.external_channel_key` phải unique
- `chatbot_guests.external_guest_key` phải unique
- `chatbot_conversations(channel_id, external_conversation_id)` phải unique
- `chatbot_messages.external_message_id` phải unique
- `chatbot_guest_memory(guest_id, hotel_id)` phải unique
- `chatbot_knowledge_documents(hotel_id, document_type, source_ref, version)` phải unique
- `chatbot_knowledge_chunks(document_id, chunk_order)` phải unique

Tất cả bảng có tham chiếu khách sạn phải foreign key về `hotels.id`.

## Dữ liệu nào không được đóng cứng trong knowledge

Không đưa các dữ liệu thay đổi liên tục vào tài liệu tĩnh:

- giá phòng
- tồn phòng
- booking status
- khuyến mãi realtime
- surcharge theo ngày

Các dữ liệu này phải lấy từ query runtime hoặc API runtime.

## Source of truth cho knowledge

Với dự án này, source of truth cho knowledge nên chốt như sau:

- `hotels`: thông tin khách sạn master
- website hoặc admin: nơi người dùng sửa nội dung nghiệp vụ
- `chatbot_knowledge_documents`: bản đã chuẩn hóa để bot đọc
- `chatbot_knowledge_chunks`: bản chunk sau khi tách nhỏ để retrieval

Yêu cầu bắt buộc với dữ liệu nguồn sync sang knowledge:

- phải có `source_ref` để truy ngược về bản ghi nguồn
- phải có `updated_at` để workflow chỉ sync phần thay đổi
- nên có `updated_by` nếu hệ thống admin đang hỗ trợ
- không được sửa trực tiếp ở `chatbot_knowledge_chunks`

Các nhóm dữ liệu nên sync vào knowledge:

- mô tả khách sạn
- chính sách check-in, check-out
- chính sách trẻ em
- chính sách phụ thu
- breakfast
- airport transfer
- tiện ích
- FAQ
- SOP vận hành

Các nhóm dữ liệu không sync cứng vào knowledge:

- giá theo ngày
- tồn phòng
- booking status
- khuyến mãi realtime
- dữ liệu thay đổi theo giờ

## Luồng sync knowledge

Luồng chuẩn:

```text
website/admin update
-> lưu dữ liệu gốc ở nguồn quản trị
-> tạo hoặc cập nhật chatbot_knowledge_documents
-> tách chunk sang chatbot_knowledge_chunks
-> re-index nếu có vector search
-> bot đọc knowledge mới ở runtime
```

Rule vận hành:

1. Người dùng sửa dữ liệu ở website hoặc admin trước.
2. Không sửa trực tiếp trong `chatbot_knowledge_chunks`.
3. Nếu tài liệu đổi, phải tăng `version` hoặc cập nhật `updated_at`.
4. Mỗi lần sync phải ghi 1 record vào `chatbot_knowledge_sync_jobs`.
5. Nếu sync lỗi, phải giữ lại `error_message` để debug.

## Luồng làm việc cho bên bot

Luồng chuẩn:

```text
1. Đọc danh sách khách sạn từ bảng master `hotels`
2. Map channel hoặc page chat về đúng `hotel_id`
3. Tạo conversation
4. Lưu message
5. Nếu cần knowledge thì đọc từ bảng chatbot_knowledge_*
6. Nếu confidence thấp thì đẩy sang handoff queue
7. Nếu tài liệu khách sạn đổi thì sync lại knowledge
```

## Điều kiện trước khi bot bắt đầu xử lý database

Bên bot chỉ bắt đầu ghi database khi đủ 5 điều kiện:

1. Đọc được database PostgreSQL
2. Xác nhận bảng `hotels` đang là source of truth
3. Có mapping channel về đúng `hotel_id`
4. Có khóa chống trùng cho:
   - `external_channel_key`
   - `external_conversation_id`
   - `external_message_id`
5. Đã chốt dữ liệu nào là knowledge tĩnh, dữ liệu nào là runtime

## Checklist cực ngắn trước khi chạy thật

- [ ] Kết nối được PostgreSQL
- [ ] Đọc được bảng `hotels`
- [ ] Không tự tạo khách sạn mới
- [ ] Mọi conversation đều map về `hotel_id`
- [ ] Mọi message có khóa chống trùng
- [ ] Có `created_at` và `updated_at`
- [ ] Tách dữ liệu chatbot bằng prefix `chatbot_`

## Lệnh cho bên bot

### 1. Kiểm tra bảng chatbot đã tạo xong chưa

```bat
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "\dt chatbot*"
```

### 2. Kiểm tra danh sách khách sạn master để map `hotel_id`

```bat
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, hotel_code, hotel_name from hotels order by hotel_name;"
```

### 3. Thứ tự ghi dữ liệu chuẩn cho bot

Bot phải ghi theo đúng thứ tự này:

1. `chatbot_hotel_channels`
2. `chatbot_guests`
3. `chatbot_conversations`
4. `chatbot_messages`
5. nếu cần thì `chatbot_handoff_queue`
6. nếu cần feedback thì `chatbot_feedback_learning`
7. nếu sync knowledge thì `chatbot_knowledge_documents -> chatbot_knowledge_chunks -> chatbot_knowledge_sync_jobs`

### 4. Query tạo channel mẫu

```sql
INSERT INTO chatbot_hotel_channels (
    hotel_id,
    channel_type,
    channel_name,
    external_channel_key,
    status
)
VALUES (
    '<hotel_id>',
    'pancake',
    'Pancake Booking Inbox',
    'pancake:booking:hotel-a:main',
    'active'
)
ON CONFLICT (external_channel_key) DO UPDATE
SET
    hotel_id = EXCLUDED.hotel_id,
    channel_type = EXCLUDED.channel_type,
    channel_name = EXCLUDED.channel_name,
    status = EXCLUDED.status,
    updated_at = NOW()
RETURNING id;
```

### 5. Query tạo guest mẫu

```sql
INSERT INTO chatbot_guests (
    external_guest_key,
    display_name,
    phone,
    email
)
VALUES (
    'guest:lark:12345',
    'Test Guest',
    NULL,
    NULL
)
ON CONFLICT (external_guest_key) DO UPDATE
SET
    display_name = EXCLUDED.display_name,
    phone = EXCLUDED.phone,
    email = EXCLUDED.email,
    updated_at = NOW()
RETURNING id;
```

### 6. Query tạo conversation mẫu

```sql
INSERT INTO chatbot_conversations (
    hotel_id,
    channel_id,
    guest_id,
    external_conversation_id,
    status,
    last_message_at
)
VALUES (
    '<hotel_id>',
    '<channel_id>',
    '<guest_id>',
    'conv:lark:10001',
    'open',
    NOW()
)
ON CONFLICT (channel_id, external_conversation_id) DO UPDATE
SET
    guest_id = EXCLUDED.guest_id,
    status = EXCLUDED.status,
    last_message_at = EXCLUDED.last_message_at,
    updated_at = NOW()
RETURNING id;
```

Ghi chú:

- Sau bước này bot phải lấy `conversation_id` từ kết quả `RETURNING id`
- `conversation_id` này sẽ được dùng tiếp khi insert vào `chatbot_messages`

### 7. Query tạo message mẫu

```sql
INSERT INTO chatbot_messages (
    conversation_id,
    external_message_id,
    role,
    content,
    translated_content,
    detected_language,
    intent,
    confidence_score,
    risk_level,
    handoff_flag,
    handoff_reason,
    sources_used,
    raw_payload
)
VALUES (
    '<conversation_id>',
    'msg:lark:90001',
    'guest',
    'Xin chao, toi muon hoi gio check-in',
    NULL,
    'vi',
    'check_in_policy',
    0.98,
    'low',
    FALSE,
    NULL,
    '[]'::jsonb,
    '{}'::jsonb
)
ON CONFLICT (external_message_id) DO NOTHING;
```

### 8. Query kiểm tra bot đã ghi đúng chưa

```bat
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, hotel_id, channel_type, channel_name, external_channel_key from chatbot_hotel_channels order by created_at desc limit 10;"
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, external_guest_key, display_name from chatbot_guests order by created_at desc limit 10;"
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, hotel_id, channel_id, guest_id, external_conversation_id, status from chatbot_conversations order by created_at desc limit 10;"
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, conversation_id, external_message_id, role, created_at from chatbot_messages order by created_at desc limit 20;"
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, conversation_id, hotel_id, status, priority, created_at from chatbot_handoff_queue order by created_at desc limit 20;"
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, hotel_id, document_type, title, version, is_active, updated_at from chatbot_knowledge_documents order by updated_at desc limit 20;"
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, document_id, hotel_id, chunk_order, created_at from chatbot_knowledge_chunks order by created_at desc limit 20;"
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, hotel_id, job_type, status, created_at from chatbot_knowledge_sync_jobs order by created_at desc limit 20;"
docker exec -it joyon-postgres psql -U hotel_admin -d hotel_review_db -c "select id, hotel_id, conversation_id, outcome, improvement_type, created_at from chatbot_feedback_learning order by created_at desc limit 20;"
```

### 9. Rule bắt buộc cho bên bot

- không tự tạo khách sạn mới
- luôn lấy `hotel_id` từ bảng `hotels`
- luôn upsert bằng khóa unique đã chốt
- nếu retry webhook thì không được tạo conversation hoặc message trùng
- không ghi knowledge trực tiếp vào chunk nếu chưa có document nguồn
- nếu dữ liệu nghiệp vụ đổi ở admin thì sync lại knowledge, không sửa tay ở chunk

## Kết luận

Với dự án này, hướng đúng là:

- dùng chung `PostgreSQL`
- dùng chung database hiện tại
- giữ `hotels` làm master
- chatbot chỉ tham chiếu `hotel_id`
- tạo nhóm bảng `chatbot_*` để xử lý riêng

Đây là file duy nhất bên bot cần đọc trước khi bắt đầu làm database.
