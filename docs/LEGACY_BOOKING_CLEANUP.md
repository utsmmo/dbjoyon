# Cleanup Review Legacy Booking

Tài liệu này dùng để dọn các review legacy có `external_review_id` dạng:

- `booking-visible-*`

Mục tiêu:

- xóa các record cũ bị trùng nội dung với review Booking thật
- không đụng vào luồng crawl hằng ngày
- chỉ cleanup thủ công hoặc one-time theo từng hotel

## Vì sao cần cleanup riêng

Hiện hệ thống chống trùng theo:

- `(hotel_id, platform_id, external_review_id)`

Nên nếu record cũ có `external_review_id = booking-visible-*`
và record mới có `external_review_id` chuẩn của Booking,
thì database vẫn coi đó là 2 record khác nhau dù nội dung giống nhau.

## Nguyên tắc an toàn

- không chạy delete trong job daily
- mặc định script chỉ `dry-run`
- chỉ xóa khi match chắc chắn 1-1 với review thật
- chỉ áp dụng cho `platform_code = booking`
- chỉ nhắm vào `external_review_id LIKE 'booking-visible-%'`

## Rule match hiện tại

Script sẽ tìm match theo:

- cùng `hotel_id`
- cùng `platform_code = booking`
- cùng `reviewer_name`
- cùng `review_title`
- cùng `review_text`
- cùng `rating`
- cùng `rating_scale`
- cùng ngày `reviewed_at`

Chỉ khi:

- 1 legacy record match đúng **1** canonical record

thì mới được xem là `safe match`.

## File script

- [ops/cleanup/cleanup_legacy_booking_reviews.py](D:/AutoCode/DB/Review/ops/cleanup/cleanup_legacy_booking_reviews.py)

## 1. Dry-run toàn bộ Booking

```powershell
python .\ops\cleanup\cleanup_legacy_booking_reviews.py
```

## 2. Dry-run cho một hotel

```powershell
python .\ops\cleanup\cleanup_legacy_booking_reviews.py --hotel-id 56864ae6-f920-4711-94e4-5a2cdc8fff42
```

## 3. Xuất report JSON

```powershell
python .\ops\cleanup\cleanup_legacy_booking_reviews.py `
  --hotel-id 56864ae6-f920-4711-94e4-5a2cdc8fff42 `
  --report-json .\reports\legacy-booking-cleanup.json
```

## 4. Xuất report CSV

```powershell
python .\ops\cleanup\cleanup_legacy_booking_reviews.py `
  --hotel-id 56864ae6-f920-4711-94e4-5a2cdc8fff42 `
  --report-csv .\reports\legacy-booking-cleanup.csv
```

## 5. Xóa thật

Chỉ chạy khi đã xem report và chắc chắn:

```powershell
python .\ops\cleanup\cleanup_legacy_booking_reviews.py `
  --hotel-id 56864ae6-f920-4711-94e4-5a2cdc8fff42 `
  --execute `
  --report-json .\reports\legacy-booking-cleanup-executed.json
```

## 6. Nên chạy theo thứ tự nào

Khuyến nghị:

1. chạy dry-run theo từng hotel
2. mở report
3. kiểm tra số lượng `safe_matches`
4. nếu hợp lý thì mới chạy `--execute`
5. sau khi xóa xong, gọi lại:
   - `GET /api/v1/reviews/stats?hotel_id=...&platform_code=booking`
6. so sánh lại tổng review với Booking thật

## 7. Điều gì script sẽ xóa

Script chỉ xóa:

- review legacy `booking-visible-*`

Script sẽ không xóa:

- review Booking canonical
- review Agoda/Google/Tripadvisor
- review không match chắc chắn

## 8. Lưu ý rất quan trọng

- hành động xóa là rủi ro
- nên backup DB trước khi chạy cleanup
- nên chạy theo từng hotel, không nên xóa toàn hệ thống trong một lần

Trước khi cleanup, nên chạy backup:

- [docs/DB_BACKUP_GOOGLE_DRIVE.md](D:/AutoCode/DB/Review/docs/DB_BACKUP_GOOGLE_DRIVE.md)

## 9. Quy trình an toàn đề nghị

```text
1. Backup DB
2. Dry-run detect duplicate legacy
3. Xem report JSON/CSV
4. Execute delete cho đúng hotel cần dọn
5. Kiểm tra lại tổng review stats
6. Tiếp tục crawl/sync bình thường
```
