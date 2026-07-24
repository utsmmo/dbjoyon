# Crawler Handoff Playbook

Tài liệu này dành cho team crawl data, n8n, hoặc automation.

Mục tiêu:

- biết cần lấy dữ liệu gì
- biết so sánh tổng review trong DB và tổng review trên OTA
- biết chỉ crawl phần review mới
- biết post vào API đúng format
- biết xử lý bad review notification an toàn

Base URL:

- `https://data.datac.click`

Swagger:

- `https://data.datac.click/docs`

## 1. Flow tổng quan

```text
1. Đảm bảo hotel đã tồn tại trong DB
2. Lấy hotel_id
3. Gọi /reviews/stats để xem DB đang có bao nhiêu review cho hotel + platform
4. Crawler đọc tổng review trên OTA
5. Tính phần chênh lệch
6. Chỉ crawl review mới nhất theo phần chênh lệch
7. Post vào /sync/reviews/{platform_code}
8. Query /reviews/bad/unnotified?channel_code=lark
9. Gửi sang Lark
10. Callback /notifications/deliveries với sent/failed
```

## 2. Lấy `hotel_id`

### Lấy danh sách hotel

```bash
curl "https://data.datac.click/api/v1/hotels?limit=100&offset=0"
```

`id` trong response là `hotel_id`.

Nếu hotel chưa có, tạo trước:

```bash
curl -X POST "https://data.datac.click/api/v1/hotels" \
  -H "Content-Type: application/json" \
  -d '{
    "hotel_code": "ania_airport_residences",
    "hotel_name": "Ania Airport Residences - Next to Holiday Inn",
    "country_code": "VN",
    "city": "Ho Chi Minh City",
    "status": "active"
  }'
```

## 3. Lấy tổng review hiện có trong DB

```bash
curl "https://data.datac.click/api/v1/reviews/stats?hotel_id=HOTEL_ID&platform_code=booking"
```

Ví dụ:

```json
{
  "items": [
    {
      "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
      "platform_code": "booking",
      "total_reviews": 50,
      "bad_reviews": 8,
      "latest_reviewed_at": "2026-07-22T22:37:00+07:00",
      "latest_source_updated_at": "2026-07-22T22:37:00+07:00"
    }
  ],
  "total": 1
}
```

## 4. So sánh với tổng review trên OTA

Ví dụ:

- DB hiện có: `50`
- Booking hiện có: `52`

Suy ra:

- đang có khoảng `2` review mới

Crawler nên:

1. vào trang review
2. lấy 2 review mới nhất
3. post vào API

Khuyến nghị thực dụng:

- nếu có khả năng trang OTA thay đổi thứ tự review, có thể lấy thêm 1-3 review đệm để an toàn
- database đã có `external_review_id` + upsert, nên lấy trùng một ít cũng không sao

## 5. Dữ liệu cần lấy từ mỗi review

### Bắt buộc

- `external_review_id`
- `reviewed_at`
- `raw_payload`

### Rất nên có

- `reviewer_name`
- `reviewer_country_code`
- `rating`
- `rating_scale`
- `review_title`
- `review_text`
- `review_language`
- `review_url`
- `source_updated_at`
- `room_name`
- `pros`
- `cons`

## 6. Mapping field để crawler sử dụng

| Dữ liệu OTA | Field API |
|---|---|
| review id | `external_review_id` |
| ngày review | `reviewed_at` |
| tên khách | `reviewer_name` |
| mã quốc gia | `reviewer_country_code` |
| điểm | `rating` |
| thang điểm | `rating_scale` |
| title | `review_title` |
| nội dung tổng hợp | `review_text` |
| ngôn ngữ | `review_language` |
| link review | `review_url` |
| tên phòng | `reviewer_profile.room_name` |
| khen | `normalized_payload.pros` |
| chê | `normalized_payload.cons` |
| full source | `raw_payload` |

## 7. Rule cho phần dịch sang tiếng Việt

Nếu backend đang bật translation:

- `TRANSLATION_PROVIDER=googletrans`
hoặc
- `TRANSLATION_PROVIDER=google_api`

thì crawler có thể chỉ gửi bản gốc.

Backend sẽ tự thêm:

- `normalized_payload.translated_title_vi`
- `normalized_payload.translated_text_vi`
- `normalized_payload.translated_pros_vi`
- `normalized_payload.translated_cons_vi`

Nếu crawler tự dịch trước cũng được, backend vẫn nhận.

## 8. Payload mẫu để post review

