# Huong Dan Post Review Va Notify

Tai lieu nay danh cho:

- n8n workflow
- scraper worker
- webhook service
- integration script
- AI tool can post review vao he thong

Base URL hien tai:

- `https://data.datac.click`

Swagger:

- `https://data.datac.click/docs`

## Nguyen tac kien truc

Khong post truc tiep vao PostgreSQL qua internet.

Luong dung:

```text
Tool ngoai -> Cloudflare Tunnel -> API app -> PostgreSQL
```

Khong dung:

```text
Tool ngoai -> PostgreSQL:15432
```

## Luong toi thieu de day review

1. Tao hotel neu he thong chua co hotel do
2. Lay `hotel_id`
3. Goi `POST /api/v1/sync/reviews/{platform_code}`
4. Neu can notify, goi `GET /api/v1/reviews/bad/unnotified`
5. Gui sang Lark/Slack
6. Goi `POST /api/v1/notifications/deliveries` de danh dau da gui

## 1. Tao hotel va lay `hotel_id`

### Tao hotel

```bash
curl -X POST "https://data.datac.click/api/v1/hotels" \
  -H "Content-Type: application/json" \
  -d '{
    "hotel_code": "ania_airport_residences",
    "hotel_name": "Ania Airport Residences - Next to Holiday Inn",
    "country_code": "VN",
    "city": "Ho Chi Minh City",
    "status": "active",
    "metadata": {
      "source": "manual_setup",
      "booking_url": "https://www.booking.com/hotel/vn/ania-airport-residences-next-to-holiday-inn.html"
    }
  }'
```

### Lay danh sach hotel

```bash
curl "https://data.datac.click/api/v1/hotels?limit=50&offset=0"
```

`id` trong response chinh la `hotel_id`.

Vi du:

```json
{
  "items": [
    {
      "id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
      "hotel_code": "republic_airport_residences",
      "hotel_name": "Republic Airport Residences - Next to Holiday Inn"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0
}
```

## 2. Endpoint dung de post review

```http
POST /api/v1/sync/reviews/{platform_code}
```

Platform code hop le hien tai:

- `booking`
- `agoda`
- `tripadvisor`
- `google`

Vi du:

- `POST https://data.datac.click/api/v1/sync/reviews/booking`
- `POST https://data.datac.click/api/v1/sync/reviews/agoda`

## 3. Muc tieu cua endpoint sync

Endpoint nay se:

1. nhan batch review
2. normalize field co ban
3. upsert vao `reviews`
4. chong duplicate bang unique key
5. ghi log vao `sync_jobs`
6. mo `incident` neu review la review xau

## 4. Co che chong duplicate

Database da co unique key:

```sql
(hotel_id, platform_id, external_review_id)
```

Va dang dung `upsert`:

```sql
INSERT ... ON CONFLICT (hotel_id, platform_id, external_review_id) DO UPDATE
```

Y nghia:

- Cung 1 review cua cung 1 hotel tren cung 1 platform se khong tao dong moi
- Sync lai se update review cu
- Day la noi check duplicate dung nhat vi database la source of truth

## 5. Payload toi thieu va payload khuyen nghi

### Bat buoc

- `hotel_id`
- `reviews[]`
- `reviews[].external_review_id`
- `reviews[].reviewed_at`
- `reviews[].raw_payload`

### Rat nen co

- `reviews[].rating`
- `reviews[].rating_scale`
- `reviews[].review_title`
- `reviews[].review_text`
- `reviews[].review_language`
- `reviews[].reviewer_name`
- `reviews[].reviewer_country_code`
- `reviews[].review_url`
- `reviews[].source_updated_at`

### Payload mau day du

```json
{
  "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
  "hotel_platform_account_id": null,
  "triggered_by": "crawler_booking_v1",
  "reviews": [
    {
      "external_review_id": "booking-review-001",
      "reviewed_at": "2026-07-22T08:30:00+07:00",
      "source_created_at": "2026-07-22T08:30:00+07:00",
      "source_updated_at": "2026-07-22T08:35:00+07:00",
      "review_url": "https://www.booking.com/review/booking-review-001",
      "reviewer_name": "Alice",
      "reviewer_country_code": "US",
      "rating": 4,
      "rating_scale": 10,
      "review_title": "Need improvement",
      "review_text": "Front desk was slow but room was clean.",
      "review_language": "en",
      "stay_date": "2026-07-20",
      "replied_at": null,
      "sentiment_label": "mixed",
      "is_bad_review": true,
      "reviewer_profile": {
        "guest_type": "family",
        "room_name": "Deluxe Double Room",
        "nights": 2,
        "country_name": "United States"
      },
      "normalized_payload": {
        "pros": "Room was clean.",
        "cons": "Front desk was slow.",
        "travel_type": "family",
        "room_text": "Deluxe Double Room",
        "translated_title_vi": "Can cai thien",
        "translated_text_vi": "Le tan cham nhung phong sach."
      },
      "metadata": {
        "sync_source": "crawler_booking_v1",
        "crawl_batch_id": "batch-20260722-0830",
        "otel_hotel_code": "ania_airport_residences"
      },
      "raw_payload": {
        "provider": "booking",
        "id": "booking-review-001",
        "original_score": 4,
        "reviewer_name": "Alice",
        "review_country": "United States",
        "title": "Need improvement",
        "positive_text": "Room was clean.",
        "negative_text": "Front desk was slow.",
        "full_card_html": "<optional raw html block or source fragment>"
      }
    }
  ]
}
```

