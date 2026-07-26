# Hotel Review Internal Data Platform

Bo khung giai doan 1 cho he thong quan tri review va du lieu noi bo chuoi khach san, toi uu cho PostgreSQL self-host va trien khai local/LAN.

## Muc tieu giai doan 1

- PostgreSQL la single source of truth.
- Gom review tu nhieu nen tang vao mot noi tap trung.
- Chong trung du lieu review khi sync lap lai.
- San sang mo rong sang room type, rate plan, department, service, operational data.
- De noi voi n8n, Lark, Google Sheet va AI analysis service ma khong bien chung thanh data source chinh.

## Cau truc thu muc

```text
.
|-- app
|   |-- api
|   |   `-- routes
|   |-- core
|   |-- db
|   |-- repositories
|   |-- schemas
|   `-- services
|-- db
|   `-- init
|-- Dockerfile
|-- docker-compose.yml
|-- .env.example
|-- docs
|   |-- CRAWLER_HANDOFF_PLAYBOOK.md
|   |-- DB_BACKUP_GOOGLE_DRIVE.md
|   |-- DEPLOY_ONLINE_QUICKSTART.md
|   |-- LEGACY_BOOKING_CLEANUP.md
|   |-- AI_CRAWLER_API_CONTRACT.md
|   `-- POST_REVIEW_GUIDE.md
|-- ops
|   |-- backup
|   |   |-- backup-db.ps1
|   |   `-- restore-db.ps1
|   |-- cleanup
|   |   `-- cleanup_legacy_booking_reviews.py
|   `-- cloudflare
|       |-- config.example.yml
|       `-- tunnel-commands.md
|-- README.md
`-- requirements.txt
```

## Cach chay local

1. Cai Docker va Docker Compose.
2. Trong thu muc project, chay:

```bash
docker compose up -d
```

3. Kiem tra health:

```bash
docker compose ps
```

4. API local:

- Base URL: `http://localhost:13000`
- Swagger: `http://localhost:13000/docs`

5. pgAdmin local:

- URL: `http://localhost:5050`
- Email: `admin@datac.click`
- Password: `admin_123`

6. Ket noi PostgreSQL:

- Host: `localhost`
- Port: `15432`
- Database: `hotel_review_db`
- User: `hotel_admin`
- Password: `hotel_admin_123`

7. Neu muon reset database tu dau:

```bash
docker compose down -v
docker compose up -d
```

Luu y:

- Cac file trong `db/init` chi duoc Postgres image chay tu dong khi volume data moi duoc tao lan dau.
- Service `api` dung `FastAPI` + `SQLAlchemy` + `psycopg`.
- Host port `13000` duoc map vao app de tranh xung dot va de gan voi Cloudflare Tunnel.
- Host port `15432` duoc map vao PostgreSQL de tranh xung dot voi cac DB co san tren may.
- `pgAdmin` duoc bo tri o `localhost:5050` de admin DB ma khong mo PostgreSQL ra internet.

## Kien truc online nhanh

Mo hinh nen dung cho giai doan dau:

```text
User -> domain/subdomain -> Cloudflare Tunnel -> app/backend or pgAdmin -> PostgreSQL
```

Khong nen dung:

```text
User -> domain -> PostgreSQL
```

Ly do:

- PostgreSQL van nam private trong may local/LAN/Docker host.
- Chi public tang app/admin panel, de kiem soat auth va logging.
- De dua len online nhanh ma chua can public DB port `15432`.

## Kien truc schema

Schema duoc tach theo 4 nhom du lieu:

1. Master data
- `hotels`
- `platforms`
- `hotel_platform_accounts`
- `room_types`
- `rate_plans`
- `departments`
- `review_tags`

2. Transactional data
- `reviews`
- `review_replies`
- `incidents`

3. Integration and sync data
- `sync_jobs`
- `audit_logs`

4. AI analysis data
- `ai_analysis_results`

## Nguyen tac thiet ke chinh

- Khong nhom moi thu vao 1 bang lon.
- Truong query/report thuong xuyen duoc tach thanh cot rieng.
- Metadata bien dong theo tung OTA duoc giu trong `JSONB`.
- `reviews.raw_payload` luu full payload goc de truy vet va xu ly schema drift.
- Chong duplicate review bang unique key:

```sql
(hotel_id, platform_id, external_review_id)
```

- Cac worker sync co the dung `INSERT ... ON CONFLICT ... DO UPDATE` de upsert an toan.
- Cac bang con nhu `room_types`, `rate_plans`, `departments` deu theo mo hinh parent-child voi `hotels`.

## Chong trung review

Bang `reviews` bat buoc co:

- `external_review_id`
- `raw_payload JSONB`
- unique constraint `uq_reviews_dedup`

Dieu nay giai quyet bai toan:

- Sync cung 1 review nhieu lan khong tao ban ghi moi.
- Khi OTA cap nhat noi dung/score/reply time, co the upsert de ghi de.
- Van giu payload goc moi nhat de AI va debugging dung lai.