```json
{
  "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
  "hotel_platform_account_id": null,
  "triggered_by": "booking_crawler_v1",
  "source_total_reviews": 52,
  "reviews": [
    {
      "external_review_id": "booking-review-051",
      "reviewed_at": "2026-07-23T09:00:00+07:00",
      "source_created_at": "2026-07-23T09:00:00+07:00",
      "source_updated_at": "2026-07-23T09:00:00+07:00",
      "review_url": "https://www.booking.com/review/booking-review-051",
      "reviewer_name": "Alice",
      "reviewer_country_code": "US",
      "rating": 4,
      "rating_scale": 10,
      "review_title": "Need improvement",
      "review_text": "Front desk was slow but room was clean.",
      "review_language": "en",
      "is_bad_review": true,
      "reviewer_profile": {
        "room_name": "Deluxe Double Room",
        "country_name": "United States"
      },
      "normalized_payload": {
        "pros": "Room was clean.",
        "cons": "Front desk was slow."
      },
      "metadata": {
        "crawl_batch_id": "batch-20260723-0900"
      },
      "raw_payload": {
        "provider": "booking",
        "id": "booking-review-051"
      }
    },
    {
      "external_review_id": "booking-review-052",
      "reviewed_at": "2026-07-23T09:05:00+07:00",
      "source_created_at": "2026-07-23T09:05:00+07:00",
      "source_updated_at": "2026-07-23T09:05:00+07:00",
      "review_url": "https://www.booking.com/review/booking-review-052",
      "reviewer_name": "Bob",
      "reviewer_country_code": "DE",
      "rating": 9,
      "rating_scale": 10,
      "review_title": "Great stay",
      "review_text": "Very nice hotel and excellent staff.",
      "review_language": "en",
      "is_bad_review": false,
      "raw_payload": {
        "provider": "booking",
        "id": "booking-review-052"
      }
    }
  ]
}
```

## 9. Endpoint sync

```bash
curl -X POST "https://data.datac.click/api/v1/sync/reviews/booking" \
  -H "Content-Type: application/json" \
  -d @payload.json
```

## 10. Cách đọc response sync

Ví dụ:

```json
{
  "sync_job_id": "uuid-string",
  "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
  "platform_code": "booking",
  "source_total_reviews": 52,
  "estimated_new_reviews_from_source": 2,
  "stored_total_reviews_before_sync": 50,
  "stored_total_reviews_after_sync": 52,
  "fetched": 2,
  "inserted": 2,
  "updated": 0,
  "incidents_opened": 1,
  "status": "success"
}
```

Ý nghĩa:

- `stored_total_reviews_before_sync`: tổng review DB trước sync
- `stored_total_reviews_after_sync`: tổng review DB sau sync
- `estimated_new_reviews_from_source`: số review chênh lệch OTA so với DB trước sync
- `inserted`: số review mới thực sự được thêm
- `updated`: số review đã có và được upsert lại

## 11. Lấy bad review chưa gửi Lark

```bash
curl "https://data.datac.click/api/v1/reviews/bad/unnotified?channel_code=lark&hotel_id=HOTEL_ID&limit=20"
```

Quan trọng:

- query này không tự động đổi trạng thái review thành đã gửi
- chỉ là danh sách review cần gửi

## 12. Callback sau khi gửi Lark

### Nếu thành công

```bash
curl -X POST "https://data.datac.click/api/v1/notifications/deliveries" \
  -H "Content-Type: application/json" \
  -d '{
    "review_id": "REVIEW_UUID",
    "channel_code": "lark",
    "event_type": "bad_review",
    "delivery_status": "sent",
    "external_message_id": "lark-msg-123"
  }'
```

### Nếu thất bại

```bash
curl -X POST "https://data.datac.click/api/v1/notifications/deliveries" \
  -H "Content-Type: application/json" \
  -d '{
    "review_id": "REVIEW_UUID",
    "channel_code": "lark",
    "event_type": "bad_review",
    "delivery_status": "failed",
    "error_message": "timeout from webhook"
  }'
```

## 13. Safe notification rule

Dùng flow này:

1. query bad review
2. thử post Lark
3. thành công mới callback `sent`
4. lỗi thì callback `failed`
5. lần sau retry review `failed`

Không được:

1. query review
2. vừa query xong đã đổi trạng thái ngay
3. rồi mới gửi Lark

Vì nếu Lark lỗi thì review đó sẽ bị bỏ sót.

## 14. Rule thực dụng cho team crawl

- luôn so sánh tổng review DB và tổng review OTA trước khi crawl
- chỉ crawl phần mới nhất theo phần chênh lệch
- vẫn cho phép lấy trùng một ít để an toàn
- để database xử lý duplicate bằng upsert
- luôn gửi `raw_payload`
- luôn gửi `external_review_id`
- nếu review xấu thì để hệ thống mở incident
- sau khi gửi Lark xong phải callback kết quả thật

## 15. Đọc thêm

- [docs/POST_REVIEW_GUIDE.md](D:/AutoCode/DB/Review/docs/POST_REVIEW_GUIDE.md)
- [docs/AI_CRAWLER_API_CONTRACT.md](D:/AutoCode/DB/Review/docs/AI_CRAWLER_API_CONTRACT.md)
- [docs/DB_BACKUP_GOOGLE_DRIVE.md](D:/AutoCode/DB/Review/docs/DB_BACKUP_GOOGLE_DRIVE.md)