## 6. Quy uoc mapping field cho crawler

Khi crawl review, tool nen map nhu sau:

| Nguon crawl | Field trong API |
|---|---|
| id review ben OTA | `external_review_id` |
| ngay review | `reviewed_at` |
| ngay tao ben source | `source_created_at` |
| ngay source update lan cuoi | `source_updated_at` |
| ten nguoi review | `reviewer_name` |
| quoc gia reviewer dang code 2 ky tu neu co | `reviewer_country_code` |
| diem review | `rating` |
| thang diem | `rating_scale` |
| title review | `review_title` |
| noi dung review tong hop | `review_text` |
| ngon ngu goc | `review_language` |
| link review | `review_url` |
| thong tin linh tinh da chuan hoa | `normalized_payload` |
| full du lieu goc | `raw_payload` |

Neu source tach rieng:

- phan khen
- phan che
- room name
- guest type
- trip type
- nights

thi nen:

- dua ban tong hop vao `review_text`
- dua chi tiet vao `normalized_payload`
- dua full source vao `raw_payload`

## 7. Khuyen nghi de luu song ngu

He thong hien tai chua co cot rieng cho ban dich VI trong bang `reviews`.
De chay nhanh giai doan nay, tool crawl hoac AI translation worker nen luu:

- text goc trong `review_title`, `review_text`
- ban dich tieng Viet trong `normalized_payload`

Vi du:

```json
{
  "review_title": "Exceptional",
  "review_text": "Very helpful staff. Clean. Perfect location close to old town.",
  "normalized_payload": {
    "translated_title_vi": "Rat tuyet",
    "translated_text_vi": "Nhan vien rat ho tro. Sach se. Vi tri rat tot, gan pho co."
  }
}
```

Neu sau nay muon query/report ban dich nhieu, khi do moi nen tach them cot rieng.

## 7.1 Dich tu dong bang Google Translate

He thong da co san bo khung de tu dong goi Google Translate khi sync review.

Bat cac bien moi truong sau trong `.env`:

```env
TRANSLATION_PROVIDER=google_api
GOOGLE_TRANSLATE_ENABLED=true
GOOGLE_TRANSLATE_API_KEY=your_google_api_key
GOOGLE_TRANSLATE_TARGET_LANGUAGE=vi
GOOGLE_TRANSLATE_TIMEOUT_SECONDS=15
```

Khi bat tinh nang nay:

- he thong giu nguyen `review_title`, `review_text` ban goc
- he thong tu dich sang tieng Viet va luu vao `normalized_payload`
- he thong co the tu detect ngon nguon neu `review_language` khong co

Mac dinh se dich cac field neu co:

- `review_title` -> `normalized_payload.translated_title_vi`
- `review_text` -> `normalized_payload.translated_text_vi`
- `normalized_payload.pros` -> `normalized_payload.translated_pros_vi`
- `normalized_payload.cons` -> `normalized_payload.translated_cons_vi`

Metadata dich them:

- `normalized_payload.translation_provider`
- `normalized_payload.translation_target_language`
- `normalized_payload.translation_detected_source_language`

## 7.2 Dich khong can API key bang `googletrans`

Neu muon chay theo huong khong can key, he thong cung ho tro `googletrans`.

Bat trong `.env`:

```env
TRANSLATION_PROVIDER=googletrans
GOOGLE_TRANSLATE_TARGET_LANGUAGE=vi
GOOGLE_TRANSLATE_TIMEOUT_SECONDS=15
```

Luu y quan trong:

- `googletrans` la thu vien Python khong chinh thuc, khong phai Google API chinh thuc
- co the on trong giai doan dau, nhung co nguy co bi block hoac luc dung luc hong
- phu hop de test nhanh, noi bo, hoac luu luong nho
- khong nen xem day la phuong an production on dinh lau dai

## 8. cURL mau de sync review

