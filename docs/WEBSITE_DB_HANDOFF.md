# Hướng Dẫn Bàn Giao DB Cho Team Website

Tài liệu này chốt rõ:

- phần nào hệ thống DB hiện tại đã có
- phần nào vừa được thiết kế bổ sung để không phải vá schema giữa chừng
- team website nên đọc dữ liệu qua API nào để hiển thị nhanh

## 1. Những phần đã có sẵn trong hệ thống hiện tại

### Đã có bảng lõi

- `hotels`
- `platforms`
- `hotel_platform_accounts`
- `hotel_platform_review_metrics`
- `reviews`
- `review_replies`
- `review_tags`
- `ai_analysis_results`
- `incidents`
- `sync_jobs`
- `audit_logs`
- `notification_deliveries`
- `room_types`
- `rate_plans`
- `departments`

### Đã có logic review quan trọng

- `external_review_id`
- `raw_payload JSONB`
- unique chống trùng:
  - `unique(hotel_id, platform_id, external_review_id)`
- upsert review an toàn
- `review_url`
- `reviewer_country_code`
- `rating`
- `rating_scale`
- `review_title`
- `review_text`
- `review_language`
- `reviewed_at`
- `source_created_at`
- `source_updated_at`
- `is_bad_review`

### Đã có dữ liệu dịch để web hiển thị

Bản dịch đang lưu trong `reviews.normalized_payload`:

- `translated_title_vi`
- `translated_text_vi`

API hiện tại đã expose sẵn ra response nên web không cần tự parse JSONB nếu chỉ gọi API.

### Đã có dữ liệu metric tổng theo từng hotel/platform

Bảng:

- `hotel_platform_review_metrics`

Mục đích:

- lưu tổng số review mới nhất
- điểm trung bình mới nhất
- thang điểm mới nhất
- link review source mới nhất

## 2. Những phần vừa bổ sung thiết kế cho website/admin

Đã thêm migration:

- [007_web_admin_foundation.sql](D:/AutoCode/DB/Review/db/migrations/007_web_admin_foundation.sql)

Migration này bổ sung:

### Quản trị người dùng

- `users`
- `roles`
- `user_roles`
- `permissions`
- `role_permissions`
- `user_hotel_scopes`

### Dữ liệu danh mục

- `countries`

### Mở rộng hotel cho web/dashboard

Thêm vào `hotels`:

- `address`
- `star_rating`
- `brand_name`
- `latitude`
- `longitude`
- `is_featured`

### Mở rộng review cho AI/dashboard

Thêm vào `reviews`:

- `sentiment_score`
- `ai_summary`
- `ai_keywords`
- `ai_topics`
- `analysis_version`
- `analysis_status`
- `analyzed_at`

### Mở rộng phân tích/tag

- `review_analysis_runs`
- `review_tag_map`

### Tương thích với tên bảng mà team web mong muốn

Đã tạo `VIEW`:

- `review_sources`

View này map từ bảng thật:

- `platforms`

Để team website có thể hiểu theo naming:

- `source_code`
- `source_name`

nhưng backend hiện tại vẫn an toàn vì code lõi tiếp tục dùng `platforms`.

## 3. Những mục website yêu cầu nhưng hệ thống hiện tại xử lý theo cách khác

### `review_sources`

Team web yêu cầu bảng `review_sources`.

Hệ thống lõi đang dùng:

- `platforms`

Giải pháp:

- giữ `platforms` làm source of truth
- tạo `view review_sources` để tương thích

### `translated_pros_vi`, `translated_cons_vi`, `pros`, `cons`

Hiện chưa tách thành cột riêng trong bảng `reviews`.

Lý do:

- các OTA không đồng nhất field
- có nguồn có `pros/cons`, có nguồn không có

Giải pháp hiện tại:

- lưu trong `normalized_payload`

Ví dụ:

- `normalized_payload.pros`
- `normalized_payload.cons`
- `normalized_payload.translated_pros_vi`
- `normalized_payload.translated_cons_vi`

Nếu sau này team web query phần này quá nhiều thì mới nên tách cột riêng.

## 4. Những index đã có và đủ cho web filter cơ bản

Đã có:

- `reviews(hotel_id)`
- `reviews(platform_id)`
- `reviews(reviewed_at desc)`
- `reviews(hotel_id, platform_id, reviewed_at desc)`
- `reviews(hotel_id, is_bad_review, reviewed_at desc)`
- `reviews(platform_id, external_review_id)`
- `reviews.raw_payload GIN`
- `reviews.normalized_payload GIN`
- `hotels(hotel_code)`
- `hotels(country_code)` qua migration mới
- `users(email)` qua migration mới
- `reviews(rating)` qua migration mới
- `reviews(reviewer_country_code)` qua migration mới
- `reviews(analysis_status, analyzed_at desc)` qua migration mới

## 5. Tài khoản seed sẵn cho phần admin

Migration mới seed sẵn:

- `admin@datac.click`
- `manager@datac.click`
- `member@datac.click`
- `ops.manager@datac.click`
- `review.member@datac.click`

Lưu ý:

- migration hiện tạo hash thật bằng `pgcrypto/crypt(...)`
- đây là tài khoản mẫu cho môi trường nội bộ/test
- khi đưa production nên đổi password ngay

Mật khẩu mẫu hiện tại:

- `admin@datac.click` / `Admin@123`
- `manager@datac.click` / `Manager@123`
- `member@datac.click` / `Member@123`
- `ops.manager@datac.click` / `OpsManager@123`
- `review.member@datac.click` / `ReviewMember@123`

## 6. Các quyết định kiến trúc đã chốt cho team web

### Rating

- hệ thống lưu cả `rating` và `rating_scale`
- không ép cứng chỉ 5 hay 10
- frontend phải hiển thị theo cặp giá trị này

Ví dụ:

- `8 / 10`
- `4.5 / 5`

### Country

- `hotels.country_code`: quốc gia của khách sạn
- `reviews.reviewer_country_code`: quốc gia của người review

Hai loại này khác nhau, frontend không được dùng lẫn.

### Bản gốc và bản dịch

Hệ thống giữ cả:

- bản gốc: `review_title`, `review_text`
- bản dịch: `translated_title_vi`, `translated_text_vi` qua API hoặc trong `normalized_payload`

### Soft delete

- hiện tại chưa dùng soft delete
- web nên xem dữ liệu hiện có là dữ liệu active thực tế

### Auth

- giai đoạn hiện tại là local password model
- chưa làm SSO
- schema đã mở đường để sau này nâng cấp

## 7. Kết luận ngắn cho team website

Team website có thể bắt đầu code ngay với giả định:

1. review đọc qua API hiện tại là đủ để hiển thị
2. hotels đọc qua API hiện tại là đủ để build listing/filter
3. DB đã có unique chống trùng review
4. phần auth/admin scope đã có thiết kế migration để không phải đập schema lại
5. phần AI đã có chỗ chứa trực tiếp trong `reviews` và bảng run riêng

Tài liệu query cụ thể cho web:

- [WEBSITE_QUERY_GUIDE.md](D:/AutoCode/DB/Review/docs/WEBSITE_QUERY_GUIDE.md)
