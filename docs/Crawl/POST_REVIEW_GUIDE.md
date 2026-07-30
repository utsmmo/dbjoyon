# Crawler Posting Guide

Tai lieu nay la huong dan chuan de doi crawl post review vao he thong dung cach.
Muc tieu:

- khong tao trung hotel
- khong post sai `hotel_id`
- khong lay nham ten OTA lam ten business
- khong tao nhieu hotel chi vi 1 hotel co nhieu link cung 1 OTA

Base URL hien tai:

- `https://data.datac.click`

Swagger:

- `https://data.datac.click/docs`

## 1. Nguyen tac bat buoc

### Nguon dung cua hotel

Crawler phai lay hotel tu:

- `GET /api/v1/hotels?limit=200&offset=0`

Khong duoc:

- tu tao hotel moi vi thay ten hotel tren OTA khac
- tu sua ten hotel
- tu sua link OTA trong database

### 1 hotel co nhieu link cung 1 OTA

Van chi la `1 hotel_id`.

Vi du:

- `Danang Beach` co 2 link Booking
- crawler duoc crawl 2 link do
- nhung tat ca review Booking cua `Danang Beach` van phai post vao cung `hotel_id` cua `Danang Beach`

Dung:

- `1 hotel business` = `1 hotel_id`
- `nhieu link OTA` = `nhieu source de crawl`, khong phai `nhieu hotel`

Sai:

- thay 2 link Booking roi tao 2 hotel trong DB
- thay ten hien thi tren Booking khac ten noi bo roi tao them hotel moi

### Agoda link phai la canonical link

Vi du sai:

- `https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html?adults=2&rooms=1&checkIn=2026-08-24&los=2`

Vi du dung:

- `https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html`

Rule:

- bo query params tracking / date / adults / rooms / los
- chi giu `scheme + host + path`

## 2. Endpoint doi crawl duoc phep dung

Crawler chi duoc dung cac endpoint sau:

- `GET /api/v1/hotels?limit=200&offset=0`
- `GET /api/v1/hotels?q=<keyword>&limit=200&offset=0`
- `GET /api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=<platform_code>`
- `GET /api/v1/reviews?hotel_id=<hotel_id>&platform_code=<platform_code>&limit=20&offset=0`
- `POST /api/v1/sync/reviews/{platform_code}`
- `DELETE /api/v1/reviews?hotel_id=<hotel_id>&platform_code=<platform_code>`
- `DELETE /api/v1/reviews?hotel_id=<hotel_id>&platform_code=<platform_code>&source_link=<canonical_link>`
- `GET /api/v1/reviews/bad/unnotified`
- `POST /api/v1/notifications/deliveries`

Crawler khong duoc goi:

- `POST /api/v1/hotels`
- `POST /api/v1/system/hotels/purge`
- `POST /api/v1/system/hotels/reset-import`
- `POST /api/v1/system/hotels/reset-import/default-manifest`
- bat ky endpoint admin CRUD hotel nao

## 3. Cach lay dung danh sach hotel va links

### Lay tat ca hotel

```bash
curl "https://data.datac.click/api/v1/hotels?limit=200&offset=0"
```

Crawler phai doc cac field sau:

- `items[].id`
- `items[].hotel_code`
- `items[].hotel_name`
- `items[].metadata.source_links`
- `items[].metadata.canonical_links`

Y nghia:

- `id` chinh la `hotel_id`
- `hotel_name` la ten business noi bo
- `metadata.source_links.booking` la danh sach link Booking neu co
- `metadata.source_links.agoda` la danh sach link Agoda neu co
- `metadata.source_links.google` la danh sach link Google neu co

### Mau response can hieu

```json
{
  "items": [
    {
      "id": "hotel-uuid-1",
      "hotel_code": "villa",
      "hotel_name": "Villa",
      "metadata": {
        "source_links": {
          "booking": [
            "https://www.booking.com/Share/AAA",
            "https://www.booking.com/Share/BBB"
          ],
          "agoda": [
            "https://www.agoda.com/vi-vn/example/hotel/da-nang-vn.html"
          ],
          "google": [
            "https://maps.google.com/example"
          ]
        }
      }
    }
  ]
}
```

Cach hieu dung:

- `Villa` chi co `1 id = hotel-uuid-1`
- du Booking co 2 link, van la cung 1 hotel
- review tu ca 2 link Booking deu phai post ve `hotel_id = hotel-uuid-1`

## 4. Flow chuan cho doi crawl

1. Goi `GET /api/v1/hotels?limit=200&offset=0`
2. Tach danh sach link theo tung OTA
3. Voi moi hotel:
   - giu nguyen `hotel_id`
   - giu nguyen `hotel_name`
   - lay danh sach link cua OTA can crawl
