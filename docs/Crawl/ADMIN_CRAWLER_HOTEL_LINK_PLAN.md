# Admin + Crawler Hotel Link Plan

Tai lieu nay la ke hoach chuan de:

- `Admin` xem, sua, xoa link OTA cua tung hotel
- `BE/DB` giu du lieu link dung va nhat quan
- `Crawler` lay dung link chuan de crawl review
- tranh viec moi ben tu hieu mot kieu

Ap dung cho project hien tai tai:

- `https://data.datac.click`
- man admin local/web: `http://localhost:3000/review/admin`

## 1. Muc tieu chung

Can dat 3 dieu:

1. Danh sach hotel noi bo la source of truth.
2. Moi hotel co the co nhieu OTA va moi OTA co the co nhieu link.
3. Crawler khong tu sinh hotel, khong tu sua ten hotel, chi doc link chuan va day review ve dung `hotel_id`.

## 2. Nguyen tac du lieu

### 2.1 Source of truth

- `hotel_name` la ten noi bo do business cung cap.
- ten tren Booking/Agoda/Google khong duoc override `hotel_name`.
- link OTA la du lieu ky thuat de crawl, khong phai ten nghiep vu.

### 2.2 Rule 1 hotel nhieu link

- `1 hotel + 1 platform` duoc phep co `nhieu link`.
- tat ca link do van map ve cung `1 hotel_id`.
- khong tao them hotel moi chi vi khac link hoac khac ten tren OTA.

### 2.3 Rule clean link

- link luu trong he thong phai la link dung de crawl.
- voi Agoda uu tien link canonical:
  - giu `scheme + host + path`
  - bo query params nhu `adults`, `rooms`, `checkIn`, `los`
- cac platform khac cung uu tien link gon, on dinh, it param track.

## 3. Muc tieu cua man admin

Man `Admin Hotel Manager` can hoan thanh dung 4 viec:

1. Xem tat ca hotel dang co.
2. Xem link OTA hien dang map voi tung hotel.
3. Sua, them, xoa hotel.
4. Sua, them, xoa link OTA cua hotel.

Muc tieu nghiep vu:

- nguoi van hanh vao admin la biet ngay hotel nao dang co link nao
- crawler chi can doc lai danh sach nay la crawl duoc

## 4. API can dung cho admin

### 4.1 API lay danh sach hotel va link

Dung:

- `GET /api/v1/hotels?limit=200&offset=0`

Y nghia:

- tra ve danh sach hotel
- tra ve `metadata.source_links`
- tra ve `metadata.canonical_links`

Day la API de FE admin hien link hien tai.

Response can duoc FE doc theo quy uoc:

```json
{
  "items": [
    {
      "id": "hotel-uuid",
      "hotel_code": "villa",
      "hotel_name": "Villa",
      "metadata": {
        "source_links": {
          "booking": [
            "https://www.booking.com/Share-H39M2G"
          ],
          "agoda": [
            "https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html"
          ]
        },
        "canonical_links": {
          "booking": "https://www.booking.com/Share-H39M2G",
          "agoda": "https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html"
        }
      }
    }
  ]
}
```

### 4.2 API tao hotel moi

- `POST /api/v1/system/hotels`

Dung khi:

- them hotel moi
- them hotel moi chua co link OTA

### 4.3 API cap nhat hotel va link

- `PUT /api/v1/system/hotels/{hotel_id}`

Dung khi:

- sua ten noi bo
- sua `hotel_code`
- them link moi
- xoa link cu
- thay doi toan bo danh sach link cua 1 hotel

### 4.4 API xoa hotel

- `DELETE /api/v1/system/hotels/{hotel_id}`

Dung khi:

- hotel tao sai
- hotel khong con dung

Luu y:

- xoa hotel la thao tac nghiep vu lon
- nen co confirm tren admin

## 5. Ke hoach FE admin

