# Review API Timeout Report - 2026-07-26

## 1. Muc dich

File nay tong hop:

- nhung thay doi da duoc thuc hien o nhanh backend/database/frontend lien quan den `GET /api/v1/reviews`
- trang thai production duoc retest vao `Sunday, July 26, 2026`
- nhan dinh nguyen nhan hien tai
- checklist can kiem tra tiep de fix dut diem

Muc tieu la de gui sang team khac hoac paste vao ticket, khong can tong hop lai bang tay.

## 2. Ket luan ngan

Tinh den `Sunday, July 26, 2026`, sau khi doi DB thong bao da xu ly, production da **cai thien mot phan** nhung van **chua on dinh hoan toan** va bug chua the dong.

Loi chinh van nam o nhanh:

- `GET /api/v1/reviews`

Khong phai o phan:

- CSS
- frontend rendering
- chart rendering

Analytics path van con song mot phan, nhung row-data path cho bang review van timeout o case baseline lon. Nghia la nhan dinh "van de nam o backend/query path" van con dung sau re-check, chi la mot so query filter nho da tot hon truoc.

## 3. Cac thay doi da duoc lam

### 3.1 Backend query path

Da sua file:

- [app/repositories/review_repository.py](D:/AutoCode/DB/Review/app/repositories/review_repository.py)
- [app/services/review_query_service.py](D:/AutoCode/DB/Review/app/services/review_query_service.py)
- [app/api/routes/reviews.py](D:/AutoCode/DB/Review/app/api/routes/reviews.py)

Noi dung da sua:

- tach logic build filter SQL thanh ham rieng de query de doc va de toi uu hon
- bo `COUNT(*) OVER()` tren full result set cua `/reviews`
- them `count query` rieng
- dung CTE `page_ids` de lay dung ID cua page hien tai roi moi join sang `reviews`, `hotels`, `platforms`
- bo mac dinh `translate + update DB` ngay trong luc `GET /reviews`
- chuyen `is_bad_review` ve logic tinh toan tren response, tranh write-back vao DB trong read path
- mo them query param `hydrate_missing_translations=false` de chi hydrate khi that su can

### 3.2 Frontend dashboard

Da sua file:

- [web-hotel-review/frontend-web/components/review-dashboard.tsx](D:/AutoCode/DB/Review/web-hotel-review/frontend-web/components/review-dashboard.tsx)

Noi dung da sua:

- bo kieu load toan bo dataset qua nhieu page roi moi render
- chuyen sang server-side pagination dung nghia
- page hien tai chi fetch dung so row can hien thi
- giam kha nang frontend tu tao ra request rat nang

### 3.3 Database performance indexes

Da them migration:

- [db/migrations/011_review_query_performance_indexes.sql](D:/AutoCode/DB/Review/db/migrations/011_review_query_performance_indexes.sql)

Migration nay them cac index phuc vu query that te:

- `(platform_id, reviewed_at desc)`
- `(platform_id, rating desc, reviewed_at desc) where rating is not null`
- `(reviewer_country_code, reviewed_at desc) where reviewer_country_code is not null`
- `(platform_id, is_bad_review, reviewed_at desc)`

## 4. Kiem tra code da lam

Da verify local:

- Python compile pass cho backend files lien quan
- `npm run lint` pass cho frontend web

Tuc la:

- code local khong vo hieu
- syntax va lint co ban da on

Nhung:

- compile/lint pass **khong dong nghia** production da on

## 5. Ket qua retest production ngay 2026-07-26

Thong tin do user cung cap sau khi retest production:

### 5.1 Re-check sau khi doi DB bao da fix

Da goi lai truc tiep cac endpoint production-facing qua local proxy `http://localhost:3000/review` vao `Sunday, July 26, 2026`.

Ket qua moi nhat:

- `default limit=200` van `504` sau khoang `15.0s`
- `rating_min=10&limit=12&offset=0` tra `200` trong khoang `1.6s`
- `platform_code=booking&limit=12&offset=0` tra `200` trong khoang `3.9s`
- `rating_max=8&limit=12&offset=0` tra `200` trong khoang `5.0s`
- `is_bad_review=true&limit=12&offset=0` tra `200` trong khoang `3.3s`
- `platform_code=agoda&is_bad_review=true&limit=12&offset=0` tra `200` trong khoang `0.8s`

