# Hướng Dẫn Upload Review Agoda

Tài liệu này dành cho:

- đội crawl Agoda
- n8n workflow
- tool đồng bộ dữ liệu
- AI agent cần đẩy review Agoda vào hệ thống

Base URL production hiện tại:

- `https://data.datac.click`

Swagger:

- `https://data.datac.click/docs`

## 1. Luồng đúng để đẩy review Agoda

Không đẩy trực tiếp vào PostgreSQL.

Luồng đúng:

```text
Crawler Agoda -> API https://data.datac.click -> PostgreSQL
```

Không dùng:

```text
Crawler Agoda -> PostgreSQL:15432
```

## 2. Endpoint dùng để upload Agoda review

```http
POST /api/v1/sync/reviews/agoda
```

URL đầy đủ:

```text
https://data.datac.click/api/v1/sync/reviews/agoda
```

## 3. Trước khi upload: cần có `hotel_id`

Hệ thống không dùng tên khách sạn để upsert review.

Cần dùng đúng:

- `hotel_id`

Có 2 cách lấy:

### Cách 1: Lấy danh sách hotel đang có

```bash
curl "https://data.datac.click/api/v1/hotels?limit=200&offset=0"
```

Ví dụ response:

```json
{
  "items": [
    {
      "id": "5e6a9f53-58bb-4f69-8592-f2d77f64fe62",
      "hotel_code": "ania_airport_residences_next_to_holiday_inn",
      "hotel_name": "Ania Airport Residences - Next to Holiday Inn",
      "country_code": "VN",
      "city": "Ho Chi Minh City",
      "status": "active"
    }
  ],
  "total": 1,
  "limit": 200,
  "offset": 0
}
```

Giá trị cần dùng là:

- `items[].id`

### Cách 2: Tạo hotel mới nếu hệ thống chưa có

```bash
curl -X POST "https://data.datac.click/api/v1/hotels" \
  -H "Content-Type: application/json" \
  -d '{
    "hotel_code": "agoda_demo_hotel",
    "hotel_name": "Agoda Demo Hotel",
    "country_code": "VN",
    "city": "Da Nang",
    "status": "active",
    "metadata": {
      "source": "manual_setup",
      "agoda_url": "https://www.agoda.com/..."
    }
  }'
```

## 4. Các field Agoda nên lấy

Nếu crawl được thì nên lấy tối đa các trường sau:

- tên khách
- mã quốc gia khách, ví dụ `VN`, `US`, `DE`
- ngày review
- điểm review
- thang điểm, thường là `10`
- tiêu đề review
- nội dung review
- ngôn ngữ gốc
- ngày lưu trú nếu có
- tên phòng
- loại khách, ví dụ couple/family/solo
- số đêm nếu có
- link review hoặc link trang review
- thời điểm Agoda cập nhật review nếu có
- toàn bộ payload gốc

## 5. Mapping field Agoda vào API

| Dữ liệu Agoda | Field gửi vào API |
|---|---|
| id review bên Agoda | `external_review_id` |
| ngày review | `reviewed_at` |
| ngày tạo bên nguồn nếu có | `source_created_at` |
| ngày cập nhật bên nguồn nếu có | `source_updated_at` |
| link review | `review_url` |
| tên khách | `reviewer_name` |
| quốc gia khách dạng code | `reviewer_country_code` |
| điểm review | `rating` |
| thang điểm | `rating_scale` |
| tiêu đề | `review_title` |
| nội dung | `review_text` |
| ngôn ngữ gốc | `review_language` |
| ngày ở | `stay_date` |
| thông tin phòng/guest type/nights | `reviewer_profile` hoặc `normalized_payload` |
| dữ liệu Agoda gốc | `raw_payload` |

## 6. Quy tắc chống trùng của hệ thống

Review Agoda được chống trùng bằng unique key trong database:

```sql
(hotel_id, platform_id, external_review_id)
```

Ý nghĩa:

- cùng một review Agoda của cùng một khách sạn chỉ có 1 dòng
- upload lại nhiều lần sẽ không sinh thêm dòng mới
- nếu Agoda cập nhật nội dung hoặc metadata thì hệ thống sẽ `upsert`

Vì vậy, `external_review_id` phải ổn định và là id thật từ Agoda.

Không nên dùng:

- số thứ tự theo trang
- vị trí review trong danh sách
- id tạm do crawler tự sinh theo thời điểm

Nên dùng:

- review id thật từ Agoda
- hoặc nếu Agoda không lộ id thật, dùng một khóa ổn định do crawler tạo ra từ dữ liệu gốc

Ví dụ khóa fallback tạm chấp nhận được:

```text
agoda:{hotel_code}:{reviewer_name}:{reviewed_at}:{rating}
```

Nhưng tốt nhất vẫn là id thật từ Agoda.

## 7. Payload mẫu để upload Agoda review

