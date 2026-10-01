# Hướng Dẫn N8N Gửi Review Sang Lark Và Đánh Dấu Đã Lấy

Tài liệu này dành cho đội `n8n`.

Mục tiêu:

- lấy review từ backend
- gửi sang nhóm Lark
- đánh dấu review đã được lấy
- không lấy trùng lại ở lần chạy sau

Base URL hiện tại:

- `https://data.datac.click`

Swagger:

- `https://data.datac.click/docs`

## 1. Kết luận ngắn gọn

Với kênh `larknoibo`, đội `n8n` **không cần quan tâm `event_type`**.

Chỉ cần:

1. gọi API lấy queue
2. lấy `items[].id`
3. gửi review sang Lark
4. gọi API đánh dấu đã lấy bằng chính `review_id`

Sau khi đánh dấu thành công, review đó sẽ không xuất hiện lại trong queue `larknoibo/unnotified`.

## 2. Endpoint cần dùng

### Lấy queue review chưa gửi

```text
GET /api/v1/reviews/larknoibo/unnotified
```

### Đánh dấu đã gửi xong

```text
POST /api/v1/notifications/deliveries
```

### Lưu ý

- với `channel_code = larknoibo`, backend đã hỗ trợ flow đơn giản
- không cần truyền `event_type`
- chỉ cần `review_id + channel_code + delivery_status`

## 3. Flow chuẩn cho n8n

Flow khuyến nghị:

1. HTTP Request:
   - `GET /api/v1/reviews/larknoibo/unnotified?limit=20`
2. Split Items
3. Gửi từng item sang Lark webhook
4. Nếu Lark trả thành công:
   - gọi `POST /api/v1/notifications/deliveries`
   - `channel_code = larknoibo`
   - `delivery_status = sent`
5. Nếu Lark trả lỗi:
   - gọi `POST /api/v1/notifications/deliveries`
   - `channel_code = larknoibo`
   - `delivery_status = failed`

## 4. API lấy queue

### Request mẫu

```bash
curl.exe -s "https://data.datac.click/api/v1/reviews/larknoibo/unnotified?limit=5"
```

### Ví dụ response rút gọn

```json
{
  "review_label": "all",
  "channel_code": "larknoibo",
  "event_type": "mixed_review",
  "items": [
    {
      "id": "3362eed4-1fe2-4a28-bf3b-aa9c6afd8850",
      "hotel_id": "d8732171-6ccd-4f74-8701-add3bd6100a5",
      "hotel_name": "HA3",
      "platform_code": "booking",
      "reviewer_name": "Corinna",
      "rating": 8.0,
      "rating_scale": 10.0,
      "review_status": "average",
      "review_title": "Excellent value for money",
      "review_text": "Excellent value for money...",
      "reviewed_at": "2026-08-03T12:57:59+07:00"
    }
  ],
  "total": 1,
  "limit": 5,
  "offset": 0
}
```

### Trường quan trọng

- `items[].id`: đây là `review_id` nội bộ của hệ thống
- `items[].review_status`: trạng thái đánh giá hiện tại
  - `good`
  - `average`
  - `bad`

### Không dùng nhầm

Không dùng:

- `external_review_id`

Phải dùng:

- `items[].id`

## 5. Bộ lọc có thể dùng khi lấy queue

### Mặc định

```text
GET /api/v1/reviews/larknoibo/unnotified
```

Mặc định backend sẽ:

- lấy trong `10` ngày gần đây
- lấy cả `good`, `average`, `bad`

### Các query param hỗ trợ

- `review_label=bad`
- `review_label=good`
- `review_label=all`
- `hotel_id=...`
- `platform_code=booking`
- `recent_days=10`
- `limit=20`
- `offset=0`

### Ví dụ

Lấy review của 1 khách sạn trong 10 ngày gần đây:

```bash
curl.exe -s "https://data.datac.click/api/v1/reviews/larknoibo/unnotified?hotel_id=d8732171-6ccd-4f74-8701-add3bd6100a5&recent_days=10&limit=10"
```

Lấy chỉ `bad review`:

```bash
curl.exe -s "https://data.datac.click/api/v1/reviews/larknoibo/unnotified?review_label=bad&limit=10"
```

Lấy chỉ `good review`:

```bash
curl.exe -s "https://data.datac.click/api/v1/reviews/larknoibo/unnotified?review_label=good&limit=10"
```

## 6. API đánh dấu đã lấy

### Request tối giản, đúng cho `larknoibo`

```bash
curl.exe -s -X POST "https://data.datac.click/api/v1/notifications/deliveries" ^
  -H "Content-Type: application/json" ^
  --data-binary "{\"review_id\":\"3362eed4-1fe2-4a28-bf3b-aa9c6afd8850\",\"channel_code\":\"larknoibo\",\"delivery_status\":\"sent\"}"
```

### Payload tối thiểu

```json
{
  "review_id": "3362eed4-1fe2-4a28-bf3b-aa9c6afd8850",
  "channel_code": "larknoibo",
  "delivery_status": "sent"
}
```

### Có thể gửi thêm nếu muốn lưu audit chi tiết

```json
{
  "review_id": "3362eed4-1fe2-4a28-bf3b-aa9c6afd8850",
  "channel_code": "larknoibo",
  "delivery_status": "sent",
  "target_ref": "lark_noi_bo_room_1",
  "external_message_id": "om_123456",
  "response_payload": {
    "code": 0,
    "msg": "ok"
  },
  "metadata": {
    "source": "n8n",
    "workflow": "hotel-larknoibo-broadcast"
  }
}
```

