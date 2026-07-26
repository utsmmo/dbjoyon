# Đề Xuất Kiến Trúc Analytics Cho Web Hotel Review

Tài liệu này bám sát schema hiện tại của project `Review` và chốt hướng tối ưu cho dashboard.

Mục tiêu:

- dashboard không phải quét `reviews` cho mọi widget
- read path cho analytics tách riêng khỏi read path review detail
- API dashboard đủ nhanh khi số review tăng mạnh
- dễ mở rộng sang score distribution, country breakdown, hotel breakdown, AI analytics

## 1. Đánh giá hiện trạng

Hiện project đã có:

- `reviews`: bảng raw + normalized review
- `hotel_platform_review_metrics`: snapshot current lấy từ source OTA
- `ai_analysis_results`: kết quả AI riêng
- `GET /api/v1/reviews`
- `GET /api/v1/reviews/stats`
- `GET /api/v1/review-metrics/current`

Điểm nghẽn hiện tại:

- `/reviews/stats` vẫn đang `GROUP BY` trực tiếp từ `reviews`
- breakdown theo country / score bucket / hotel nếu làm từ raw table sẽ chậm dần
- frontend dashboard đang phải dựa nhiều vào raw review query

Kết luận:

- `reviews` nên giữ làm source of truth cho detail/list/search
- dashboard nên chuyển sang aggregate path riêng

## 2. Hướng kiến trúc đề xuất

### Read path tách thành 2 nhánh

#### Nhánh 1: review detail path

Dùng cho:

- bảng review chi tiết
- search review
- popup/detail review
- audit/debug

Đọc từ:

- `reviews`

#### Nhánh 2: analytics/dashboard path

Dùng cho:

- summary cards
- country breakdown
- hotel breakdown
- score buckets
- trend chart theo ngày

Đọc từ:

- `review_dashboard_current_metrics`
- `review_dashboard_daily_metrics`
- `review_dashboard_daily_country_metrics`
- `review_dashboard_daily_score_buckets`

## 3. Schema aggregate đề xuất

Đã tạo migration mẫu:

- [008_review_dashboard_analytics.sql](D:/AutoCode/DB/Review/db/migrations/008_review_dashboard_analytics.sql)

### 3.1 `review_dashboard_current_metrics`

Mục đích:

- snapshot current theo `hotel + platform`
- load cực nhanh cho summary cards

Các field chính:

- `hotel_id`
- `platform_id`
- `total_reviews`
- `bad_reviews`
- `positive_reviews`
- `neutral_reviews`
- `negative_reviews`
- `mixed_reviews`
- `avg_rating`
- `min_rating`
- `max_rating`
- `latest_reviewed_at`
- `latest_source_updated_at`
- `source_total_reviews`
- `source_average_rating`
- `source_rating_scale`
- `last_aggregated_at`

### 3.2 `review_dashboard_daily_metrics`

Mục đích:

- trend theo ngày
- hotel breakdown
- platform breakdown
- summary theo date range

Grain:

- `metric_date + hotel_id + platform_id`

### 3.3 `review_dashboard_daily_country_metrics`

Mục đích:

- country breakdown

Grain:

- `metric_date + hotel_id + platform_id + reviewer_country_code`

### 3.4 `review_dashboard_daily_score_buckets`

Mục đích:

- score distribution

Grain:

- `metric_date + hotel_id + platform_id + bucket_code`

Bucket đề xuất phase 1:

- `0_2`
- `2_4`
- `4_6`
- `6_8`
- `8_9`
- `9_10`

Nếu sau này có platform thang `5`, backend normalize về thang `10` trước khi aggregate.

## 4. Tại sao chọn aggregate table thay vì chỉ materialized view

### Aggregate table phù hợp hơn vì:

- filter date range/hotel/platform/country chạy ổn định hơn
- dễ upsert incremental sau mỗi sync job
- không cần refresh full toàn bộ như materialized view
- dễ cache theo key logic
- dễ mở rộng thêm metric mới

### Materialized view chỉ nên dùng khi:

- cần quick win cho một số snapshot global
- dữ liệu chưa quá lớn
- chấp nhận refresh theo batch

Kết luận practical:

