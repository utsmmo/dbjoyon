# Review Categories Guide

Mục tiêu:

- lưu các category score theo từng `hotel + platform + thời điểm lấy`
- cho web lấy ra nhanh để hiển thị
- vẫn giữ được lịch sử snapshot nếu trong ngày crawl nhiều lần

## 1. Database

Đã thêm migration:

- [010_review_category_snapshots.sql](D:/AutoCode/DB/Review/db/migrations/010_review_category_snapshots.sql)

Bảng mới:

- `hotel_platform_category_snapshots`

Ý nghĩa:

- mỗi lần crawler lấy được category từ OTA thì ghi 1 snapshot
- unique theo:
  - `hotel_id`
  - `platform_id`
  - `source_captured_at`

Như vậy:

- cùng thời điểm capture thì upsert
- khác thời điểm capture thì giữ lịch sử

## 2. Payload sync mới

Endpoint sync hiện tại:

- `POST /api/v1/sync/reviews/{platform_code}`

Đã hỗ trợ thêm 2 field mới trong request:

- `source_categories`
- `source_category_payload`

### `source_categories`

Dùng cho danh sách category đã chuẩn hóa:

```json
[
  {
    "category_code": "staff",
    "category_name": "Staff",
    "score": 8.9,
    "score_scale": 10,
    "display_order": 1,
    "metadata": {
      "label_color": "#1d4ed8"
    }
  },
  {
    "category_code": "facilities",
    "category_name": "Facilities",
    "score": 8.4,
    "score_scale": 10,
    "display_order": 2,
    "metadata": {}
  }
]
```

### `source_category_payload`

Dùng để lưu full JSON gốc từ crawler:

```json
{
  "provider": "booking",
  "categories_title": "Categories",
  "items": [
    {"name": "Staff", "score": 8.9},
    {"name": "Facilities", "score": 8.4},
    {"name": "Cleanliness", "score": 8.6}
  ],
  "image_urls": [
    "https://example.com/category-image-1.jpg"
  ]
}
```

## 3. API cho web

Đã thêm endpoint:

```http
GET /api/v1/review-categories/current
```

Query params:

- `hotel_id`
- `platform_code`

Response:

```json
{
  "items": [
    {
      "hotel_id": "155ced91-f79c-4ddc-b498-0399858aebf4",
      "hotel_name": "Ania Airport Residences - Next to Holiday Inn",
      "platform_code": "booking",
      "source_captured_at": "2026-07-26T10:15:00+07:00",
      "categories": [
        {
          "category_code": "staff",
          "category_name": "Staff",
          "score": 8.9,
          "score_scale": 10,
          "display_order": 1,
          "metadata": {}
        },
        {
          "category_code": "facilities",
          "category_name": "Facilities",
          "score": 8.4,
          "score_scale": 10,
          "display_order": 2,
          "metadata": {}
        }
      ],
      "raw_payload": {
        "provider": "booking"
      },
      "metadata": {
        "triggered_by": "crawler_booking_v1"
      }
    }
  ],
  "total": 1
}
```

## 4. Cách web nên dùng

Web gọi:

```http
GET /api/v1/review-categories/current?hotel_id={hotel_id}&platform_code=booking
```

Rồi hiển thị:

- danh sách category
- điểm từng category
- `source_captured_at` để biết dữ liệu được lấy lúc nào

Nếu crawler có ảnh hoặc metadata khác:

- web có thể đọc thêm từ `raw_payload`

## 5. Lệnh migration

Nếu đang đứng ở:

```text
C:\Users\Admin\Desktop\DBv2\db\migrations
```

thì chạy:

```bash
docker exec -i hotel-review-postgres psql -U hotel_admin -d hotel_review_db < 010_review_category_snapshots.sql
```