```json
{
  "hotel_id": "5e6a9f53-58bb-4f69-8592-f2d77f64fe62",
  "hotel_platform_account_id": null,
  "triggered_by": "crawler_agoda_v1",
  "source_total_reviews": 128,
  "source_average_rating": 8.7,
  "source_rating_scale": 10,
  "source_review_url": "https://www.agoda.com/vi-vn/example-hotel/reviews.html",
  "source_captured_at": "2026-07-23T18:30:00+07:00",
  "source_metrics_payload": {
    "provider": "agoda",
    "hotel_score_text": "8.7/10",
    "total_reviews_text": "128 reviews"
  },
  "reviews": [
    {
      "external_review_id": "agoda-review-0001",
      "reviewed_at": "2026-07-22T09:15:00+07:00",
      "source_created_at": "2026-07-22T09:15:00+07:00",
      "source_updated_at": "2026-07-22T09:15:00+07:00",
      "review_url": "https://www.agoda.com/vi-vn/example-hotel/reviews.html",
      "reviewer_name": "Mai",
      "reviewer_country_code": "VN",
      "rating": 7,
      "rating_scale": 10,
      "review_title": "Vị trí tốt",
      "review_text": "Gần sân bay nhưng phòng cách âm chưa tốt.",
      "review_language": "vi",
      "stay_date": "2026-07-20",
      "sentiment_label": "mixed",
      "is_bad_review": true,
      "reviewer_profile": {
        "room_name": "Deluxe Double Room",
        "guest_type": "couple",
        "nights": 2
      },
      "normalized_payload": {
        "pros": "Gần sân bay",
        "cons": "Phòng cách âm chưa tốt",
        "translated_title_vi": "Vị trí tốt",
        "translated_text_vi": "Gần sân bay nhưng phòng cách âm chưa tốt."
      },
      "metadata": {
        "sync_source": "crawler_agoda_v1",
        "crawl_batch_id": "agoda-20260723-1830",
        "hotel_code": "ania_airport_residences_next_to_holiday_inn"
      },
      "raw_payload": {
        "provider": "agoda",
        "review_id": "agoda-review-0001",
        "reviewer_name": "Mai",
        "reviewer_country_code": "VN",
        "rating": 7,
        "rating_scale": 10,
        "title": "Vị trí tốt",
        "text": "Gần sân bay nhưng phòng cách âm chưa tốt.",
        "room_name": "Deluxe Double Room",
        "guest_type": "couple",
        "nights": 2,
        "source_url": "https://www.agoda.com/vi-vn/example-hotel/reviews.html"
      }
    }
  ]
}
```

## 8. Ví dụ cURL upload Agoda review

```bash
curl -X POST "https://data.datac.click/api/v1/sync/reviews/agoda" \
  -H "Content-Type: application/json" \
  -d '{
    "hotel_id": "5e6a9f53-58bb-4f69-8592-f2d77f64fe62",
    "triggered_by": "crawler_agoda_v1",
    "source_total_reviews": 128,
    "source_average_rating": 8.7,
    "source_rating_scale": 10,
    "source_review_url": "https://www.agoda.com/vi-vn/example-hotel/reviews.html",
    "source_captured_at": "2026-07-23T18:30:00+07:00",
    "reviews": [
      {
        "external_review_id": "agoda-review-0001",
        "reviewed_at": "2026-07-22T09:15:00+07:00",
        "review_url": "https://www.agoda.com/vi-vn/example-hotel/reviews.html",
        "reviewer_name": "Mai",
        "reviewer_country_code": "VN",
        "rating": 7,
        "rating_scale": 10,
        "review_title": "Vị trí tốt",
        "review_text": "Gần sân bay nhưng phòng cách âm chưa tốt.",
        "review_language": "vi",
        "is_bad_review": true,
        "reviewer_profile": {
          "room_name": "Deluxe Double Room",
          "guest_type": "couple",
          "nights": 2
        },
        "raw_payload": {
          "provider": "agoda",
          "review_id": "agoda-review-0001"
        }
      }
    ]
  }'
```

## 9. Response thành công sẽ như thế nào

Ví dụ response:

```json
{
  "sync_job_id": "7a27f760-3474-4ccd-9dcb-b8659662b7ae",
  "hotel_id": "5e6a9f53-58bb-4f69-8592-f2d77f64fe62",
  "platform_code": "agoda",
  "source_total_reviews": 128,
  "source_average_rating": 8.7,
  "source_rating_scale": 10,
  "source_review_url": "https://www.agoda.com/vi-vn/example-hotel/reviews.html",
  "source_captured_at": "2026-07-23T18:30:00+07:00",
  "estimated_new_reviews_from_source": 2,
  "stored_total_reviews_before_sync": 126,
  "stored_total_reviews_after_sync": 127,
  "fetched": 1,
  "inserted": 1,
  "updated": 0,
  "incidents_opened": 1,
  "status": "success"
}
```