- dùng **aggregate tables** là chính
- nếu muốn, có thể thêm một materialized view global ở phase sau, nhưng không phải nền tảng chính

## 5. Read path đề xuất

### `/api/v1/reviews`

Đọc từ:

- `reviews`

Use case:

- detail list
- search
- pagination
- filter nhiều chiều

### `/api/v1/reviews/summary`

Đọc từ:

- `review_dashboard_current_metrics`
- hoặc sum từ `review_dashboard_daily_metrics` nếu có date range

Không nên đọc từ:

- `reviews`

### `/api/v1/reviews/country-breakdown`

Đọc từ:

- `review_dashboard_daily_country_metrics`

### `/api/v1/reviews/hotel-breakdown`

Đọc từ:

- `review_dashboard_daily_metrics`

### `/api/v1/reviews/score-buckets`

Đọc từ:

- `review_dashboard_daily_score_buckets`

## 6. Index đề xuất theo filter thực tế

### 6.1 Trên `reviews` cho detail/search path

Đã có và nên giữ:

- `(hotel_id)`
- `(platform_id)`
- `(reviewed_at desc)`
- `(hotel_id, platform_id, reviewed_at desc)`
- `(hotel_id, is_bad_review, reviewed_at desc)`
- `(platform_id, external_review_id)`
- `GIN(raw_payload)`
- `GIN(normalized_payload)`

Nên có thêm hoặc đã bổ sung:

- `(reviewer_country_code)`
- `(rating)`
- `(analysis_status, analyzed_at desc)`

Nếu dashboard/search dùng `q` nhiều:

- phase 1: giữ `ILIKE`
- phase 2: thêm `tsvector` hoặc trigram index

Đề xuất phase 2 cho search:

```sql
CREATE EXTENSION IF NOT EXISTS pg_trgm;

CREATE INDEX IF NOT EXISTS idx_reviews_search_trgm
ON reviews
USING GIN (
    (
        COALESCE(review_title, '') || ' ' ||
        COALESCE(review_text, '') || ' ' ||
        COALESCE(normalized_payload ->> 'translated_title_vi', '') || ' ' ||
        COALESCE(normalized_payload ->> 'translated_text_vi', '') || ' ' ||
        COALESCE(reviewer_name, '')
    ) gin_trgm_ops
);
```

### 6.2 Trên aggregate tables

`review_dashboard_current_metrics`

- PK `(hotel_id, platform_id)`
- index `(hotel_id)`
- index `(platform_id)`
- index `(last_aggregated_at desc)`

`review_dashboard_daily_metrics`

- PK `(metric_date, hotel_id, platform_id)`
- index `(hotel_id, metric_date desc)`
- index `(platform_id, metric_date desc)`
- index `(metric_date desc)`

`review_dashboard_daily_country_metrics`

- PK `(metric_date, hotel_id, platform_id, reviewer_country_code)`
- index `(hotel_id, platform_id, metric_date desc)`
- index `(reviewer_country_code, metric_date desc)`

`review_dashboard_daily_score_buckets`

- PK `(metric_date, hotel_id, platform_id, bucket_code)`
- index `(hotel_id, platform_id, metric_date desc)`

## 7. API aggregate đề xuất

### 7.1 `GET /api/v1/reviews/summary`

Mục tiêu:

- summary cards

Query params:

- `hotel_id`
- `platform_code`
- `date_from`
- `date_to`

Response đề xuất:

```json
{
  "hotel_id": "uuid-or-null",
  "platform_code": "booking",
  "date_from": "2026-07-01",
  "date_to": "2026-07-25",
  "total_reviews": 655,
  "bad_reviews": 121,
  "bad_review_ratio": 0.1847,
  "avg_rating": 8.61,
  "positive_reviews": 401,
  "neutral_reviews": 88,
  "negative_reviews": 102,
  "mixed_reviews": 64,
  "latest_reviewed_at": "2026-07-25T21:30:00+07:00",
  "source_total_reviews": 662,
  "source_average_rating": 8.70,
  "source_rating_scale": 10.0,
  "last_aggregated_at": "2026-07-25T21:35:00+07:00"
}
```

### 7.2 `GET /api/v1/reviews/country-breakdown`

