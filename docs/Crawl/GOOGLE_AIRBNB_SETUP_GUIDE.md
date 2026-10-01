# Google và Airbnb Setup Guide

Tài liệu này chốt cách bật `google` và `airbnb` theo đúng mô hình OTA hiện tại của hệ review.

Mục tiêu:

- không tạo schema riêng cho từng OTA
- dùng lại đúng flow đang chạy tốt của `booking`, `agoda`, `ctrip`
- chuẩn hóa cách lưu link hotel, crawl review, và post vào backend

Base URL:

- `https://data.datac.click`

## 1. Nguyên tắc chung

`google` và `airbnb` phải đi theo cùng pattern:

1. link hotel được lưu trong `hotels.metadata.source_links.<platform_code>`
2. canonical link được lưu trong `hotels.metadata.canonical_links.<platform_code>`
3. crawler đọc hotel từ `GET /api/v1/hotels`
4. crawler post về `POST /api/v1/sync/reviews/{platform_code}`
5. backend map sang `hotel_platform_accounts`
6. metrics, categories, reviews dùng lại đúng các bảng hiện có

Không tạo:

- bảng riêng cho Google
- bảng riêng cho Airbnb
- endpoint riêng cho từng hotel

## 2. Dữ liệu hotel cần có

Cho mỗi hotel, admin hoặc import manifest cần lưu:

### Google

```json
{
  "links": {
    "google": [
      "https://maps.google.com/?cid=1234567890"
    ]
  },
  "metadata": {
    "google_place_id": "ChIJxxxxxxxxxxxxxxxx"
  }
}
```

### Airbnb

```json
{
  "links": {
    "airbnb": [
      "https://www.airbnb.com/rooms/123456789"
    ]
  },
  "metadata": {
    "airbnb_room_id": "123456789"
  }
}
```

Giải thích:

- `links.google[]` và `links.airbnb[]` là dữ liệu bắt buộc để backend verify `source_link_used`
- `metadata.google_place_id` là dữ liệu khuyến nghị để crawl Google Maps ổn định hơn
- `metadata.airbnb_room_id` là dữ liệu khuyến nghị để crawl Airbnb ổn định hơn

## 3. Canonical link rule

### Google

Khuyến nghị dùng:

- canonical Google Maps place URL
- hoặc URL đại diện cố định mà crawler có thể normalize ổn định

Nếu có `google_place_id`, crawler nên ưu tiên dùng `place_id` làm định danh nội bộ.

### Airbnb

Backend hiện normalize Airbnb giống Agoda:

- chỉ giữ `scheme + host + path`
- bỏ query params tracking

Ví dụ:

- đúng: `https://www.airbnb.com/rooms/123456789`
- vẫn được normalize về đúng chuẩn nếu crawler gửi kèm query params

## 4. Field sync hiện backend đã hỗ trợ

### Metrics tổng

Backend đã có chỗ lưu:

- `source_total_reviews`
- `source_average_rating`
- `source_rating_scale`
- `source_review_url`
- `source_captured_at`
- `source_metrics_payload`

### Categories

Backend đã có chỗ lưu:

- `source_categories`
- `source_category_payload`

### Review chi tiết

Backend đã có chỗ lưu:

- `external_review_id`
- `reviewer_name`
- `reviewer_country_code`
- `rating`
- `rating_scale`
- `review_title`
- `review_text`
- `review_language`
- `reviewed_at`
- `replied_at`
- `source_created_at`
- `source_updated_at`
- `raw_payload`
- `normalized_payload`
- `metadata`

## 5. Rule reviewer country

`reviewer_country_code`:

- bắt buộc với `booking`, `agoda`, `ctrip`, `expedia`, `tripadvisor`
- được phép bỏ trống với `google`, `airbnb`

Lý do:

- Google và Airbnb thường không public quốc gia reviewer đầy đủ
- không nên gán fallback giả như `VN` nếu dữ liệu thật không có

## 6. Endpoint crawler dùng

### Lấy danh sách hotel

```bash
curl "https://data.datac.click/api/v1/hotels?limit=200&offset=0"
```