Vi du upsert da duoc dat san trong file:

- [db/init/005_examples.sql](D:/AutoCode/DB/Review/db/init/005_examples.sql)

## Index da toi uu giai doan dau

- Theo hotel: `idx_reviews_hotel_id`
- Theo platform: `idx_reviews_platform_id`
- Theo thoi diem review: `idx_reviews_reviewed_at`
- Theo dashboard hotel + platform + thoi gian: `idx_reviews_hotel_platform_reviewed_at`
- Theo bad review: `idx_reviews_bad_review`
- Theo JSONB payload: `idx_reviews_raw_payload_gin`
- Theo AI analysis lookup: `idx_ai_analysis_lookup`
- Theo JSONB AI payload: `idx_ai_analysis_result_payload_gin`

## Vi tri cua tung bang

### Master data

- `hotels`: thong tin khach san goc.
- `platforms`: danh muc nen tang, da seed `booking`, `agoda`, `tripadvisor`, `google`.
- `hotel_platform_accounts`: mapping moi khach san voi tung tai khoan OTA/review platform.
- `room_types`, `rate_plans`, `departments`: mo rong du lieu van hanh ma khong phai dap lai schema.
- `review_tags`: tag manual hoac AI cho review.

### Transactional data

- `reviews`: bang trung tam.
- `review_replies`: reply tu khach san theo review.
- `incidents`: su co / canh bao / issue phat sinh tu review xau hoac AI.

### Integration data

- `sync_jobs`: log moi lan sync voi OTA, n8n hoac service noi bo.
- `audit_logs`: log thay doi quan trong de trace.

### AI data

- `ai_analysis_results`: luu ket qua sentiment, urgency, root cause, entities, recommendations.

## Cach noi voi n8n, Lark, Google Sheet, AI service

- `n8n`: goi worker/API sync, ghi ket qua vao `sync_jobs`, upsert vao `reviews`.
- `Lark` / `Google Sheet`: chi doc tu PostgreSQL hoac tu API noi bo de hien thi, bao cao, van hanh.
- `AI analysis service`: doc review moi hoac review xau, phan tich, ghi vao `ai_analysis_results`, co the tao `incidents` neu can.

## API da co san

### 1. Healthcheck

```http
GET /health
```

Khi chay local qua Docker:

- `http://localhost:13000/health`

### 2. Tao va lay hotel

Tao hotel:

```http
POST /api/v1/hotels
```

Payload mau:

```json
{
  "hotel_code": "danang_boutique_01",
  "hotel_name": "Da Nang Boutique Hotel",
  "country_code": "VN",
  "city": "Da Nang",
  "status": "active",
  "metadata": {
    "source": "manual_setup"
  }
}
```

Lay danh sach hotel:

```http
GET /api/v1/hotels
```

Khi tao xong, API se tra ve `id`, day chinh la `hotel_id` de dung khi sync review.

### 3. Sync reviews theo platform

```http
POST /api/v1/sync/reviews/{platform_code}
```

Platforms da support mapper skeleton:

- `booking`
- `agoda`
- `tripadvisor`
- `google`

Payload mau:

```json
{
  "hotel_id": "11111111-1111-1111-1111-111111111111",
  "hotel_platform_account_id": null,
  "triggered_by": "n8n",
  "reviews": [
    {
      "external_review_id": "booking-review-001",
      "reviewed_at": "2026-07-22T08:30:00+07:00",
      "source_created_at": "2026-07-22T08:30:00+07:00",
      "source_updated_at": "2026-07-22T08:35:00+07:00",
      "review_url": "https://example.com/review/booking-review-001",
      "reviewer_name": "Alice",
      "reviewer_country_code": "US",
      "rating": 4,
      "rating_scale": 10,
      "review_title": "Need improvement",
      "review_text": "Front desk was slow but room was clean.",
      "review_language": "en",
      "sentiment_label": "mixed",
      "reviewer_profile": {
        "guest_type": "family"
      },
      "normalized_payload": {
        "topics": ["front_desk", "cleanliness"]
      },
      "metadata": {
        "sync_source": "manual_test"
      },
      "raw_payload": {
        "provider": "booking",
        "id": "booking-review-001"
      }
    }
  ]
}
```

Ket qua:

- Upsert vao `reviews`
- Ghi log vao `sync_jobs`
- Neu review bi danh dau `is_bad_review = true` hoac `rating < BAD_REVIEW_RATING_THRESHOLD` thi mo `incident`

### 4. Query reviews

```http
GET /api/v1/reviews
GET /api/v1/reviews/bad
GET /api/v1/reviews/stats
```

Filter co ban:

- `hotel_id`
- `platform_code`
- `limit`
- `offset`

Thong ke tong review theo hotel/platform:

- `GET /api/v1/reviews/stats?hotel_id=...&platform_code=booking`
- dung de so sanh tong review trong DB voi tong review tren OTA
- phu hop cho crawler chi lay phan review moi

### 5. Query incidents