4. Crawl review tu tung link
5. Normalize review
6. Check stats hien tai trong DB neu can
7. Goi `POST /api/v1/sync/reviews/{platform_code}`
8. Verify lai bang `GET /api/v1/reviews/stats`

## 5. Platform code hop le de post review

Hien tai ho tro:

- `booking`
- `agoda`
- `ctrip`
- `expedia`
- `tripadvisor`
- `google`

Vi du:

- `POST https://data.datac.click/api/v1/sync/reviews/booking`
- `POST https://data.datac.click/api/v1/sync/reviews/agoda`
- `POST https://data.datac.click/api/v1/sync/reviews/ctrip`
- `POST https://data.datac.click/api/v1/sync/reviews/expedia`
- `POST https://data.datac.click/api/v1/sync/reviews/google`

## 6. Payload post review chuan

### Field bat buoc

- `hotel_id`
- `reviews[]`
- `reviews[].external_review_id`
- `reviews[].reviewed_at`
- `reviews[].reviewer_country_code`
- `reviews[].raw_payload`

### Field nen co

- `source_link_used`
- `reviews[].review_url`
- `reviews[].rating`
- `reviews[].rating_scale`
- `reviews[].review_title`
- `reviews[].review_text`
- `reviews[].review_language`
- `reviews[].reviewer_name`
- `reviews[].reviewer_country_code`
- `reviews[].source_created_at`
- `reviews[].source_updated_at`

### Rule validation moi

Tu ngay `July 29, 2026`, backend se tu choi payload neu thieu:

- `reviews[].reviewer_country_code`

Va field nay phai dung format:

- ma quoc gia `2 ky tu`
- vi du: `US`, `VN`, `KR`, `AU`

Neu crawler chua resolve duoc quoc gia reviewer, khong duoc post review do vao backend.

### Khuyen nghi production

De tranh `500`, `502`, `ReadTimeout` va giam rui ro sync fail, crawler nen mac dinh dung payload toi gian:

- `hotel_id`
- `source_link_used`
- `triggered_by`
- `reviews[].external_review_id`
- `reviews[].reviewed_at`
- `reviews[].reviewer_country_code`
- `reviews[].raw_payload`

Chi gui them cac field mo rong nhu `hotel_platform_account_id`, `source_total_reviews`, `source_categories`, `review_text`, `rating`, `reviewer_*` khi da xac nhan backend lane do on dinh cho batch hien tai.

`hotel_platform_account_id` la field de fail nhat neu mapping sai. Neu crawler khong lay duoc UUID chinh xac tu he thong, hay bo trong field nay.

Neu crawler gui dung `source_link_used`, backend se tu resolve `hotel_platform_account_id` theo link da dang ky cua hotel. Chi gui ca hai field khi chac chan chung cung tro toi mot account.

### Payload mau

```json
{
  "hotel_id": "hotel-uuid-1",
  "hotel_platform_account_id": null,
  "source_link_used": "https://www.booking.com/Share/AAA",
  "triggered_by": "crawler_booking_v1",
  "reviews": [
    {
      "external_review_id": "booking-review-001",
      "reviewed_at": "2026-07-29T09:00:00+07:00",
      "source_created_at": "2026-07-29T09:00:00+07:00",
      "source_updated_at": "2026-07-29T09:05:00+07:00",
      "review_url": "https://www.booking.com/review/booking-review-001",
      "reviewer_name": "Alice",
      "reviewer_country_code": "US",
      "rating": 8,
      "rating_scale": 10,
      "review_title": "Good stay",
      "review_text": "Nice room and clean area.",
      "review_language": "en",
      "is_bad_review": false,
      "metadata": {
        "sync_source": "crawler_booking_v1",
        "source_link_used": "https://www.booking.com/Share/AAA",
        "crawl_batch_id": "batch-20260729-0900"
      },
      "normalized_payload": {
        "platform_code": "booking"
      },
      "raw_payload": {
        "provider": "booking",
        "id": "booking-review-001",
        "title": "Good stay",
        "text": "Nice room and clean area."
      }
    }
  ]
}
```

### Payload toi gian de sync an toan

```json
{
  "hotel_id": "6681d663-38ae-4896-a24b-4bcb7b091346",
  "source_link_used": "https://www.booking.com/Share-97t5jDA",
  "triggered_by": "crawler_booking_v1",
  "reviews": [
    {
      "external_review_id": "booking-review-001",
      "reviewed_at": "2026-07-29T09:00:00+07:00",
      "reviewer_country_code": "VN",
      "raw_payload": {
        "provider": "booking",
        "id": "booking-review-001"
      }
    }
  ]
}
```

## 7. Cach map field tu crawler vao API