Mục tiêu:

- top reviewer countries

Query params:

- `hotel_id`
- `platform_code`
- `date_from`
- `date_to`
- `limit`

Response đề xuất:

```json
{
  "items": [
    {
      "reviewer_country_code": "US",
      "total_reviews": 120,
      "bad_reviews": 22,
      "avg_rating": 8.4
    }
  ],
  "total": 10
}
```

### 7.3 `GET /api/v1/reviews/hotel-breakdown`

Mục tiêu:

- ranking khách sạn theo review volume / bad review / avg rating

Query params:

- `platform_code`
- `date_from`
- `date_to`
- `sort_by`
- `sort_order`
- `limit`

`sort_by` phase 1:

- `total_reviews`
- `bad_reviews`
- `avg_rating`
- `latest_reviewed_at`

Response đề xuất:

```json
{
  "items": [
    {
      "hotel_id": "uuid",
      "hotel_name": "Ania Airport Residences - Next to Holiday Inn",
      "platform_code": "booking",
      "total_reviews": 52,
      "bad_reviews": 13,
      "avg_rating": 8.2,
      "latest_reviewed_at": "2026-07-25T19:00:00+07:00"
    }
  ],
  "total": 10
}
```

### 7.4 `GET /api/v1/reviews/score-buckets`

Mục tiêu:

- chart phân bố điểm

Query params:

- `hotel_id`
- `platform_code`
- `date_from`
- `date_to`

Response đề xuất:

```json
{
  "items": [
    {
      "bucket_code": "8_9",
      "bucket_label": "8.0 - 8.99",
      "rating_from": 8.0,
      "rating_to": 8.99,
      "review_count": 140,
      "bad_review_count": 140
    }
  ],
  "total": 6
}
```

## 8. Cách update aggregate

### Hướng thực dụng phase 1

Khi sync review thành công:

1. upsert vào `reviews`
2. ghi `sync_jobs`
3. enqueue job rebuild aggregate cho `hotel_id + platform_id`

Worker aggregate:

1. rebuild current snapshot cho `hotel_id + platform_id`
2. rebuild daily rows trong khoảng affected date
3. update `last_aggregated_at`

### Affected date range đề xuất

Lấy min/max từ batch:

- `min(reviewed_at::date)`
- `max(reviewed_at::date)`

Chỉ rebuild khoảng ngày bị ảnh hưởng, không rebuild full toàn hệ thống.

## 9. Chiến lược cache backend

### Phase 1

Cache ở backend/API layer:

- TTL `30s - 120s` cho dashboard aggregate endpoint
- cache key theo:
  - endpoint
  - `hotel_id`
  - `platform_code`
  - `date_from`
  - `date_to`
  - `limit`
  - `sort_by`
  - `sort_order`

### Phase 2

Thêm invalidation theo sync:

- khi aggregate worker cập nhật `hotel_id + platform_id`
- clear cache key liên quan hotel/platform đó

### Khuyến nghị practical

- nếu đang self-host đơn giản: dùng in-memory cache hoặc Redis nhỏ
- nếu nhiều app instance: ưu tiên Redis

## 10. Lộ trình triển khai đề xuất

### Phase A

- tạo aggregate tables
- tạo repository/service mới cho analytics
- build:
  - `/reviews/summary`
  - `/reviews/country-breakdown`
  - `/reviews/hotel-breakdown`
  - `/reviews/score-buckets`

### Phase B

- thêm aggregate refresh job sau sync
- thêm cache TTL

### Phase C

- tối ưu search với trigram/fts
- thêm AI/topic breakdown

## 11. Kết luận ngắn

Tôi thấy hướng đúng cho project hiện tại là:

1. giữ `reviews` làm source of truth cho review detail
2. không dùng `reviews` trực tiếp cho dashboard widgets nặng
3. dùng aggregate tables riêng cho analytics
4. summary card đọc từ `review_dashboard_current_metrics`
5. breakdown/trend đọc từ các bảng daily aggregate
6. cache ở backend để frontend luôn thấy nhanh và ổn định

Đây là hướng sạch, practical, và bám sát trạng thái hiện tại của project `Review`.