## 7. API đánh dấu gửi lỗi

Nếu gửi Lark lỗi, nên ghi lại để có log:

```bash
curl.exe -s -X POST "https://data.datac.click/api/v1/notifications/deliveries" ^
  -H "Content-Type: application/json" ^
  --data-binary "{\"review_id\":\"3362eed4-1fe2-4a28-bf3b-aa9c6afd8850\",\"channel_code\":\"larknoibo\",\"delivery_status\":\"failed\",\"error_message\":\"timeout from lark webhook\"}"
```

Lưu ý:

- trạng thái `failed` chỉ để audit
- review vẫn có thể được lấy lại ở lần sau
- chỉ khi `delivery_status = sent` thì queue mới bỏ qua review đó

## 8. Cách kiểm tra có còn bị lấy trùng không

### Bước 1

Lấy 1 review:

```bash
curl.exe -s "https://data.datac.click/api/v1/reviews/larknoibo/unnotified?limit=1"
```

### Bước 2

Lấy `items[0].id`, ví dụ:

```text
3362eed4-1fe2-4a28-bf3b-aa9c6afd8850
```

### Bước 3

Post đánh dấu:

```bash
curl.exe -s -X POST "https://data.datac.click/api/v1/notifications/deliveries" ^
  -H "Content-Type: application/json" ^
  --data-binary "{\"review_id\":\"3362eed4-1fe2-4a28-bf3b-aa9c6afd8850\",\"channel_code\":\"larknoibo\",\"delivery_status\":\"sent\"}"
```

### Bước 4

Gọi lại queue:

```bash
curl.exe -s "https://data.datac.click/api/v1/reviews/larknoibo/unnotified?limit=1"
```

Kết quả mong đợi:

- review vừa đánh dấu sẽ không còn xuất hiện lại

## 9. Khi nào cần `event_type`

### Với `larknoibo`

Không cần.

### Với các kênh khác như `lark`

Vẫn nên giữ `event_type` vì flow cũ còn dùng:

- `bad_review`
- `good_review`

Vì vậy đội `n8n` chỉ áp dụng tài liệu rút gọn này cho:

- `channel_code = larknoibo`

## 10. Gợi ý mapping node trong n8n

### Node 1: Get Queue

- Method: `GET`
- URL: `https://data.datac.click/api/v1/reviews/larknoibo/unnotified`
- Query:
  - `limit=20`
  - `recent_days=10`

### Node 2: Split Items

- tách từng review

### Node 3: Send Lark Message

- gửi sang webhook Lark nội bộ

### Node 4: If Success?

Nếu Lark trả:

- `code = 0`

thì đi nhánh thành công

### Node 5A: Mark Delivery Sent

- Method: `POST`
- URL: `https://data.datac.click/api/v1/notifications/deliveries`
- Body JSON:

```json
{
  "review_id": "={{ $json.id }}",
  "channel_code": "larknoibo",
  "delivery_status": "sent"
}
```

### Node 5B: Mark Delivery Failed

- Method: `POST`
- URL: `https://data.datac.click/api/v1/notifications/deliveries`
- Body JSON:

```json
{
  "review_id": "={{ $json.id }}",
  "channel_code": "larknoibo",
  "delivery_status": "failed",
  "error_message": "={{ $json.error || 'unknown lark error' }}"
}
```

## 11. Các lỗi hay gặp

### Lỗi 1: Dùng `external_review_id` để đánh dấu

Sai vì:

- backend cần `review_id` nội bộ

Đúng là:

- dùng `items[].id`

### Lỗi 2: Gửi xong Lark nhưng không gọi API mark

Hậu quả:

- queue lần sau lấy lại đúng review đó

### Lỗi 3: Đánh dấu `failed` nhưng nghĩ là đã bỏ khỏi queue

Không đúng.

Chỉ `sent` mới loại review khỏi queue.

### Lỗi 4: Cố truyền `event_type` cho `larknoibo` rồi tự rối flow

Hiện tại với `larknoibo`:

- không cần `event_type`
- bỏ luôn cho đơn giản

## 12. Mẫu quy ước làm việc cho đội n8n

Quy ước ngắn:

- lấy queue từ `GET /api/v1/reviews/larknoibo/unnotified`
- đọc `items[].id`
- gửi message sang Lark
- nếu thành công thì `POST /api/v1/notifications/deliveries`
- body tối thiểu:
  - `review_id`
  - `channel_code = larknoibo`
  - `delivery_status = sent`

## 13. Câu lệnh test nhanh

### Lấy 3 review mới nhất trong queue

```bash
curl.exe -s "https://data.datac.click/api/v1/reviews/larknoibo/unnotified?limit=3"
```

### Đánh dấu 1 review là đã lấy

```bash
curl.exe -s -X POST "https://data.datac.click/api/v1/notifications/deliveries" ^
  -H "Content-Type: application/json" ^
  --data-binary "{\"review_id\":\"REVIEW_ID\",\"channel_code\":\"larknoibo\",\"delivery_status\":\"sent\"}"
```

### Kiểm tra lại queue

```bash
curl.exe -s "https://data.datac.click/api/v1/reviews/larknoibo/unnotified?limit=3"
```

---

Nếu sau này cần thêm 1 kênh khác như:

- `larksale`
- `larkmanager`
- `slackinternal`

thì có thể giữ đúng cùng mô hình này:

- mỗi kênh là 1 `channel_code`
- queue lấy theo `channel_code`
- sau khi gửi xong thì mark lại theo `review_id + channel_code`