```http
GET /api/v1/incidents
```

Filter co ban:

- `hotel_id`
- `status`
- `severity`

### 6. Lay bad review chua notify theo channel

```http
GET /api/v1/reviews/bad/unnotified?channel_code=lark
```

Vi du:

```bash
curl "https://data.datac.click/api/v1/reviews/bad/unnotified?channel_code=lark&limit=20"
```

Logic:

- chi lay `is_bad_review = true`
- bo qua review da co `notification_deliveries.delivery_status = 'sent'`
- van lay lai review neu chua tung gui hoac gui loi

### 7. Danh dau da gui notification

```http
POST /api/v1/notifications/deliveries
```

Payload mau:

```json
{
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
}
```

Neu gui loi:

```json
{
  "review_id": "11111111-1111-1111-1111-111111111111",
  "channel_code": "lark",
  "event_type": "bad_review",
  "delivery_status": "failed",
  "error_message": "timeout from webhook"
}
```

## Goi y buoc tiep theo de code API sync review

1. Ket noi API nay voi n8n de goi `POST /api/v1/sync/reviews/{platform_code}` theo lich.
2. Them bang/luong quan ly credentials an toan cho OTA account.
3. Viet adapter fetch thuc te cho tung platform thay vi day raw payload thu cong.
4. Them worker AI:
- doc review xau chua phan tich
- ghi `ai_analysis_results`
- update tag / root cause / urgency

5. Chuan bi automation n8n:
- schedule sync theo gio
- canh bao khi co bad review moi
- gui digest hang ngay qua Lark hoac email

## Khuyen nghi thuc dung cho giai doan dau

- Chua can tach schema PostgreSQL thanh qua nhieu namespace.
- Chua can event bus hay microservice.
- Chua can public Postgres len internet.
- Neu can remote access, dat API/backend sau Cloudflare Tunnel hoặc Zero Trust, Postgres chi bind noi bo/LAN/VPN.

## Cach public online nhanh bang Cloudflare Tunnel

File huong dan va mau config da co san:

- [ops/cloudflare/tunnel-commands.md](D:/AutoCode/DB/Review/ops/cloudflare/tunnel-commands.md)
- [ops/cloudflare/config.example.yml](D:/AutoCode/DB/Review/ops/cloudflare/config.example.yml)
- [docs/DEPLOY_ONLINE_QUICKSTART.md](D:/AutoCode/DB/Review/docs/DEPLOY_ONLINE_QUICKSTART.md)
- [docs/DB_BACKUP_GOOGLE_DRIVE.md](D:/AutoCode/DB/Review/docs/DB_BACKUP_GOOGLE_DRIVE.md)
- [docs/LEGACY_BOOKING_CLEANUP.md](D:/AutoCode/DB/Review/docs/LEGACY_BOOKING_CLEANUP.md)
- [docs/CRAWLER_HANDOFF_PLAYBOOK.md](D:/AutoCode/DB/Review/docs/CRAWLER_HANDOFF_PLAYBOOK.md)
- [docs/AI_CRAWLER_API_CONTRACT.md](D:/AutoCode/DB/Review/docs/AI_CRAWLER_API_CONTRACT.md)
- [docs/POST_REVIEW_GUIDE.md](D:/AutoCode/DB/Review/docs/POST_REVIEW_GUIDE.md)
- [docs/AGODA_UPLOAD_GUIDE.md](D:/AutoCode/DB/Review/docs/AGODA_UPLOAD_GUIDE.md)
- [docs/WEBSITE_DB_HANDOFF.md](D:/AutoCode/DB/Review/docs/WEBSITE_DB_HANDOFF.md)
- [docs/WEBSITE_QUERY_GUIDE.md](D:/AutoCode/DB/Review/docs/WEBSITE_QUERY_GUIDE.md)
- [docs/DASHBOARD_ANALYTICS_ARCHITECTURE.md](D:/AutoCode/DB/Review/docs/DASHBOARD_ANALYTICS_ARCHITECTURE.md)
- [docs/BACKEND_ANALYTICS_TASK.md](D:/AutoCode/DB/Review/docs/BACKEND_ANALYTICS_TASK.md)
- [docs/ANALYTICS_BACKFILL_RUNBOOK.md](D:/AutoCode/DB/Review/docs/ANALYTICS_BACKFILL_RUNBOOK.md)

Flow nhanh:

1. Chay `docker compose up -d`
2. Kiem tra app tai `http://localhost:13000`
3. Kiem tra pgAdmin tai `http://localhost:5050`
4. Cai `cloudflared`
5. Tao tunnel va DNS route
6. Map:
- `data.datac.click -> http://localhost:13000`
- `pgadmin.tenmiencuaban.com -> http://localhost:5050`

Neu chi can admin DB tam thoi thi public `pgAdmin`; neu can workflow nghiep vu thi public app/API.

Bo khung nay du cho anh/chị bat dau code backend sync review ngay ma van giu duoc kha nang mo rong sang pricing va operational data ve sau.
