# Analytics Backfill Runbook

Tài liệu này dùng khi:

- analytics routes đã deploy
- migration analytics đã chạy
- nhưng các endpoint analytics còn rỗng hoặc `summary` lỗi do aggregate chưa có dữ liệu

## 1. File backfill cần chạy

- [009_backfill_review_dashboard_analytics.sql](D:/AutoCode/DB/Review/db/migrations/009_backfill_review_dashboard_analytics.sql)

File này sẽ:

- xóa dữ liệu cũ trong 4 bảng aggregate
- build lại từ `reviews`
- kéo thêm current source metrics từ `hotel_platform_review_metrics`

Các bảng được backfill:

- `review_dashboard_current_metrics`
- `review_dashboard_daily_metrics`
- `review_dashboard_daily_country_metrics`
- `review_dashboard_daily_score_buckets`

## 2. Thứ tự đầy đủ nếu server còn thiếu migration

Chạy lần lượt:

1. `006_hotel_platform_review_metrics.sql`
2. `007_web_admin_foundation.sql`
3. `008_review_dashboard_analytics.sql`
4. `009_backfill_review_dashboard_analytics.sql`

## 3. Lệnh chạy trong Docker

Nếu đang đứng trong thư mục:

```text
C:\Users\Admin\Desktop\DBv2\db\migrations
```

thì chạy:

```bash
docker exec -i hotel-review-postgres psql -U hotel_admin -d hotel_review_db < 006_hotel_platform_review_metrics.sql
docker exec -i hotel-review-postgres psql -U hotel_admin -d hotel_review_db < 007_web_admin_foundation.sql
docker exec -i hotel-review-postgres psql -U hotel_admin -d hotel_review_db < 008_review_dashboard_analytics.sql
docker exec -i hotel-review-postgres psql -U hotel_admin -d hotel_review_db < 009_backfill_review_dashboard_analytics.sql
```

## 4. Kiểm tra nhanh sau khi chạy

Vào psql:

```bash
docker exec -it hotel-review-postgres psql -U hotel_admin -d hotel_review_db
```

Chạy:

```sql
SELECT 'review_dashboard_current_metrics' AS table_name, COUNT(*) AS rows_count
FROM review_dashboard_current_metrics
UNION ALL
SELECT 'review_dashboard_daily_metrics', COUNT(*) FROM review_dashboard_daily_metrics
UNION ALL
SELECT 'review_dashboard_daily_country_metrics', COUNT(*) FROM review_dashboard_daily_country_metrics
UNION ALL
SELECT 'review_dashboard_daily_score_buckets', COUNT(*) FROM review_dashboard_daily_score_buckets;
```

Nếu cả 4 bảng đều có số dòng > 0 thì backfill đã có dữ liệu.

## 5. Test lại API

Sau khi backfill xong, test lại:

- `GET /api/v1/reviews/summary`
- `GET /api/v1/reviews/country-breakdown?date_from=2026-07-01T00:00:00+07:00&date_to=2026-07-25T23:59:59+07:00&limit=20`
- `GET /api/v1/reviews/hotel-breakdown?date_from=2026-07-01T00:00:00+07:00&date_to=2026-07-25T23:59:59+07:00&limit=20`
- `GET /api/v1/reviews/score-buckets?date_from=2026-07-01T00:00:00+07:00&date_to=2026-07-25T23:59:59+07:00`
- `GET /api/v1/reviews/daily-trend?date_from=2026-07-01T00:00:00+07:00&date_to=2026-07-25T23:59:59+07:00`

## 6. Lưu ý

- file `009` là backfill toàn bộ, phù hợp để chạy ban đầu
- về sau nên có job incremental rebuild theo `hotel_id + platform_id`
- nếu `summary` vẫn `500` sau khi đã có dữ liệu aggregate, cần xem tiếp log backend/runtime error
