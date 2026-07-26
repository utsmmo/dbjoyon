# Hướng Dẫn Team Website Query Dữ Liệu Để Hiển Thị

Tài liệu này dành cho frontend/web team.

Mục tiêu:

- không query trực tiếp PostgreSQL từ internet
- đọc dữ liệu qua API public hiện có
- dùng được ngay để render website/dashboard

Base URL hiện tại:

- `https://data.datac.click`

Swagger:

- `https://data.datac.click/docs`

## 1. Nguyên tắc cho team web

Web không nên gọi trực tiếp PostgreSQL.

Luồng đúng:

```text
Website -> HTTPS API -> App backend -> PostgreSQL
```

Không dùng:

```text
Website -> PostgreSQL public
```

## 2. API chính cần dùng

### 2.1 Danh sách khách sạn

```http
GET /api/v1/hotels?limit=50&offset=0
```

Ví dụ:

```bash
curl "https://data.datac.click/api/v1/hotels?limit=50&offset=0"
```

Dùng để:

- render dropdown chọn khách sạn
- build menu/filter khách sạn
- lấy `hotel_id` để query review

Field quan trọng:

- `id`
- `hotel_code`
- `hotel_name`
- `country_code`
- `city`
- `status`

### 2.2 Danh sách review

```http
GET /api/v1/reviews?limit=20&offset=0
```

Ví dụ:

```bash
curl "https://data.datac.click/api/v1/reviews?limit=20&offset=0"
```

Có thể filter:

- `hotel_id`
- `platform_code`
- `is_bad_review`
- `reviewer_country_code`
- `rating_min`
- `rating_max`
- `date_from`
- `date_to`
- `q`
- `sort_by`
- `sort_order`

Ví dụ:

```bash
curl "https://data.datac.click/api/v1/reviews?hotel_id=155ced91-f79c-4ddc-b498-0399858aebf4&platform_code=booking&limit=20&offset=0"
```

Ví dụ đầy đủ:

```bash
curl "https://data.datac.click/api/v1/reviews?hotel_id=155ced91-f79c-4ddc-b498-0399858aebf4&platform_code=booking&reviewer_country_code=US&rating_min=7&rating_max=10&date_from=2026-07-01T00:00:00%2B07:00&date_to=2026-07-25T23:59:59%2B07:00&q=clean&sort_by=reviewed_at&sort_order=desc&limit=20&offset=0"
```

### 2.3 Danh sách bad review

```http
GET /api/v1/reviews/bad?hotel_id={hotel_id}&limit=20
```

Ví dụ:

```bash
curl "https://data.datac.click/api/v1/reviews/bad?hotel_id=155ced91-f79c-4ddc-b498-0399858aebf4&limit=20"
```

### 2.4 Thống kê review theo khách sạn/nền tảng

```http
GET /api/v1/reviews/stats?hotel_id={hotel_id}
```

Ví dụ:

```bash
curl "https://data.datac.click/api/v1/reviews/stats?hotel_id=155ced91-f79c-4ddc-b498-0399858aebf4"
```

Dùng để:

- hiển thị tổng review
- hiển thị tổng bad review
- biết review mới nhất theo từng platform

## 3. Các field web nên dùng trực tiếp

Response `GET /api/v1/reviews` hiện tại đã có các field phù hợp để render:

- `id`
- `hotel_id`
- `hotel_name`
- `platform_code`
- `external_review_id`
- `reviewer_name`
- `reviewer_country_code`
- `rating`
- `rating_scale`
- `review_title`
- `review_text`
- `translated_title_vi`
- `translated_text_vi`
- `review_language`
- `sentiment_label`
- `is_bad_review`
- `stay_date`
- `reviewed_at`
- `source_updated_at`
- `created_at`
- `updated_at`

## 4. Quy tắc hiển thị đề xuất cho frontend

### Ưu tiên nội dung tiếng Việt

Nếu có:

- `translated_title_vi`
- `translated_text_vi`

thì dùng để hiển thị chính.

Nếu không có:

- fallback sang `review_title`
- fallback sang `review_text`

### Giữ cả nội dung gốc nếu cần popup/detail

Khuyến nghị:

- card list: hiển thị bản dịch tiếng Việt
- modal/detail drawer: hiển thị thêm bản gốc

### Hiển thị rating

Luôn hiển thị theo cặp:

```text
rating / rating_scale
```

Ví dụ:

- `8 / 10`
- `4.5 / 5`

Không được hard-code toàn bộ là `/10`.

### Badge bad review

Nếu:

- `is_bad_review = true`

thì hiển thị badge:

- `Bad review`
- hoặc `Cần xử lý`

## 5. Ví dụ response để team web map UI