Dieu nay cho thay fix cua doi DB **da cai thien mot phan** query path cho `/api/v1/reviews`, nhat la voi nhung request da duoc thu hep page size.

### 5.2 Cac case van loi

`/review/api/reviews` van timeout hoac 504 o case chinh:

- baseline `limit=200` van `504` sau khoang `15s`

### 5.3 Cac case con tra duoc

- `rating_min=10&limit=12&offset=0` tra `200` trong khoang `1.6s`
- `platform_code=booking&limit=12&offset=0` tra `200` trong khoang `3.9s`
- `rating_max=8&limit=12&offset=0` tra `200` trong khoang `5.0s`
- `is_bad_review=true&limit=12&offset=0` tra `200` trong khoang `3.3s`
- `platform_code=agoda&is_bad_review=true&limit=12&offset=0` tra nhanh hon, khoang `0.8s`

### 5.4 Hien trang UI

Tren UI `/review`, re-check cho thay:

- trang van co the bi ket o trang thai loading sau khi reload
- `Summary` co the hien so lieu trong khi `Review Table` chua settle
- case `Max rating = 8` cho thay summary co thay doi, nhung table/insights chua duoc xac nhan sync on dinh 100%
- case `Min rating = 10` khong con vo timeout ngay lap tuc, nhung UX tren UI van chua duoc xac nhan settle sach

### 5.5 Analytics path van song nhung khong giai cuu duoc table

Da check lai `/review/api/reviews-analytics`:

- default van tra `200` nhanh
- `platform_code=booking` van tra `200`
- `rating_min=10`, `rating_max=8`, `is_bad_review=true` van tra `200` nhung co `unsupported_filters`

Y nghia:

- analytics path khong phai diem nghen chinh
- row-data path cua `/review/api/reviews` van la noi gay ra su lech giua summary va review table
- production dang o trang thai "tot hon truoc", nhung chua du on dinh de dong ticket

## 6. Nhan dinh nguyen nhan hien tai

Nguyen nhan kha nang cao nhat van la:

- **backend/query-path instability on `/api/v1/reviews`**

Khong phai nguyen nhan chinh tu frontend rendering.

Bang chung:

- analytics endpoints van con tra du lieu
- row-data endpoint `/api/v1/reviews` van timeout o broad queries

Dieu nay cho thay:

- aggregate/analytics path con hoat dong mot phan
- row-data query path van chua duoc toi uu dung cach tren production
- frontend chi la noi bieu hien trieu chung, khong phai goc loi chinh

## 7. Gia thuyet ky thuat kha nang cao

### 7.1 Ban code moi chua len dung production

Co the code local da sua, nhung production chua chay dung ban moi.

### 7.2 Migration index chua duoc apply day du hoac chua phat huy dung cho broad query

Co the migration:

- [db/migrations/011_review_query_performance_indexes.sql](D:/AutoCode/DB/Review/db/migrations/011_review_query_performance_indexes.sql)

chua duoc apply tren DB production.

Neu dung vay, query plan cho:

- `platform_code=booking`
- `rating_min=10`
- broad requests

van co the rat nang, dac biet o baseline lon.

### 7.3 Query plan tren production chua dung index mong doi cho broad request

Ngay ca khi migration da chay, production van co the:

- chua `ANALYZE`
- chon sai plan
- van quet dataset lon hon mong doi
- chi cai thien tot voi request da thu hep `limit=12`

### 7.4 Van con timeout cap khoang 15 giay o mot layer trung gian

Co kha nang mot trong cac layer sau van cap timeout:

- upstream API
- reverse proxy
- frontend proxy route

Vi production timeout lap lai khoang `15s` o baseline lon, day van la dau hieu dang nghi.

### 7.5 Frontend/proxy van goi duong cu nang

Mac du code frontend local da duoc chuyen sang server-side pagination, production van co the:

- chua deploy dung ban frontend moi
- hoac van route vao duong API/proxy cu

## 8. Chu so huu van de

Neu chia trach nhiem:

- chinh: backend + database
- phu: deploy/proxy configuration
- khong phai chu so huu chinh: UI rendering

Neu noi thang:

- van de goc nam o nhanh code/backend/database ma toi da sua
- nhung production behavior cho thay viec fix **chua hoan thanh**

## 9. Viec can kiem tra ngay tren production

### 9.1 Xac nhan code dang chay

Can xac nhan production dang chay dung ban code moi cho:

- [app/repositories/review_repository.py](D:/AutoCode/DB/Review/app/repositories/review_repository.py)
- [app/services/review_query_service.py](D:/AutoCode/DB/Review/app/services/review_query_service.py)
- [app/api/routes/reviews.py](D:/AutoCode/DB/Review/app/api/routes/reviews.py)

### 9.2 Xac nhan migration da apply

Can kiem tra migration:

- [db/migrations/011_review_query_performance_indexes.sql](D:/AutoCode/DB/Review/db/migrations/011_review_query_performance_indexes.sql)

da duoc chay tren production DB chua.

Lenh can chay tren may Docker:

```powershell
docker exec -i hotel-review-postgres psql -U hotel_admin -d hotel_review_db < db\migrations\011_review_query_performance_indexes.sql
```

### 9.3 Kiem tra query plan that

Can chay `EXPLAIN ANALYZE` tren production DB cho it nhat 3 query:

- baseline request lon
- `platform_code=booking`
- `rating_min=10`

Neu co the, chay them:

- `rating_max=8`

de so sanh vi sao case nay con tra duoc trong khi `booking` va `rating_min=10` bi timeout.

Muc tieu:

- xac nhan co dung index moi hay khong
- xac nhan co scan qua nhieu row hay khong

### 9.4 Kiem tra timeout

Can kiem tra timeout cap o:

- app server
- reverse proxy
- frontend proxy
- cloud edge neu co

Vi neu query da cai thien nhung timeout van cap `15s`, production van bi 504.

### 9.5 Kiem tra frontend ban deploy

Can xac nhan frontend production da deploy ban co:

- server-side pagination moi
- khong con tu fetch full dataset qua nhieu page

## 10. Action items de fix dut diem

1. Xac nhan lai backend API production dang chay dung ban code toi uu moi nhat, khong phai ban cu.
2. Xac nhan migration index `011_review_query_performance_indexes.sql` da duoc apply that tren production DB.
3. Chay `ANALYZE` neu can de PostgreSQL cap nhat planner stats.
4. Chay `EXPLAIN ANALYZE` cho cac case timeout va so sanh voi case da cai thien.
5. Kiem tra timeout cap `15s` o proxy/app.
6. Xac nhan frontend/proxy production dang goi dung duong API moi va khong bi route nham vao behavior cu.
7. Retest production voi cac case:
   - `/api/v1/reviews?limit=200&offset=0`
   - `/api/v1/reviews?rating_min=10&limit=12&offset=0`
   - `/api/v1/reviews?platform_code=booking&limit=12&offset=0`
   - `/api/v1/reviews?rating_max=8&limit=12&offset=0`
   - `/api/v1/reviews?is_bad_review=true&limit=12&offset=0`

## 11. Short handoff note

```text
As of July 26, 2026, the fix appears partially improved but not fully complete. Targeted filtered review queries such as rating_min=10 and platform_code=booking now return successfully when the page size is small, but the broad baseline row-data request /api/v1/reviews?limit=200&offset=0 still times out around 15s. This suggests the backend/DB production path has improved for narrow requests, but the heavy baseline query path is still unresolved.
```

## 12. Trang thai thuc te can chot

Trang thai hien tai nen duoc danh dau:

- **Partially improved on production**
- **Targeted filtered queries improved**
- **Large baseline row-data request still open**
- **Retested after DB handoff: not fully stable yet**

Khong nen chot:

- fixed
- verified stable
- production ready

cho den khi 3 case nang o muc 5.1 deu qua duoc on dinh.