Ý nghĩa nhanh:

- `inserted > 0`: có review mới
- `updated > 0`: review cũ đã tồn tại, hệ thống update lại
- `inserted = 0` và `updated > 0`: không lỗi, chỉ là dữ liệu bị trùng và đã được upsert đúng

## 10. Cách kiểm tra review Agoda đã vào DB chưa

### Xem tổng review theo hotel và platform

```bash
curl "https://data.datac.click/api/v1/reviews/stats?hotel_id=5e6a9f53-58bb-4f69-8592-f2d77f64fe62&platform_code=agoda"
```

### Xem danh sách review Agoda của một khách sạn

```bash
curl "https://data.datac.click/api/v1/reviews?hotel_id=5e6a9f53-58bb-4f69-8592-f2d77f64fe62&platform_code=agoda&limit=20&offset=0"
```

### Chỉ lấy bad review Agoda

```bash
curl "https://data.datac.click/api/v1/reviews/bad?hotel_id=5e6a9f53-58bb-4f69-8592-f2d77f64fe62&platform_code=agoda&limit=20"
```

## 11. Logic bad review hiện tại

Ngưỡng hiện tại của hệ thống là:

- `rating < 9` thì là bad review

Nghĩa là:

- 8.9 trở xuống: `is_bad_review = true`
- 9.0 trở lên: `is_bad_review = false`

Nếu crawler gửi sai `is_bad_review`, backend vẫn có thể chuẩn hóa lại theo `rating`.

## 12. Dịch tiếng Việt đang hoạt động như thế nào

Hiện tại hệ thống hỗ trợ lưu:

- nội dung gốc ở `review_title`, `review_text`
- bản dịch tiếng Việt ở `translated_title_vi`, `translated_text_vi`

Khuyến nghị cho Agoda:

- nếu crawler đã dịch sẵn thì cứ gửi luôn
- nếu crawler chưa dịch thì vẫn gửi review gốc, backend có thể xử lý dịch theo cấu hình hiện tại

Tối thiểu vẫn phải gửi:

- `review_title`
- `review_text`
- `raw_payload`

## 13. Cách dùng `source_total_reviews`

Nên gửi thêm:

- `source_total_reviews`
- `source_average_rating`
- `source_rating_scale`

Vì sau này có thể so sánh:

- tổng review Agoda hiện tại trên web
- tổng review Agoda đã lưu trong database

Ví dụ:

- Agoda hiện tại có `128`
- DB đang có `126`

Khi đó crawler biết đang thiếu khoảng `2` review mới và có thể ưu tiên lấy phần mới nhất.

## 14. Checklist tối thiểu cho bên crawl Agoda

Trước khi bàn giao, nên đảm bảo đủ các mục sau:

- lấy được `hotel_id`
- dùng đúng endpoint `POST /api/v1/sync/reviews/agoda`
- mỗi review có `external_review_id` ổn định
- mỗi review có `reviewed_at`
- mỗi review có `raw_payload`
- nếu có điểm thì gửi `rating` và `rating_scale`
- nếu có tên khách, quốc gia, tiêu đề, nội dung thì gửi hết
- nếu có room name, guest type, nights thì đưa vào `reviewer_profile` hoặc `normalized_payload`
- nên gửi `source_total_reviews`
- sau khi upload xong nên gọi API đọc lại để kiểm tra

## 15. Mẫu payload tối thiểu nếu chỉ mới crawl được ít field

```json
{
  "hotel_id": "5e6a9f53-58bb-4f69-8592-f2d77f64fe62",
  "triggered_by": "crawler_agoda_minimal",
  "reviews": [
    {
      "external_review_id": "agoda-review-0001",
      "reviewed_at": "2026-07-22T09:15:00+07:00",
      "rating": 7,
      "rating_scale": 10,
      "reviewer_name": "Mai",
      "review_title": "Vị trí tốt",
      "review_text": "Gần sân bay nhưng phòng cách âm chưa tốt.",
      "raw_payload": {
        "provider": "agoda",
        "review_id": "agoda-review-0001"
      }
    }
  ]
}
```

## 16. Kết luận ngắn

Nếu cần upload review Agoda đúng chuẩn, bên crawl chỉ cần nhớ:

1. lấy đúng `hotel_id`
2. gọi `POST /api/v1/sync/reviews/agoda`
3. dùng `external_review_id` ổn định để chống trùng
4. luôn gửi `raw_payload`
5. nên gửi thêm `source_total_reviews`, `rating`, `title`, `text`, `country`, `room_name`

Nếu cần tài liệu tổng quát hơn cho mọi nền tảng, xem thêm:

- [POST_REVIEW_GUIDE.md](D:/AutoCode/DB/Review/docs/POST_REVIEW_GUIDE.md)
- [AI_CRAWLER_API_CONTRACT.md](D:/AutoCode/DB/Review/docs/AI_CRAWLER_API_CONTRACT.md)
