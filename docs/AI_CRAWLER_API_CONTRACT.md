# AI Crawler API Contract

Tai lieu nay viet theo kieu machine-friendly de AI crawler, n8n node, hoac integration worker doc nhanh va lam dung.

## 1. Base URL

- Production: `https://data.datac.click`
- Swagger: `https://data.datac.click/docs`

## 2. Tuyet doi khong lam

- Khong ket noi truc tiep PostgreSQL qua internet
- Khong dung `db host:15432` tu tool ben ngoai

Dung API:

```text
Crawler -> HTTPS API -> App -> PostgreSQL
```

## 3. Flow bat buoc

1. Dam bao hotel da ton tai trong he thong
2. Lay `hotel_id`
3. Sync review vao `POST /api/v1/sync/reviews/{platform_code}`
4. Neu can notify:
5. Goi `GET /api/v1/reviews/bad/unnotified?channel_code=lark`
6. Gui sang Lark
7. Goi `POST /api/v1/notifications/deliveries`

## 4. Cach lay `hotel_id`

### Tao hotel

`POST /api/v1/hotels`

Request:

```json
{
  "hotel_code": "ania_airport_residences",
  "hotel_name": "Ania Airport Residences - Next to Holiday Inn",
  "country_code": "VN",
  "city": "Ho Chi Minh City",
  "status": "active",
  "metadata": {
    "source": "crawler_setup"
  }
}
```

### Lay danh sach hotel

`GET /api/v1/hotels?limit=50&offset=0`

Dung truong `id` lam `hotel_id`.

## 5. Endpoint sync review

`POST /api/v1/sync/reviews/{platform_code}`

Platform code hop le:

- `booking`
- `agoda`
- `tripadvisor`
- `google`

## 6. Request schema

Top-level:

```json
{
  "hotel_id": "uuid-string",
  "hotel_platform_account_id": null,
  "triggered_by": "crawler_name",
  "source_total_reviews": 52,
  "reviews": [
    {
      "external_review_id": "string",
      "reviewed_at": "ISO-8601 datetime",
      "source_created_at": "ISO-8601 datetime or null",
      "source_updated_at": "ISO-8601 datetime or null",
      "review_url": "string or null",
      "reviewer_name": "string or null",
      "reviewer_country_code": "string or null",
      "rating": 0,
      "rating_scale": 10,
      "review_title": "string or null",
      "review_text": "string or null",
      "review_language": "string or null",
      "stay_date": "YYYY-MM-DD or null",
      "replied_at": "ISO-8601 datetime or null",
      "sentiment_label": "string or null",
      "is_bad_review": true,
      "reviewer_profile": {},
      "normalized_payload": {},
      "metadata": {},
      "raw_payload": {}
    }
  ]
}
```

## 7. Field rules

### Required

- `hotel_id`
- `reviews`
- `reviews[].external_review_id`
- `reviews[].reviewed_at`
- `reviews[].raw_payload`

### Strongly recommended

- `source_total_reviews`
- `reviews[].rating`
- `reviews[].rating_scale`
- `reviews[].review_title`
- `reviews[].review_text`
- `reviews[].review_language`
- `reviews[].reviewer_name`
- `reviews[].review_url`
- `reviews[].source_updated_at`

### Mapping rules

- OTA review id -> `external_review_id`
- Review date -> `reviewed_at`
- Original title -> `review_title`
- Original content -> `review_text`
- Full raw source object/html/json -> `raw_payload`
- Structured derived values -> `normalized_payload`
- Per-run metadata -> `metadata`

## 8. Translation rule

He thong hien tai chua co cot rieng cho title/text tieng Viet.

Neu crawler hoac translation worker co ban dich tieng Viet, luu vao:

```json
{
  "normalized_payload": {
    "translated_title_vi": "string",
    "translated_text_vi": "string"
  }
}
```

Khong ghi de ban goc trong:

- `review_title`
- `review_text`

Neu backend da bat Google Translate API qua env:

- `TRANSLATION_PROVIDER=google_api`
- `GOOGLE_TRANSLATE_ENABLED=true`
- `GOOGLE_TRANSLATE_API_KEY=...`

thi crawler co the chi can gui ban goc, backend se tu them:

- `normalized_payload.translated_title_vi`
- `normalized_payload.translated_text_vi`
- `normalized_payload.translated_pros_vi`
- `normalized_payload.translated_cons_vi`

Neu backend da bat `googletrans` qua env:

- `TRANSLATION_PROVIDER=googletrans`

thi backend van co the tu them cac field dich o tren ma khong can API key.

Canh bao:

- `googletrans` la thu vien khong chinh thuc
- co the bi gioi han, thay doi hanh vi, hoac fail theo tung thoi diem

Neu crawler da tu dich truoc khi post, backend van chap nhan payload da co san cac field tren.

