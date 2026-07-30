# Crawler OTA Endpoint Matrix

Tai lieu nay de gui truc tiep cho doi crawl.
Ban nay uu tien goc nhin "lay link dung va post dung".

Muc tieu:

- biet lay link hotel theo tung OTA
- biet lay link cua tat ca hotel hoac 1 hotel cu the
- biet endpoint nao de doc, endpoint nao de upload review
- biet file nao phai doc truoc khi code crawler

Base URL:

- `https://data.datac.click`

Swagger:

- `https://data.datac.click/docs`

## 1. Bo file doi crawl phai doc

Thu tu uu tien:

1. `docs/Crawl/CRAWLER_OTA_ENDPOINT_MATRIX.md`
2. `docs/Crawl/POST_REVIEW_GUIDE.md`
3. `docs/Crawl/ADMIN_CRAWLER_HOTEL_LINK_PLAN.md`
4. `docs/API_ENDPOINTS.md`

## 2. Nguyen tac lam viec voi hotel links

- Danh sach hotel chuan duoc doc tu `GET /api/v1/hotels`
- Link OTA nam trong:
  - `metadata.source_links`
  - `metadata.canonical_links`
- `hotel_name` la ten business noi bo
- crawler khong tu sua ten hotel
- crawler khong tu sua link hotel
- neu link sai, crawler report lai cho admin
- 1 hotel co nhieu link cung 1 OTA van chi la `1 hotel_id`
- crawler duoc crawl nhieu link, nhung khong duoc tao nhieu hotel

## 3. Endpoint goc de lay danh sach hotel va links

### 3.1 Lay tat ca hotel

```http
GET /api/v1/hotels?limit=200&offset=0
```

Vi du:

```bash
curl "https://data.datac.click/api/v1/hotels?limit=200&offset=0"
```

Dung de:

- lay toan bo hotel
- lay toan bo links cua tat ca OTA
- tach rieng danh sach Booking / Agoda / Google o phia crawler

### 3.2 Lay 1 hotel theo ten

Hien tai khong co endpoint `GET /api/v1/hotels/{hotel_id}` rieng.

Dung tam:

```http
GET /api/v1/hotels?q=<keyword>&limit=200&offset=0
```

Vi du:

```bash
curl "https://data.datac.click/api/v1/hotels?q=Villa&limit=200&offset=0"
```

Hoac:

- goi full list
- loc lai theo `hotel_id` hoac `hotel_code` trong crawler

Khuyen nghi cho doi crawl:

- moi lan sync, goi full list 1 lan
- cache theo `hotel_id`
- sau do tach rieng theo OTA
- khong map theo ten OTA, uu tien map theo `hotel_id`

## 4. Matrix endpoint theo tung OTA

## 4.1 Booking

### Lay tat ca Booking links

Dung:

- `GET /api/v1/hotels?limit=200&offset=0`

Crawler doc:

- `items[].id`
- `items[].hotel_code`
- `items[].hotel_name`
- `items[].metadata.source_links.booking`
- `items[].metadata.canonical_links.booking`

Y nghia:

- neu `source_links.booking` co du lieu thi hotel do can crawl Booking
- neu co nhieu link thi crawl tung link, nhung van post cung `hotel_id`
- neu 2 link Booking cung thuoc 1 hotel thi khong tao hotel moi

### Lay Booking links cua 1 hotel

Dung:

- `GET /api/v1/hotels?q=<hotel_name_or_code>&limit=200&offset=0`

Sau do doc:

- `metadata.source_links.booking`

### Check tong review Booking dang co trong DB

```http
GET /api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=booking
```

### Upload review Booking

```http
POST /api/v1/sync/reviews/booking
```

## 4.2 Agoda

### Lay tat ca Agoda links

Dung:

- `GET /api/v1/hotels?limit=200&offset=0`

Crawler doc:

- `items[].metadata.source_links.agoda`
- `items[].metadata.canonical_links.agoda`

Rule quan trong:

- Agoda link trong he thong da duoc clean ve canonical URL
- khong duoc tu them query params khi so sanh link
- neu crawler lay duoc link Agoda co query params, phai clean truoc khi so sanh / log

### Lay Agoda links cua 1 hotel

Dung:

- `GET /api/v1/hotels?q=<hotel_name_or_code>&limit=200&offset=0`

Sau do doc:

- `metadata.source_links.agoda`

### Check tong review Agoda dang co trong DB

```http
GET /api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=agoda
```

### Upload review Agoda

```http
POST /api/v1/sync/reviews/agoda
```

## 4.3 Google

### Lay tat ca Google links

Dung:

- `GET /api/v1/hotels?limit=200&offset=0`

Crawler doc:

- `items[].metadata.source_links.google`
- `items[].metadata.canonical_links.google`

### Lay Google links cua 1 hotel

Dung:

- `GET /api/v1/hotels?q=<hotel_name_or_code>&limit=200&offset=0`

Sau do doc:

- `metadata.source_links.google`

### Check tong review Google dang co trong DB

```http
GET /api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=google
```

### Upload review Google

```http
POST /api/v1/sync/reviews/google
```

## 4.4 Cac OTA khac dang co trong link admin

He thong hien tai dang cho luu them:

- `traveloka`
- `expedia`
- `ctrip`

`ctrip` hien tai da co the post review qua:

