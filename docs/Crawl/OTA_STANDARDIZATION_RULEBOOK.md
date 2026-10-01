# OTA Standardization Rulebook

Tai lieu nay la bo rang buoc chuan cho tat ca OTA.
Muc tieu:

- khong map sai hotel
- khong post sai link
- khong tao trung review
- khong bi lech giua link hien thi va review trong DB
- khong de crawler tu "doan" hotel theo ten tren OTA

Base URL:

- `https://data.datac.click`

## 1. Nguyen tac tong

### 1.1 Nguon su that duy nhat

Nguon su that duy nhat cho crawler la:

- `GET /api/v1/hotels`

Crawler chi duoc tin:

- `hotel_id`
- `hotel_name`
- `metadata.source_links`
- `metadata.canonical_links`

Crawler khong duoc tin:

- ten hotel hien tren OTA
- slug OTA
- brand name tren OTA
- ten reviewer nhac den hotel nao

### 1.2 1 hotel business = 1 hotel_id

Rule bat buoc:

- `1 hotel trong he thong = 1 hotel_id`
- du 1 OTA co 1 link hay nhieu link, van chi la 1 `hotel_id`

Vi du dung:

- `Villa` co 3 link Booking
- ca 3 link deu crawl ve cung `hotel_id` cua `Villa`

Vi du sai:

- thay 3 link Booking roi tao 3 hotel
- thay ten Booking khac ten noi bo roi tao hotel moi

### 1.3 1 link OTA = 1 source da dang ky

Moi link OTA duoc xem la 1 source da dang ky san trong hotel metadata.

Crawler chi duoc crawl va post theo:

- `metadata.source_links.<platform_code>[]`

Neu link crawler dang cam khong nam trong danh sach nay:

- khong duoc post
- phai report lai Admin / DB / BE

## 2. Rule canonical link theo tung OTA

### 2.1 Agoda

Canonical Agoda link chi duoc giu:

- `scheme + host + path`

Phai bo:

- query params nhu `adults`, `rooms`, `checkIn`, `los`
- UTM
- tracking params

Vi du sai:

- `https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html?adults=2&rooms=1&checkIn=2026-08-24&los=2`

Vi du dung:

- `https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html`

Rang buoc bo sung:

- khong duoc coi `https://www.agoda.com/raon-hoian-gardenview/hotel/hoi-an-vn.html`
  va `https://www.agoda.com/vi-vn/raon-hoian-gardenview/hotel/hoi-an-vn.html`
  la 2 hotel khac nhau
- neu he thong dang ky link canonical co `/vi-vn/` thi crawler phai normalize ve dung bien the do truoc khi post

### 2.2 Booking

Booking cho phep:

- nhieu link cung 1 hotel
- moi link la 1 source Booking hop le cua cung `hotel_id`

Rule:

- khong duoc tao hotel moi neu Booking co nhieu share link
- `source_link_used` phai la link Booking da dang ky trong `source_links.booking[]`

### 2.3 Ctrip

Rule:

- link Ctrip phai map ve dung `hotel_id` da dang ky
- khong duoc map theo ten hotel hien thi trong app Ctrip
- neu payload co `commentRating`, categories phai gan cho dung review / dung hotel

### 2.4 Expedia

Rule:

- Expedia link phai dung link da dang ky trong `source_links.expedia[]`
- khong duoc doi slug Expedia de doan ra hotel khac

### 2.5 Google

Rule:

- Google phai dung dung place URL / map URL da dang ky
- khong duoc tim theo keyword ten hotel roi post vao `hotel_id` gan dung

### 2.6 Tripadvisor va OTA khac

Ap dung cung 1 rule:

- chi crawl theo link da dang ky
- chi post vao `hotel_id` da dang ky
- khong suy luan hotel theo ten

## 3. Flow chuan cho moi OTA

1. Goi `GET /api/v1/hotels?limit=200&offset=0`
2. Lay danh sach hotel
3. Voi moi hotel:
   - lay `hotel_id`
   - lay `source_links.<platform_code>[]`
   - lay `canonical_links.<platform_code>` neu co
4. Normalize link crawl ve dang canonical
5. So sanh link dang crawl voi danh sach link da dang ky
6. Chi khi match moi duoc crawl / post
7. Crawl review
8. Dedupe theo `external_review_id`
9. Post vao `POST /api/v1/sync/reviews/{platform_code}`
10. Verify bang `GET /api/v1/reviews/stats`

## 4. Rang buoc bat buoc truoc khi post

### 4.1 Bat buoc phai co

- `hotel_id`
- `platform_code`
- `source_link_used`
- `reviews[].external_review_id`
- `reviews[].reviewed_at`
- `reviews[].reviewer_country_code`
- `reviews[].raw_payload`

### 4.2 Khong duoc post neu

- khong resolve duoc `hotel_id`
- `source_link_used` khong nam trong danh sach link da dang ky cua hotel do
- thieu `reviewer_country_code`
- `reviewer_country_code` khong phai ma quoc gia 2 ky tu
- `external_review_id` rong
- `reviewed_at` rong

