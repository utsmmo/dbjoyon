# Crawler Doc Start Here

Tai lieu nay danh cho doi crawl / ingestion.
Muc tieu la de doi crawl doc dung 3 file, lay dung link, map dung `hotel_id`, va post review dung endpoint ma khong tao trung hotel.

## Thu tu doc bat buoc

1. `docs/Crawl/CRAWLER_DOC_START_HERE.md`
2. `docs/Crawl/CRAWLER_OTA_ENDPOINT_MATRIX.md`
3. `docs/Crawl/POST_REVIEW_GUIDE.md`
4. `docs/Crawl/ADMIN_CRAWLER_HOTEL_LINK_PLAN.md`

## Nguon su that

- Danh sach hotel chuan: `GET /api/v1/hotels`
- Link OTA chuan: `items[].metadata.source_links`
- Ten business chuan: `items[].hotel_name`
- Endpoint post review chuan: `POST /api/v1/sync/reviews/{platform_code}`

Crawler khong tu tao ten hotel moi theo ten OTA.
Crawler khong tu sua link hotel trong database.
Crawler chi doc link va post review.

## Rule rat quan trong

### 1 hotel co nhieu link cung 1 OTA

Van chi la `1 hotel_id`.

Vi du:

- `Villa` co 3 link Booking
- crawler crawl ca 3 link neu can
- nhung khi post review, tat ca review van dung cung `hotel_id` cua `Villa`
- khong duoc tao 3 hotel moi

### Agoda link phai clean

Vi du sai:

- `https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html?adults=2&rooms=1&checkIn=2026-08-24&los=2`

Vi du dung:

- `https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html`

### Ten hotel noi bo moi la nguon dung

Ten OTA co the khac.
Chi can link dung, `hotel_id` dung, va review post ve dung hotel.

## Crawler duoc phep goi endpoint nao

- `GET /api/v1/hotels`
- `GET /api/v1/reviews/stats`
- `GET /api/v1/reviews`
- `POST /api/v1/sync/reviews/{platform_code}`
- `GET /api/v1/reviews/bad/unnotified`
- `POST /api/v1/notifications/deliveries`

## Crawler khong duoc dung endpoint nao

- `POST /api/v1/system/hotels/purge`
- `POST /api/v1/system/hotels/reset-import`
- `POST /api/v1/system/hotels/reset-import/default-manifest`
- `POST /api/v1/hotels`
- bat ky endpoint admin nao de tao, sua, xoa hotel

Neu link sai, hotel sai, trung hotel, hay can sua OTA list:

- crawler report lai cho Admin / DB / BE
- khong tu sua database

## Checklist truoc khi chay crawler

1. Da goi `GET /api/v1/hotels?limit=200&offset=0`
2. Da lay dung `hotel_id`
3. Da doc dung `metadata.source_links.<platform>`
4. Da clean link Agoda neu can
5. Da xac dinh ro: 1 hotel co nhieu link cung OTA van la 1 `hotel_id`
6. Da chuan bi `external_review_id` cho moi review
7. Da biet se post vao `platform_code` nao
8. Neu co, da gui `source_link_used` dung voi link dang crawl

## Neu chi doc 1 file

Neu doi crawl chi co it thoi gian, doc file nay truoc, sau do doc ngay:

- `docs/Crawl/CRAWLER_OTA_ENDPOINT_MATRIX.md`
- `docs/Crawl/POST_REVIEW_GUIDE.md`