```bash
curl -X POST "https://data.datac.click/api/v1/sync/reviews/booking" \
  -H "Content-Type: application/json" \
  -d '{
    "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
    "hotel_platform_account_id": null,
    "triggered_by": "crawler_booking_v1",
    "reviews": [
      {
        "external_review_id": "booking-review-001",
        "reviewed_at": "2026-07-22T08:30:00+07:00",
        "source_created_at": "2026-07-22T08:30:00+07:00",
        "source_updated_at": "2026-07-22T08:35:00+07:00",
        "review_url": "https://www.booking.com/review/booking-review-001",
        "reviewer_name": "Alice",
        "reviewer_country_code": "US",
        "rating": 4,
        "rating_scale": 10,
        "review_title": "Need improvement",
        "review_text": "Front desk was slow but room was clean.",
        "review_language": "en",
        "is_bad_review": true,
        "normalized_payload": {
          "translated_title_vi": "Can cai thien",
          "translated_text_vi": "Le tan cham nhung phong sach."
        },
        "raw_payload": {
          "provider": "booking",
          "id": "booking-review-001"
        }
      }
    ]
  }'
```

## 9. Response mau

```json
{
  "sync_job_id": "9e7abbbb-1111-2222-3333-444444444444",
  "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
  "platform_code": "booking",
  "fetched": 1,
  "inserted": 1,
  "updated": 0,
  "incidents_opened": 1,
  "status": "success"
}
```

Cach hieu:

- `inserted > 0`: co review moi
- `updated > 0`: review da ton tai va da duoc upsert
- `inserted = 0` va `updated > 0`: duplicate da duoc xu ly dung

## 10. Query review de kiem tra da vao DB chua

### Lay thong ke tong review theo hotel/platform

```bash
curl "https://data.datac.click/api/v1/reviews/stats?hotel_id=56864ae6-f920-4711-94e4-5a2cdc8fff42"
```

Vi du response:

```json
{
  "items": [
    {
      "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
      "platform_code": "booking",
      "total_reviews": 50,
      "bad_reviews": 8,
      "latest_reviewed_at": "2026-07-22T22:37:00+07:00",
      "latest_source_updated_at": "2026-07-22T22:37:00+07:00"
    }
  ],
  "total": 1
}
```

Neu muon loc theo tung platform:

```bash
curl "https://data.datac.click/api/v1/reviews/stats?hotel_id=56864ae6-f920-4711-94e4-5a2cdc8fff42&platform_code=booking"
```

Y nghia:

- `total_reviews`: tong so review hien dang co trong database
- `bad_reviews`: tong so review xau trong database
- `latest_reviewed_at`: review moi nhat theo ngay review
- `latest_source_updated_at`: thoi diem source update moi nhat da luu

Day la API de crawler so sanh voi tong review tren OTA.

### Cach dung thong ke tong review de chi crawl phan chenh lech

Vi du:

- trong database: `total_reviews = 50`
- tren Booking hien tai: `source_total_reviews = 52`

Khi do:

- he thong dang thieu it nhat `2` review moi
- crawler co the uu tien lay 2 review moi nhat truoc

Flow de nghi:

1. goi `GET /api/v1/reviews/stats?hotel_id=...&platform_code=booking`
2. lay `total_reviews` hien co trong DB
3. crawler doc tong review tren OTA
4. tinh:
   - `estimated_new_reviews = source_total_reviews - total_reviews`
5. neu `estimated_new_reviews > 0`
   - crawl phan review moi nhat theo so luong do
6. post vao `POST /api/v1/sync/reviews/booking`

Luu y:

- day la cach practical de giam so luong crawl
- van nen co `external_review_id` + upsert de tranh sot neu tong review tren OTA thay doi khong dung 100%

### Lay tat ca review

```bash
curl "https://data.datac.click/api/v1/reviews?limit=10&offset=0"
```

### Loc theo hotel

```bash
curl "https://data.datac.click/api/v1/reviews?hotel_id=56864ae6-f920-4711-94e4-5a2cdc8fff42&limit=10&offset=0"
```

### Lay review xau

```bash
curl "https://data.datac.click/api/v1/reviews/bad?hotel_id=56864ae6-f920-4711-94e4-5a2cdc8fff42&limit=20"
```

## 11. Logic review xau

Neu payload gui len co `is_bad_review`, he thong uu tien dung gia tri do.

Neu khong gui `is_bad_review`, he thong tu suy ra theo env:

- `BAD_REVIEW_RATING_THRESHOLD`

Giá trị hiện tại đang để:

- `9`

Nghia la:

- `rating < 9` => bad review

## 11.1 Gui them tong review tu OTA khi sync

Endpoint sync da ho tro them field:

- `source_total_reviews`

Vi du:

```json
{
  "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
  "triggered_by": "crawler_booking_v1",
  "source_total_reviews": 52,
  "reviews": [
    {
      "external_review_id": "booking-review-051",
      "reviewed_at": "2026-07-23T09:00:00+07:00",
      "raw_payload": {
        "provider": "booking"
      }
    },
    {
      "external_review_id": "booking-review-052",
      "reviewed_at": "2026-07-23T09:05:00+07:00",
      "raw_payload": {
        "provider": "booking"
      }
    }
  ]
}
```

