# Web Hotel Review

Project demo review khach san tach biet hoan toan khoi he thong crawl/API hien tai.

## Kien truc

- `frontend-web`: website review + admin panel
- `backend-api`: auth, RBAC, hotels, reviews, dashboard API
- `database`: Prisma schema, seed, ghi chu migration
- `infra`: nginx route mau cho `/review`

## Dashboard direction

- Summary cards: tong review, diem trung binh, so khach san, quoc gia top 1
- Filter bar: hotel, country, score, source, time range, text search
- Charts: phan bo diem, review theo khach san, review theo quoc gia
- AI Insights: tong ket sentiment, van de noi bat, goi y cai thien

## Chay local

### Frontend

```bash
cd frontend-web
pnpm dev
```

### Backend

```bash
cd backend-api
pnpm start:dev
```

Frontend doc env:

- `NEXT_PUBLIC_BASE_PATH=/review`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:3001/api`
- `DATABASE_URL=postgresql://hotel_admin:hotel_admin_123@localhost:15432/hotel_review_db`

Luu y:

- Tai lieu cu cho thay DB hien tai dang dung `hotel_review_db`
- user: `hotel_admin`
- host port local: `15432`
- luc minh kiem tra ngay `2026-07-25`, port `15432` dang dong, nen chua the doc du lieu that truc tiep tu local DB

## AI analysis roadmap

Review da duoc chuan bi san cac truong:

- `sentiment_label`
- `sentiment_score`
- `keywords`
- `summary`
- `analysis_version`
- `detected_language`

Giai doan dau backend dung bo phan tich mock de demo nhanh. Giai doan sau co the thay bang OpenAI batch analysis hoac queue worker ma khong can doi frontend.