- `POST /api/v1/sync/reviews/ctrip`

`expedia` hien tai da co the post review qua:

- `POST /api/v1/sync/reviews/expedia`

Neu sau nay co luong crawl cho cac nen tang nay thi van dung:

- `GET /api/v1/hotels?limit=200&offset=0`

de lay link.

Tuy nhien upload review hien tai can theo platform da backend support.

## 5. Cach tach link theo OTA o phia crawler

Sau khi goi:

```http
GET /api/v1/hotels?limit=200&offset=0
```

Crawler tach nhu sau:

### 5.1 Booking list

```json
[
  {
    "hotel_id": "uuid",
    "hotel_code": "villa",
    "hotel_name": "Villa",
    "links": [
      "https://www.booking.com/Share-H39M2G"
    ]
  }
]
```

Lay tu:

- `item.id`
- `item.hotel_code`
- `item.hotel_name`
- `item.metadata.source_links.booking`

Rule:

- `links` co the co 1 hoac nhieu phan tu
- du co nhieu link, van chi dung 1 `hotel_id`

### 5.2 Agoda list

```json
[
  {
    "hotel_id": "uuid",
    "hotel_code": "villa",
    "hotel_name": "Villa",
    "links": [
      "https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html"
    ]
  }
]
```

Lay tu:

- `item.metadata.source_links.agoda`

Rule:

- so sanh link Agoda theo canonical URL
- bo toan bo query params phu

### 5.3 Google list

```json
[
  {
    "hotel_id": "uuid",
    "hotel_code": "villa",
    "hotel_name": "Villa",
    "links": [
      "https://maps.google.com/..."
    ]
  }
]
```

Lay tu:

- `item.metadata.source_links.google`

## 6. Flow chuan cho doi crawl

1. Goi `GET /api/v1/hotels?limit=200&offset=0`
2. Tach danh sach theo OTA:
   - booking
   - agoda
   - google
3. Voi moi hotel trong tung OTA:
   - lay `hotel_id`
   - lay danh sach links
4. Goi `GET /api/v1/reviews/stats?hotel_id=...&platform_code=...`
5. So sanh tong review tren OTA voi tong review trong DB
6. Crawl phan chenh hoac crawl review moi nhat
7. Goi `POST /api/v1/sync/reviews/{platform_code}`
8. Neu co bad review can notify:
   - goi `GET /api/v1/reviews/bad/unnotified`
   - goi `POST /api/v1/notifications/deliveries`

## 7. Endpoint can gui cho doi crawl

Day la bo endpoint toi thieu can gui:

- `GET https://data.datac.click/api/v1/hotels?limit=200&offset=0`
- `GET https://data.datac.click/api/v1/hotels?q=<hotel_name_or_code>&limit=200&offset=0`
- `GET https://data.datac.click/api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=booking`
- `GET https://data.datac.click/api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=agoda`
- `GET https://data.datac.click/api/v1/reviews/stats?hotel_id=<hotel_id>&platform_code=google`
- `POST https://data.datac.click/api/v1/sync/reviews/booking`
- `POST https://data.datac.click/api/v1/sync/reviews/agoda`
- `POST https://data.datac.click/api/v1/sync/reviews/google`

## 8. Endpoint khong duoc dung

Doi crawl khong duoc goi:

- `POST /api/v1/system/hotels`
- `PUT /api/v1/system/hotels/{hotel_id}`
- `DELETE /api/v1/system/hotels/{hotel_id}`
- `POST /api/v1/system/hotels/purge`
- `POST /api/v1/system/hotels/reset-import`
- `POST /api/v1/system/hotels/reset-import/default-manifest`

## 9. Mau script doc links

Pseudo-code:

```js
const hotels = await fetch("https://data.datac.click/api/v1/hotels?limit=200&offset=0").then(r => r.json());

const bookingHotels = hotels.items
  .filter(h => h.metadata?.source_links?.booking?.length)
  .map(h => ({
    hotel_id: h.id,
    hotel_code: h.hotel_code,
    hotel_name: h.hotel_name,
    links: h.metadata.source_links.booking,
  }));

const agodaHotels = hotels.items
  .filter(h => h.metadata?.source_links?.agoda?.length)
  .map(h => ({
    hotel_id: h.id,
    hotel_code: h.hotel_code,
    hotel_name: h.hotel_name,
    links: h.metadata.source_links.agoda,
  }));

const googleHotels = hotels.items
  .filter(h => h.metadata?.source_links?.google?.length)
  .map(h => ({
    hotel_id: h.id,
    hotel_code: h.hotel_code,
    hotel_name: h.hotel_name,
    links: h.metadata.source_links.google,
  }));
```

## 10. Chot huong van hanh

- `GET /api/v1/hotels` la endpoint goc de lay links cua tat ca OTA
- khong co endpoint tach rieng Booking/Agoda/Google tu backend o thoi diem hien tai
- doi crawl phai tu tach theo `metadata.source_links.<platform>`
- nhu vay se don gian hon, it route hon, va giu 1 nguon su that duy nhat

Neu sau nay can toi uu hon, co the bo sung them endpoint moi:

- `GET /api/v1/hotels/links/booking`
- `GET /api/v1/hotels/links/agoda`
- `GET /api/v1/hotels/links/google`

Nhung hien tai chua can, vi `GET /api/v1/hotels` da du dung cho crawler.