### 5.1 Man hinh can co

Trang:

- `/review/admin`

Can hien:

- danh sach hotel
- so luong hotel
- link theo tung OTA
- nut `Edit`
- nut `Delete`
- form `Add / Update hotel`

### 5.2 UX toi thieu

Moi hotel card can hien:

- `hotel_name`
- `hotel_code`
- `city`
- `status`
- block link theo tung OTA

Moi OTA:

- moi link 1 dong
- neu khong co thi hien `No link`

### 5.3 Form sua hotel

Form can cho:

- sua `hotel_code`
- sua `hotel_name`
- sua `city`
- sua `country_code`
- sua `status`
- nhap nhieu link cho moi OTA, `one link per line`

### 5.4 Validation FE

FE nen chan som:

- `hotel_code` khong duoc rong
- `hotel_name` khong duoc rong
- bo dong trong trong textarea link
- trim khoang trang dau/cuoi

Neu sau nay muon tot hon:

- validate link bat dau bang `http://` hoac `https://`
- canh bao Agoda link con query params

## 6. Ke hoach BE

### 6.1 Tra link ra de FE doc

BE phai dam bao `GET /api/v1/hotels` tra du:

- `metadata.source_links`
- `metadata.canonical_links`

Do day la hop dong de admin va crawler doc link chuan.

### 6.2 Giu rule normalize link

Khi tao/sua hotel qua API system:

- doc `links`
- normalize bang service link
- luu vao:
  - `metadata.source_links`
  - `metadata.canonical_links`
- tao lai `hotel_platform_accounts` theo tung link

### 6.3 Rule update

Khi `PUT /system/hotels/{hotel_id}`:

- xem payload moi la source of truth moi
- xoa mapping account cu cua hotel do
- tao lai mapping theo danh sach link moi

Dieu nay giup:

- admin xoa link nao thi DB het link do
- admin them link nao thi DB co them link do

### 6.4 Rule response loi

BE nen tra loi ro:

- hotel khong ton tai
- `hotel_code` bi trung
- payload sai dinh dang
- purge/reset that bai

De FE va crawler biet huong xu ly.

## 7. Ke hoach DB

### 7.1 DB la noi chot dung sai

DB can dam bao:

- 1 hotel co 1 `hotel_id`
- 1 platform co nhieu link van map dung ve hotel do
- khong duplicate hotel chi vi link khac nhau

### 7.2 Dinh huong luu tru

Hotel can giu:

- `hotel_name`
- `hotel_code`
- `metadata.source_links`
- `metadata.canonical_links`

Bang mapping platform can giu:

- moi link la 1 account record hoac 1 source record ro rang
- deu tro ve cung `hotel_id`

### 7.3 Checklist DB sau moi lan admin sua

DB can verify:

1. hotel van ton tai dung `hotel_id`
2. so luong link tren DB khop so luong link admin vua luu
3. link Agoda da duoc clean
4. khong con link cu neu admin da xoa

## 8. Ke hoach cho doi crawler

## 8.1 Crawler dung file nao

Doi crawler can doc:

- `docs/Crawl/POST_REVIEW_GUIDE.md`
- `docs/Crawl/ADMIN_CRAWLER_HOTEL_LINK_PLAN.md`
- `docs/Crawl/CRAWLER_OTA_ENDPOINT_MATRIX.md`
- `docs/API_ENDPOINTS.md`

## 8.2 Crawler duoc dung API nao

Crawler chi duoc dung:

- `GET /api/v1/hotels?limit=200&offset=0`
- `GET /api/v1/reviews/stats?hotel_id=...&platform_code=...`
- `POST /api/v1/sync/reviews/{platform_code}`
- `GET /api/v1/reviews/bad/unnotified`
- `POST /api/v1/notifications/deliveries`

Crawler khong duoc dung:

- `POST /api/v1/system/hotels/purge`
- `POST /api/v1/system/hotels/reset-import`
- `POST /api/v1/system/hotels/reset-import/default-manifest`
- `PUT /api/v1/system/hotels/{hotel_id}`
- `DELETE /api/v1/system/hotels/{hotel_id}`

## 8.3 Flow crawler dung

Flow dung cho moi platform:

1. goi `GET /api/v1/hotels?limit=200&offset=0`
2. lay danh sach hotel
3. doc `metadata.source_links[platform_code]`
4. neu hotel khong co link cua platform do:
   - bo qua hotel do
5. neu co nhieu link:
   - crawl tung link
   - nhung van post ve cung `hotel_id`
6. goi `GET /api/v1/reviews/stats?hotel_id=...&platform_code=...`
7. so sanh tong review tren OTA voi DB
8. crawl phan chenh hoac crawl moi nhat
9. goi `POST /api/v1/sync/reviews/{platform_code}`

Platform uu tien hien tai:

- `booking`
- `agoda`
- `google`

## 8.4 Payload crawler phai ton trong

Crawler phai:

- gui dung `hotel_id`
- giu `external_review_id`
- gui `raw_payload`
- khong doi `hotel_name`
- khong tu tao hotel moi neu business chua tao san

## 8.5 Neu thay link sai thi lam gi

Crawler khong tu sua DB.

Crawler phai report ve:

- hotel nao sai
- platform nao sai
- link nao hong
- de `Admin` hoac `BE/DB` sua tren admin

## 9. Phan quyen trach nhiem

### `Leader`

- chot rule
- dieu phoi giua FE, BE, DB, Tester, Crawler
- giu 1 luong tai lieu duy nhat

### `FE`

- lam man admin de xem/sua/xoa link
- hien loi ro rang
- hien link hien tai dung metadata API

### `BE`

- giu contract API
- normalize link
- luu metadata + mapping dung

### `DB`

- verify record sau khi sua
- clean data sai neu co
- dam bao khong duplicate mapping

### `Tester`

- test tao hotel
- test sua link
- test xoa link
- test xoa hotel
- test reset manifest
- test `GET /api/v1/hotels` tra dung link sau khi sua

### `Crawler`

- chi doc link chuan
- chi post review
- report link sai

## 10. Checklist test nghiep vu

Tester can chay toi thieu:

1. Mo `/review/admin`
2. Check tong so hotel dang dung
3. Chon 1 hotel co link Agoda
4. Sua Agoda link co query params
5. Save
6. Goi lai `GET /api/v1/hotels`
7. Xac nhan `metadata.source_links.agoda` da duoc clean
8. Them 2 link Booking cho cung 1 hotel
9. Save
10. Goi lai `GET /api/v1/hotels`
11. Xac nhan hotel do van la 1 `hotel_id`
12. Xac nhan mang `source_links.booking` co 2 link
13. Xoa 1 link
14. Save
15. Goi lai API
16. Xac nhan link da mat khoi response

## 11. Danh sach hotel hien tai

Tinh den `2026-07-29`, danh sach business name dang chot la `9` hotel:

- `Danang Beach`
- `The Grace`
- `Villa`
- `Beachfront Hotel Hoi An`
- `Sala Hoian Hotel`
- `Old Town Hotel`
- `Eco hoian Hotel`
- `La Alba Villa`
- `SLIVIN SG`

## 12. Chot huong van hanh

Tu bay gio:

- `Admin` la noi sua ten hotel va link
- `GET /api/v1/hotels` la noi FE + crawler doc danh sach link chuan
- `Crawler` khong sua hotel, chi dung `hotel_id` + link chuan de crawl
- neu thay sai, report ve admin/BE/DB de sua nguon

Neu can endpoint va payload chi tiet cho sync review, xem them:

- [POST_REVIEW_GUIDE.md](D:/AutoCode/DB/Review/docs/Crawl/POST_REVIEW_GUIDE.md)