| Nguon crawl | Field API |
|---|---|
| id review ben OTA | `external_review_id` |
| ngay review | `reviewed_at` |
| ngay tao ben OTA | `source_created_at` |
| ngay OTA cap nhat lan cuoi | `source_updated_at` |
| ten nguoi review | `reviewer_name` |
| quoc gia reviewer | `reviewer_country_code` |
| diem review | `rating` |
| thang diem | `rating_scale` |
| tieu de | `review_title` |
| noi dung | `review_text` |
| link review | `review_url` |
| metadata crawl | `metadata` |
| du lieu da normalize | `normalized_payload` |
| du lieu goc day du | `raw_payload` |

## 8. Cach xu ly khi 1 hotel co nhieu link cung 1 OTA

Day la rule quan trong nhat.

Vi du:

- `The Grace` co 3 link Booking
- `The Grace` co 1 link Agoda

Crawler lam nhu sau:

1. Lay `hotel_id` cua `The Grace`
2. Crawl tung link Booking
3. Gom review theo `external_review_id`
4. Post tat ca review Booking vao:
   - `POST /api/v1/sync/reviews/booking`
   - voi cung `hotel_id` cua `The Grace`
5. Khong tao them hotel
6. Khong tao them `hotel_id` moi

Neu 2 link cung tra ve cung 1 review:

- unique key DB se chong duplicate theo:
  - `hotel_id`
  - `platform_id`
  - `external_review_id`

Nhung crawler van nen tu dedupe truoc khi post de nhe payload.

Ngoai ra:

- nen gui `source_link_used`
- backend se doi chieu link nay voi `metadata.source_links.<platform_code>`
- neu link khong nam trong danh sach da khai bao cua hotel, backend se tu choi sync

## 9. Verify sau khi post

### Check thong ke

```bash
curl "https://data.datac.click/api/v1/reviews/stats?hotel_id=hotel-uuid-1&platform_code=booking"
```

### Check 1 it review mau

```bash
curl "https://data.datac.click/api/v1/reviews?hotel_id=hotel-uuid-1&platform_code=booking&limit=20&offset=0"
```

## 10. Endpoint xoa review theo OTA de lam sach du lieu

Day la endpoint backend noi bo, dung khi Admin / DB / crawl duoc phep lam sach du lieu sai.

### Xoa tat ca review cua 1 hotel + 1 OTA

```bash
curl -X DELETE "https://data.datac.click/api/v1/reviews?hotel_id=<hotel_id>&platform_code=booking"
```

### Xoa review cua 1 hotel + 1 OTA + 1 link cu the

```bash
curl -X DELETE "https://data.datac.click/api/v1/reviews?hotel_id=<hotel_id>&platform_code=booking&source_link=<canonical_link>"
```

### Rule dung endpoint xoa

- `hotel_id` la bat buoc
- `platform_code` la bat buoc
- `source_link` la tuy chon
- neu khong co `source_link`: xoa toan bo review cua OTA do trong hotel do
- neu co `source_link`: chi xoa review gan voi link do
- chi dung khi da co lenh ro rang tu Admin / DB / Leader
- khong duoc tu dong goi endpoint nay trong crawl flow hang ngay

### Xoa 1 review theo review_id

```bash
curl -X DELETE "https://data.datac.click/api/v1/reviews?review_id=<review_id>"
```

- dung khi can xoa rieng 1 dong review test
- neu da truyen `review_id` thi khong can `hotel_id` va `platform_code`

## 11. Cach phan biet dung va sai

### Dung

- lay hotel list tu API
- lay link OTA tu `metadata.source_links`
- giu ten business noi bo
- giu `1 hotel = 1 hotel_id`
- nhieu link cung OTA van post ve cung `hotel_id`
- Agoda link duoc clean

### Sai

- goi `POST /api/v1/hotels` de tao hotel moi
- lay ten Booking roi tao hotel moi
- thay 2 link Booking roi tao 2 hotel
- post review vao sai `hotel_id`
- tu sua link hotel trong database
- goi endpoint reset/import cua admin

## 12. Neu gap du lieu sai

Neu crawler gap mot trong cac tinh huong sau:

- link OTA sai
- hotel dang bi trung
- ten hotel business khac ten OTA
- 1 hotel co qua nhieu link dang nghi trung

Thi xu ly dung la:

1. report lai cho Admin / DB / BE
2. gui kem:
   - `hotel_id`
   - `hotel_name`
   - `platform_code`
   - link dang dung
   - link nghi sai
3. tam thoi khong tu sua DB

## 13. Checklist truoc khi ban giao cho doi crawl

1. Da doc `docs/Crawl/CRAWLER_OTA_ENDPOINT_MATRIX.md`
2. Da doc file nay
3. Da hieu rule `1 hotel + nhieu link cung OTA = 1 hotel_id`
4. Da hieu Agoda phai clean link
5. Da test `GET /api/v1/hotels`
6. Da test `POST /api/v1/sync/reviews/{platform_code}`
7. Da test verify bang `GET /api/v1/reviews/stats`