### Sync Google

```bash
curl -X POST "https://data.datac.click/api/v1/sync/reviews/google" \
  -H "Content-Type: application/json" \
  -d @google_payload.json
```

### Sync Airbnb

```bash
curl -X POST "https://data.datac.click/api/v1/sync/reviews/airbnb" \
  -H "Content-Type: application/json" \
  -d @airbnb_payload.json
```

## 7. Payload tối thiểu nên dùng

### Google

```json
{
  "hotel_id": "hotel-uuid",
  "source_link_used": "https://maps.google.com/?cid=1234567890",
  "triggered_by": "crawler",
  "source_total_reviews": 120,
  "source_average_rating": 4.6,
  "source_rating_scale": 5,
  "source_review_url": "https://maps.google.com/?cid=1234567890",
  "reviews": [
    {
      "external_review_id": "google-review-001",
      "reviewed_at": "2026-08-25T10:00:00+07:00",
      "reviewer_name": "John",
      "reviewer_country_code": null,
      "rating": 5,
      "rating_scale": 5,
      "review_text": "Very good stay",
      "raw_payload": {
        "provider": "google"
      }
    }
  ]
}
```

### Airbnb

```json
{
  "hotel_id": "hotel-uuid",
  "source_link_used": "https://www.airbnb.com/rooms/123456789",
  "triggered_by": "crawler",
  "source_total_reviews": 17,
  "source_average_rating": 4.65,
  "source_rating_scale": 5,
  "source_review_url": "https://www.airbnb.com/rooms/123456789",
  "reviews": [
    {
      "external_review_id": "airbnb-review-001",
      "reviewed_at": "2026-08-25T10:00:00+07:00",
      "reviewer_name": "Anna",
      "reviewer_country_code": null,
      "rating": 5,
      "rating_scale": 5,
      "review_text": "Great host",
      "raw_payload": {
        "provider": "airbnb"
      }
    }
  ]
}
```

## 8. Cần làm ở production

### Bước 1. Chạy migration

```powershell
type D:\AutoCode\DB\Review\db\migrations\017_enable_airbnb_and_fix_danang_beach_links.sql | docker exec -i hotel-review-postgres psql -U hotel_admin -d hotel_review_db
```

Mục đích:

- bật platform `airbnb`

### Bước 2. Deploy lại backend

Deploy lại service `data.datac.click` theo cách bạn đang dùng hiện tại.

### Bước 3. Cập nhật link hotel

Trong dữ liệu hotel:

- hotel nào có Google thì thêm `links.google[]`
- hotel nào có Airbnb thì thêm `links.airbnb[]`
- nếu có thì thêm:
  - `metadata.google_place_id`
  - `metadata.airbnb_room_id`

### Bước 4. Test thật

Test từng platform:

```bash
POST /api/v1/sync/reviews/google
POST /api/v1/sync/reviews/airbnb
```

### Bước 5. Verify lại

```bash
GET /api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=google
GET /api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=airbnb
```

## 9. Checklist chốt

- platform `airbnb` đã active
- hotel có `source_links.google` đúng
- hotel có `source_links.airbnb` đúng
- crawler gửi `source_link_used` đúng canonical link
- Google/Airbnb được phép thiếu `reviewer_country_code`
- OTA khác vẫn giữ strict country code
- metrics và categories đã vào DB
- review text đã vào DB

## 10. Nếu DB đang map sai link giữa Google và Airbnb

Nếu hotel đang bị lưu nhầm kiểu:

- link Airbnb nằm trong `source_links.google`
- hoặc link Google nằm trong `source_links.airbnb`

thì đội DB chạy playbook này:

- [AIRBNB_GOOGLE_DB_REPAIR.sql](D:/AutoCode/DB/Review/docs/Crawl/AIRBNB_GOOGLE_DB_REPAIR.sql)

Playbook đó đã gồm:

- query rà toàn bộ hotel đang map sai
- query rà `hotel_platform_accounts` đang sai platform
- block fix cho từng hotel
- query verify sau khi sửa