## 9. Duplicate rule

Duplicate duoc xac dinh boi:

```text
(hotel_id, platform_id, external_review_id)
```

Ket qua:

- cung review sync lai -> update
- khong tao ban ghi moi

Neu sync response la:

```json
{
  "fetched": 3,
  "inserted": 0,
  "updated": 3,
  "status": "success"
}
```

thi nghia la duplicate da duoc xu ly dung.

## 9.1 Review total rule

Crawler nen doc tong review tren OTA va so sanh voi tong review hien co trong DB.

DB co API:

`GET /api/v1/reviews/stats?hotel_id={hotel_id}&platform_code={platform_code}`

Vi du response:

```json
{
  "items": [
    {
      "hotel_id": "uuid-string",
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

Neu OTA hien 52 review va DB hien 50 review:

- crawler co the xem nhu dang thieu khoang `2` review moi
- crawler co the uu tien lay 2 review moi nhat
- sau do post vao endpoint sync

Van phai dung `external_review_id` + upsert de chong sai lech.

## 10. Example request

```json
{
  "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
  "hotel_platform_account_id": null,
  "triggered_by": "booking_crawler_v1",
  "source_total_reviews": 52,
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
      "reviewer_profile": {
        "country_name": "United States",
        "guest_type": "family",
        "room_name": "Deluxe Double Room"
      },
      "normalized_payload": {
        "pros": "Room was clean.",
        "cons": "Front desk was slow.",
        "translated_title_vi": "Can cai thien",
        "translated_text_vi": "Le tan cham nhung phong sach."
      },
      "metadata": {
        "crawl_batch_id": "batch-20260722-0830"
      },
      "raw_payload": {
        "provider": "booking",
        "id": "booking-review-001",
        "positive_text": "Room was clean.",
        "negative_text": "Front desk was slow."
      }
    }
  ]
}
```

## 11. Example response

```json
{
  "sync_job_id": "uuid-string",
  "hotel_id": "56864ae6-f920-4711-94e4-5a2cdc8fff42",
  "platform_code": "booking",
  "source_total_reviews": 52,
  "estimated_new_reviews_from_source": 2,
  "stored_total_reviews_before_sync": 50,
  "stored_total_reviews_after_sync": 52,
  "fetched": 1,
  "inserted": 1,
  "updated": 0,
  "incidents_opened": 1,
  "status": "success"
}
```

## 12. Query after sync

Lay review:

`GET /api/v1/reviews?hotel_id={hotel_id}&limit=20&offset=0`

Lay thong ke tong review trong DB:

`GET /api/v1/reviews/stats?hotel_id={hotel_id}&platform_code={platform_code}`

Lay bad review:

`GET /api/v1/reviews/bad?hotel_id={hotel_id}&limit=20`

Lay bad review chua notify:

`GET /api/v1/reviews/bad/unnotified?channel_code=lark&hotel_id={hotel_id}&limit=20`

Quan trong:

- endpoint nay chi tra danh sach review can gui
- endpoint nay khong tu dong doi trang thai thanh `sent`
- chi sau khi Lark/gui notification tra ket qua that thi moi duoc callback cap nhat trang thai

## 13. Notification callback

Sau khi gui Lark thanh cong:

`POST /api/v1/notifications/deliveries`

Request:

```json
{
  "review_id": "uuid-string",
  "channel_code": "lark",
  "event_type": "bad_review",
  "delivery_status": "sent",
  "target_ref": "ops-review-room",
  "external_message_id": "lark-msg-123",
  "request_payload": {},
  "response_payload": {},
  "metadata": {
    "posted_by": "crawler_or_n8n"
  }
}
```

Neu gui loi:

```json
{
  "review_id": "uuid-string",
  "channel_code": "lark",
  "event_type": "bad_review",
  "delivery_status": "failed",
  "error_message": "timeout from webhook"
}
```

## 13.1 Safe notification flow

Dung flow nay:

1. query bad review chua gui
2. thu post sang Lark
3. neu thanh cong:
   - callback `delivery_status = sent`
4. neu that bai:
   - callback `delivery_status = failed`
5. lan sau tiep tuc retry review `failed`

Khong dung flow nay:

1. query review
2. doi trang thai ngay khi vua query
3. roi moi thu post Lark

Ly do:

- neu Lark loi thi review do se bi mat khoi hang doi notify
- he thong se tuong la da gui xong du chua gui thanh cong

## 14. Operational notes

- `is_bad_review` neu co thi he thong dung gia tri do
- neu khong co `is_bad_review`, he thong suy ra theo threshold rating
- `raw_payload` nen luu toi da du lieu goc co the
- `normalized_payload` nen luu field chuan hoa va field dich tieng Viet
- database la source of truth cho duplicate