### 4.3 `hotel_platform_account_id`

Rule:

- crawler khong bat buoc gui `hotel_platform_account_id`
- neu khong chac UUID dung, de `null`
- backend uu tien resolve bang `source_link_used`

Day la field de gay fail nhat neu mapping sai.

## 5. Dedupe va upsert

### 5.1 Review unique key

Review duoc coi la 1 ban ghi duy nhat theo:

- `hotel_id`
- `platform_id`
- `external_review_id`

### 5.2 Crawler van phai tu dedupe

Du DB co unique key, crawler van phai dedupe truoc khi post de:

- giam payload
- giam nguy co timeout
- giam ghi de lap lai

### 5.3 Truong hop 1 hotel co nhieu link cung 1 OTA

Neu 2 link cung tra ve cung 1 review:

- van phai post ve cung `hotel_id`
- va dedupe theo `external_review_id`

Khong duoc:

- nhan ban review vi do la 2 link

## 6. Cac case sai thuong gap

### Case A: Map theo ten OTA

Sai:

- crawler thay ten hotel tren Agoda khac ten noi bo
- tu tao hoac tu chon `hotel_id` khac

Dung:

- bo qua ten OTA
- chi dung link da dang ky + `hotel_id` da co

### Case B: Link khong canonical

Sai:

- crawler lay 1 link Agoda co query params
- backend dang ky 1 link Agoda khong query params
- post vao xong bi lech account hoac khong xoa duoc theo link

Dung:

- normalize link truoc khi crawl
- normalize lai truoc khi post

### Case C: 1 link sai, review vao sai hotel

Sai:

- link Agoda cua hotel A dang bi dang ky nham sang hotel B
- crawler van post vao B

Dung:

- dung crawl
- report lai de Admin / DB sua link truoc

### Case D: Web khong tim thay review dung nhu thuc te

Dau hieu:

- trong dashboard thay tong review co
- nhung search review that lai khong ra dung hotel / dung link

Nguyen nhan thuong la:

- crawl dung review nhung sai hotel
- crawl dung hotel nhung sai `source_link_used`
- link bi bien the sai canonical

## 7. Rule verify sau moi batch

Sau khi post xong moi hotel + OTA, crawler phai verify:

### 7.1 Check stats

`GET /api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=<platform_code>`

### 7.2 Check sample

`GET /api/v1/reviews?hotel_id=<hotel_id>&platform_code=<platform_code>&limit=20&offset=0`

### 7.3 Check source link consistency

Crawler phai tu doi chieu:

- link dang crawl
- link da dang ky
- `source_link_used` vua post

Neu 3 cai nay khong giong nhau sau normalize:

- batch do xem nhu fail

## 8. Rule xoa du lieu sai

### 8.1 Xoa theo hotel + OTA

Dung khi can xoa sach 1 OTA cua 1 hotel:

`DELETE /api/v1/reviews?hotel_id=<hotel_id>&platform_code=<platform_code>`

### 8.2 Xoa theo review_id

Dung khi can xoa 1 dong test:

`DELETE /api/v1/reviews?review_id=<review_id>`

### 8.3 Khong duoc xoa tu dong trong crawl hằng ngay

Crawler chi duoc xoa khi co lenh ro rang tu:

- Admin
- DB
- Leader

## 9. Log bat buoc cho moi batch crawl

Moi batch phai log:

- `hotel_id`
- `hotel_name`
- `platform_code`
- `source_link_used`
- `canonical_link_after_normalize`
- `total_reviews_fetched`
- `total_reviews_after_dedupe`
- `total_reviews_posted`
- `failed_review_ids`
- `first_external_review_id`
- `last_external_review_id`

Neu batch fail, phai log them:

- vi sao fail
- link dang dung
- hotel_id dang map
- payload mau bi fail

## 10. Contract bat buoc giua crawler va backend

Backend co quyen tu choi batch neu:

- `source_link_used` khong thuoc hotel do
- thieu country code
- sai platform code
- sai hotel_id

Crawler co nghia vu:

- khong retry mu quang 1 payload sai mapping
- report lai nguon sai
- khong tu sua DB

## 11. Checklist ban giao cho tat ca OTA

Truoc khi chay bat ky OTA nao, doi crawl phai tick du:

1. Da lay `hotel_id` tu `GET /api/v1/hotels`
2. Da lay link tu `metadata.source_links`
3. Da normalize link ve dang canonical
4. Da xac nhan link sau normalize ton tai trong source list
5. Da chon dung `platform_code`
6. Da co `external_review_id`
7. Da co `reviewed_at`
8. Da co `reviewer_country_code`
9. Da dedupe trong batch
10. Da biet cach verify bang `stats` va `reviews`

Neu thieu bat ky muc nao:

- khong duoc post

## 12. Ket luan cho doi crawl

Rule quan trong nhat:

- khong map theo ten
- khong tao hotel moi
- khong tu sua DB
- khong post neu link chua duoc dang ky
- khong post neu chua normalize link
- khong post neu thieu country code

Neu khong chac:

- dung batch
- report lai