Response sync se co them:

- `source_total_reviews`
- `estimated_new_reviews_from_source`
- `stored_total_reviews_before_sync`
- `stored_total_reviews_after_sync`

Vi du:

```json
{
  "sync_job_id": "uuid-string",
  "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
  "platform_code": "booking",
  "source_total_reviews": 52,
  "estimated_new_reviews_from_source": 2,
  "stored_total_reviews_before_sync": 50,
  "stored_total_reviews_after_sync": 52,
  "fetched": 2,
  "inserted": 2,
  "updated": 0,
  "incidents_opened": 0,
  "status": "success"
}
```

Y nghia:

- `stored_total_reviews_before_sync`: tong review trong DB truoc khi sync
- `stored_total_reviews_after_sync`: tong review trong DB sau khi sync
- `estimated_new_reviews_from_source`: so review chenh lech OTA so voi DB truoc sync

## 12. API cho notification

### Lay bad review chua notify theo channel

```bash
curl "https://data.datac.click/api/v1/reviews/bad/unnotified?channel_code=lark&limit=20"
```

Logic:

- chi lay `is_bad_review = true`
- bo qua review da co `delivery_status = sent` cho cung `review_id + channel_code + event_type`
- chi la query de lay danh sach, khong tu dong doi trang thai

### Danh dau gui thanh cong

```bash
curl -X POST "https://data.datac.click/api/v1/notifications/deliveries" \
  -H "Content-Type: application/json" \
  -d '{
    "review_id": "11111111-1111-1111-1111-111111111111",
    "channel_code": "lark",
    "event_type": "bad_review",
    "delivery_status": "sent",
    "target_ref": "ops-review-room",
    "external_message_id": "lark-msg-123",
    "request_payload": {
      "webhook": "lark-webhook-1"
    },
    "response_payload": {
      "code": 0
    },
    "metadata": {
      "posted_by": "n8n"
    }
  }'
```

### Danh dau gui that bai

```bash
curl -X POST "https://data.datac.click/api/v1/notifications/deliveries" \
  -H "Content-Type: application/json" \
  -d '{
    "review_id": "11111111-1111-1111-1111-111111111111",
    "channel_code": "lark",
    "event_type": "bad_review",
    "delivery_status": "failed",
    "error_message": "timeout from webhook"
  }'
```

## 13. Logic chong gui trung notification

Database da co unique key:

```sql
(review_id, channel_code, event_type)
```

Nghia la:

- moi review co the notify nhieu kenh
- moi kenh chi co 1 record log chinh cho moi event
- goi lai se update record cu, khong tao duplicate

## 13.1 Quy tac dung de tranh mat notification

Khong duoc coi viec query ra review la da gui thanh cong.

Flow dung:

1. goi `GET /api/v1/reviews/bad/unnotified?channel_code=lark`
2. nhan danh sach bad review can gui
3. tool cua anh/chị thu post tung review sang Lark
4. neu Lark tra ve thanh cong that su:
   - goi `POST /api/v1/notifications/deliveries`
   - `delivery_status = sent`
5. neu Lark gui loi:
   - goi `POST /api/v1/notifications/deliveries`
   - `delivery_status = failed`
6. lan query sau:
   - review da `sent` se khong bi lay lai
   - review `failed` van co the duoc lay lai de retry

Khong nen lam theo kieu:

1. query ra review
2. doi trang thai ngay lap tuc
3. moi bat dau post sang Lark

Vi neu Lark loi o buoc sau thi review do co the bi bo sot va khong duoc gui lai.

## 13.2 Vi du flow retry an toan

Lan 1:

- query duoc review `R1`
- post Lark bi timeout
- goi callback:
  - `delivery_status = failed`

Lan 2:

- query lai
- `R1` van xuat hien trong danh sach unnotified hoac retry
- post Lark thanh cong
- goi callback:
  - `delivery_status = sent`

Luc do `R1` moi duoc xem la da gui xong.

## 14. Ket luan ngan cho tool ngoai

Neu la AI crawler/tool crawl thi can nho:

1. khong post truc tiep vao Postgres
2. luon dung `hotel_id`
3. luon gui `external_review_id`
4. luon gui `raw_payload`
5. neu co ban dich VI, luu vao `normalized_payload`
6. sau khi sync xong, query `bad/unnotified` roi moi notify Lark

Neu can mot file spec gon hon cho AI tool doc truc tiep, dung file:

- [docs/AI_CRAWLER_API_CONTRACT.md](D:/AutoCode/DB/Review/docs/AI_CRAWLER_API_CONTRACT.md)
