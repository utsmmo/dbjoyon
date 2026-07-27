# Web Hotel Review

Project web review khach san da tach khoi monorepo chinh de co the dua len repo rieng va deploy truc tiep tai `joyon.asia`.

## Kien truc

- `frontend-web`: Next.js dashboard + review workspace
- `backend-api`: NestJS API cho hotel, reviews, analytics
- `database`: schema va tai lieu lien quan DB
- `infra`: mau Nginx reverse proxy cho `joyon.asia`
- `infra/cloudflare`: mau Cloudflare Tunnel neu deploy qua Cloudflare

## Cach chay local

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

### Bien moi truong local

- `NEXT_PUBLIC_BASE_PATH=`
- `NEXT_PUBLIC_API_BASE_URL=http://localhost:3001/api`
- `INTERNAL_API_BASE_URL=http://localhost:3001/api`
- `FRONTEND_URL=http://localhost:3000`
- `DATABASE_URL=postgresql://hotel_admin:hotel_admin_123@localhost:15432/hotel_review_db`

## Deploy len joyon.asia

### Docker Compose

```bash
docker compose up -d --build
```

Mac dinh file `docker-compose.yml` da duoc doi de:

- frontend chay o root domain `/`
- backend public qua `/api/`
- CORS cho phep `joyon.asia` va `www.joyon.asia`
- frontend noi bo goi backend qua `INTERNAL_API_BASE_URL=http://backend-api:3001/api`

### Production Docker cho joyon.asia

Repo da co san bo file production:

- `docker-compose.prod.yml`
- `.env.production.example`
- `infra/nginx/joyon.conf`

Tren may deploy:

```bash
cp .env.production.example .env.production
docker compose -f docker-compose.prod.yml --env-file .env.production up -d --build
```

Mau nay chay theo huong:

- `nginx` public cong `80`
- `frontend-web` chi chay noi bo trong Docker network
- `backend-api` chi chay noi bo trong Docker network
- `postgres` chi chay noi bo trong Docker network

Luu y quan trong:

- Browser truy cap `https://joyon.asia`
- Nginx se forward tat ca request vao `frontend-web`
- Cac route `/api/*` cua website van di qua Next.js frontend
- Frontend server-side moi goi `backend-api` qua `INTERNAL_API_BASE_URL`

Neu server cua ban co SSL o ngoai Docker, chi can reverse proxy domain `joyon.asia` vao port `80` cua container `nginx`.
Neu ban muon SSL ngay trong Docker, minh co the viet them bo `nginx + certbot` cho ban.
Trong bo compose production hien tai, host port dang map la `9979 -> 80`.

### Nginx

File mau: `infra/nginx/review.conf`

- `location /` proxy vao frontend
- `location /api/` proxy vao backend
- `server_name joyon.asia www.joyon.asia`

Neu server dung SSL, can bo sung block `listen 443 ssl` va cert tuong ung.

Cho production Docker trong repo nay, file uu tien dung la:

- `infra/nginx/joyon.conf`

### Cloudflare Tunnel

Neu `joyon.asia` dang di qua Cloudflare, co the dung file mau:

- `infra/cloudflare/config.example.yml`

Luot setup co ban:

```bash
cloudflared tunnel login
cloudflared tunnel create joyon-workspace
cloudflared tunnel route dns joyon-workspace joyon.asia
cloudflared tunnel route dns joyon-workspace www.joyon.asia
cloudflared tunnel run joyon-workspace
```

Voi bo production hien tai, Cloudflare Tunnel nen forward vao:

- `http://localhost:9979`

## Luu y bao mat

- Khong commit file `.env`
- `REVIEW_AI_API_KEY` phai duoc cap qua env, khong hardcode trong source
- Neu dung AI insights, can set them:
  - `REVIEW_AI_BASE_URL`
  - `REVIEW_AI_API_KEY`
  - `REVIEW_AI_MODEL`

## Dashboard direction

- Summary cards: tong review, diem trung binh, so khach san, quoc gia top 1
- Filter bar: hotel, country, score, source, time range, text search
- Charts: phan bo diem, review theo khach san, review theo quoc gia
- AI Insights: tong ket sentiment, van de noi bat, goi y cai thien