```json
{
  "items": [
    {
      "id": "2c849856-24da-44b6-84ae-a319a4accf64",
      "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
      "hotel_name": "Republic Airport Residences - Next to Holiday Inn",
      "platform_code": "booking",
      "external_review_id": "booking-republic-charlotte-us-2026-07-22-003",
      "reviewer_name": "Charlotte",
      "reviewer_country_code": "US",
      "rating": 8.0,
      "rating_scale": 10.0,
      "review_title": "Clean and modern",
      "review_text": "Friendly and helpful staff, resonsive, very clean, good location, modern.",
      "translated_title_vi": "Sạch sẽ và hiện đại",
      "translated_text_vi": "Nhân viên thân thiện và hữu ích, nhanh nhạy, rất sạch sẽ, vị trí tốt, hiện đại.",
      "review_language": "en",
      "sentiment_label": null,
      "is_bad_review": true,
      "stay_date": null,
      "reviewed_at": "2026-07-22T22:37:00+07:00",
      "source_updated_at": "2026-07-22T22:37:00+07:00",
      "created_at": "2026-07-22T22:59:56.249440+07:00",
      "updated_at": "2026-07-22T23:00:20.389812+07:00"
    }
  ],
  "total": 655,
  "limit": 20,
  "offset": 0
}
```

## 6. Flow frontend nhanh nhất

### Trang danh sách review

1. Gọi `GET /api/v1/hotels`
2. Cho user chọn khách sạn
3. Gọi `GET /api/v1/reviews?hotel_id=...`
4. Render card/table

### Trang bad review

1. Chọn `hotel_id`
2. Gọi `GET /api/v1/reviews/bad?hotel_id=...`
3. Render danh sách ưu tiên xử lý

### Dashboard tổng quan

1. Gọi `GET /api/v1/hotels`
2. Với từng khách sạn hoặc khi chọn khách sạn:
   - gọi `GET /api/v1/reviews/stats?hotel_id=...`
3. Hiển thị:
   - tổng review
   - tổng bad review
   - platform nào có nhiều review nhất

## 7. Ví dụ code frontend thuần JavaScript

```html
<script>
  async function loadReviews(hotelId) {
    const url = new URL("https://data.datac.click/api/v1/reviews");
    url.searchParams.set("hotel_id", hotelId);
    url.searchParams.set("limit", "20");
    url.searchParams.set("offset", "0");

    const response = await fetch(url.toString());
    if (!response.ok) {
      throw new Error("Failed to load reviews");
    }

    const data = await response.json();
    return data.items.map((item) => ({
      id: item.id,
      hotelName: item.hotel_name,
      platform: item.platform_code,
      reviewerName: item.reviewer_name,
      countryCode: item.reviewer_country_code,
      ratingText: `${item.rating ?? "-"} / ${item.rating_scale ?? "-"}`,
      title: item.translated_title_vi || item.review_title || "",
      text: item.translated_text_vi || item.review_text || "",
      originalTitle: item.review_title || "",
      originalText: item.review_text || "",
      isBadReview: item.is_bad_review,
      reviewedAt: item.reviewed_at
    }));
  }
</script>
```

## 8. Nếu team web muốn query SQL nội bộ trong LAN

Chỉ dùng khi web chạy trong cùng mạng nội bộ và được phép truy cập DB.

Query mẫu:

```sql
SELECT
    r.id,
    h.hotel_name,
    p.platform_code,
    r.reviewer_name,
    r.reviewer_country_code,
    r.rating,
    r.rating_scale,
    r.review_title,
    r.review_text,
    r.normalized_payload ->> 'translated_title_vi' AS translated_title_vi,
    r.normalized_payload ->> 'translated_text_vi' AS translated_text_vi,
    r.is_bad_review,
    r.reviewed_at
FROM reviews r
JOIN hotels h ON h.id = r.hotel_id
JOIN platforms p ON p.id = r.platform_id
WHERE r.hotel_id = CAST(:hotel_id AS uuid)
ORDER BY r.reviewed_at DESC
LIMIT 20 OFFSET 0;
```

Nhưng với hướng đang triển khai online, khuyến nghị vẫn là:

- web chỉ gọi API
- không nối trực tiếp PostgreSQL ra internet

## 9. Kết luận ngắn cho team website

Team website hiện có thể code ngay bằng các endpoint:

- `GET /api/v1/hotels`
- `GET /api/v1/reviews`
- `GET /api/v1/reviews/bad`
- `GET /api/v1/reviews/stats`

Không cần chờ thêm backend mới để bắt đầu làm trang hiển thị review.

## 10. Bộ filter mở rộng của `/api/v1/reviews`

Query params hỗ trợ:

- `hotel_id`
- `platform_code`
- `is_bad_review`
- `reviewer_country_code`
- `rating_min`
- `rating_max`
- `date_from`
- `date_to`
- `q`
- `sort_by`
- `sort_order`
- `limit`
- `offset`

Validate:

- `rating_min <= rating_max`
- `date_from <= date_to`
- `sort_by` chỉ nhận:
  - `reviewed_at`
  - `rating`
  - `created_at`
  - `hotel_name`
  - `reviewer_name`
- `sort_order` chỉ nhận:
  - `asc`
  - `desc`

Sort mặc định:

- `sort_by=reviewed_at`
- `sort_order=desc`
