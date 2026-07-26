# Backend Analytics Task For Web Hotel Review

Tài liệu này là bản chốt để team DB/backend triển khai nhánh analytics cho dashboard web hotel review.

## Mục tiêu

- dashboard không lệch số với review list
- không còn tình trạng `total` lớn nhưng chart chỉ tính từ vài chục row của page hiện tại
- analytics load nhanh hơn rõ rệt
- tách rõ `review detail path` và `analytics path`

## 1. Nguyên tắc bắt buộc

### 1.1 Review detail path

`GET /api/v1/reviews` chỉ dùng cho:

- list review
- search
- filter
- sort
- pagination

### 1.2 Analytics path

Dashboard analytics không được query trực tiếp từ raw `reviews` mỗi request.

Phải đọc từ aggregate tables:

- `review_dashboard_current_metrics`
- `review_dashboard_daily_metrics`
- `review_dashboard_daily_country_metrics`
- `review_dashboard_daily_score_buckets`

## 2. Phase 1 cần 5 endpoint

- `GET /api/v1/reviews/summary`
- `GET /api/v1/reviews/country-breakdown`
- `GET /api/v1/reviews/hotel-breakdown`
- `GET /api/v1/reviews/score-buckets`
- `GET /api/v1/reviews/daily-trend`

## 3. Filter phase 1

### `GET /api/v1/reviews/summary`

- `hotel_id`
- `platform_code`
- `date_from`
- `date_to`

### `GET /api/v1/reviews/country-breakdown`

- `hotel_id`
- `platform_code`
- `date_from`
- `date_to`
- `limit`

### `GET /api/v1/reviews/hotel-breakdown`

- `platform_code`
- `date_from`
- `date_to`
- `sort_by`
- `sort_order`
- `limit`

### `GET /api/v1/reviews/score-buckets`

- `hotel_id`
- `platform_code`
- `date_from`
- `date_to`

### `GET /api/v1/reviews/daily-trend`

- `hotel_id`
- `platform_code`
- `date_from`
- `date_to`

## 4. Rule bắt buộc cho nguồn đọc dữ liệu

- không có `date_from/date_to` ở `summary`
  - đọc từ `review_dashboard_current_metrics`

- có `date_from/date_to` ở `summary`
  - sum từ `review_dashboard_daily_metrics`

- `country-breakdown`
  - đọc từ `review_dashboard_daily_country_metrics`

- `hotel-breakdown`
  - đọc từ `review_dashboard_daily_metrics`

- `score-buckets`
  - đọc từ `review_dashboard_daily_score_buckets`

- `daily-trend`
  - đọc từ `review_dashboard_daily_metrics`

## 5. Rule về date range

Phase 1 yêu cầu truyền đủ cặp `date_from + date_to`, thiếu 1 đầu mốc thì trả `400`.

Ngoại lệ:

- riêng `GET /api/v1/reviews/summary`
- nếu không truyền cả `date_from` và `date_to`
- thì đọc từ `review_dashboard_current_metrics`

Nếu có truyền date range:

- `date_from <= date_to`
- nếu sai thì trả `400`

Áp dụng cho:

- `country-breakdown`
- `hotel-breakdown`
- `score-buckets`
- `daily-trend`

Ngoại lệ duy nhất vẫn là:

- `summary`
- không truyền cả hai mốc ngày thì đọc current snapshot

## 6. Rule cho hotel-breakdown

- luôn group theo `hotel`

Nếu có `platform_code`:

- breakdown theo hotel trong platform đó

Nếu không có `platform_code`:

- gộp tất cả platform của cùng hotel

Phase 1:

- không trả từng dòng `hotel + platform`

## 7. Rule cho hotel-breakdown sorting

`sort_by` chỉ cho:

- `total_reviews`
- `bad_reviews`
- `avg_rating`
- `latest_reviewed_at`
- `hotel_name`

`sort_order` chỉ cho:

- `asc`
- `desc`

Param sai:

- trả `400`

## 8. Rule cho daily-trend

Sort mặc định:

- `metric_date asc`

Response item phase 1 nên có:

- `metric_date`
- `total_reviews`
- `bad_reviews`
- `avg_rating`

Nếu backend đã có sẵn thì có thể trả thêm:

- `positive_reviews`
- `neutral_reviews`
- `negative_reviews`
- `mixed_reviews`

## 9. Cache

Aggregate endpoints cache:

- `60-300s`

Có thể cache ở:

- backend memory
- Redis
- reverse proxy

## 10. Luồng cập nhật aggregate

Sau mỗi lần sync review:

1. upsert `reviews`
2. ghi `sync_jobs`
3. rebuild aggregate theo `hotel_id + platform_id`

Chỉ rebuild khoảng ngày bị ảnh hưởng, không rebuild full.

Các bảng cần update:

- `review_dashboard_current_metrics`
- `review_dashboard_daily_metrics`
- `review_dashboard_daily_country_metrics`
- `review_dashboard_daily_score_buckets`

## 11. Index cần kiểm tra

Trên `reviews`:

- `hotel_id`
- `platform_id`
- `reviewer_country_code`
- `is_bad_review`
- `reviewed_at`
- `rating`

Composite nên có:

- `(hotel_id, platform_id, reviewed_at desc)`
- `(hotel_id, is_bad_review, reviewed_at desc)`
- `(platform_id, reviewed_at desc)`

## 12. Ghi chú triển khai

- không dùng raw `reviews` để feed chart mỗi request
- frontend review list và dashboard phải dùng hai read path khác nhau
- summary cards, chart country, chart hotel, chart score, chart trend đều phải đọc từ aggregate path

## 13. Kết quả kỳ vọng

Sau khi backend hoàn thành:

- bảng review vẫn dùng `GET /api/v1/reviews`
- summary cards dùng `GET /api/v1/reviews/summary`
- chart country dùng `GET /api/v1/reviews/country-breakdown`
- chart hotel dùng `GET /api/v1/reviews/hotel-breakdown`
- chart score dùng `GET /api/v1/reviews/score-buckets`
- chart trend dùng `GET /api/v1/reviews/daily-trend`

Kết quả cuối:

- dữ liệu dashboard không lệch số với review list
- không còn tính chart từ page hiện tại
- hiệu năng dashboard ổn định hơn rõ rệt
