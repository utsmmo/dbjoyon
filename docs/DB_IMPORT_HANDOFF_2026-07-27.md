# DB Import Handoff 2026-07-27

## Trang thai

- Chua the xoa cung du lieu online bang API hien tai.
- Co the tiep tuc import ngay sau khi co:
  - quyen truy cap DB online
  - hoac endpoint admin de xoa `hotels` va `reviews`

## Kiem tra da lam

- Da doc Swagger online tai `https://data.datac.click/docs`
- Da doc OpenAPI online tai `https://data.datac.click/openapi.json`
- Xac nhan API online hien tai chi co:
  - `GET /api/v1/hotels`
  - `POST /api/v1/hotels`
  - `POST /api/v1/sync/reviews/{platform_code}`
  - cac endpoint query/analytics/notify
- Khong co:
  - `DELETE /api/v1/hotels`
  - `DELETE /api/v1/reviews`
  - endpoint purge/reset admin

## Du lieu hien tai tren online

Ngay kiem tra: `2026-07-27`

- Hotel hien co tren API online: `10`
- Danh sach moi can import: `8`

Nhan xet:

- Data online hien tai khong khop bo hotel moi.
- Neu import chong len truoc khi xoa, he thong se roi hon.

## Danh sach hotel moi can import

Nguon: `C:\Users\Admin\Downloads\Link OTA RAON.xlsx`

1. `Danang Beach`
2. `The Grace`
3. `Villa`
4. `Beachfront Hotel Hoi An`
5. `Sala Hoian Hotel`
6. `Old Town Hotel`
7. `Eco hoian Hotel`
8. `La Alba Villa`

## File manifest da chuan bi

- `ops/codex/raon_hotel_import_manifest.json`

File nay da gom:

- ten hotel
- link theo tung nen tang
- cho phep DB/Crawler dung lai sau khi reset data online

## Rule lam sach link

- Agoda:
  - chi giu `scheme + host + path`
  - bo toan bo query string nhu `checkIn`, `los`, `searchrequestid`, `ds`
- Booking / Traveloka / Expedia / Ctrip:
  - tam thoi giu nguyen link nguon neu la short link
  - neu sau nay crawler resolve duoc canonical URL thi moi thay the

Vi du:

- sai:
  - `https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html?adults=2&rooms=1&checkIn=2026-08-24&los=2`
- dung:
  - `https://www.agoda.com/vi-vn/ania-private-pool-villas-collection/hotel/da-nang-vn.html`

## Rule 1 hotel co nhieu link cung platform

- Khong tao nhieu `hotel` cho cung mot khach san.
- `1 hotel + 1 platform` co the co `nhieu link nguon`.
- DB nen luu theo 1 trong 2 cach:
  - uu tien: 1 dong `hotel_platform_accounts` cho moi link
  - toi thieu: 1 `canonical_link` + mang `source_links[]` trong metadata

Quy tac dedupe link:

- Agoda: dedupe tren canonical URL da clean
- Booking short links: dedupe tren URL string sau khi trim

Quy tac nghiep vu:

- nhieu link Booking cua cung 1 hotel van phai map ve cung `hotel_id`
- review sync van dedupe bang:
  - `hotel_id`
  - `platform_id`
  - `external_review_id`
- tuyet doi khong de moi link Booking sinh ra mot hotel moi

## Hanh dong DB can lam tiep

1. Xoa cung toan bo review sai
2. Xoa cung toan bo hotel sai
3. Tao ho tro xoa an toan o tang DB/BE neu he thong online chua co
4. Import lai 8 hotel tu manifest
5. Luu link theo rule canonical + source_links
6. Neu 1 hotel co nhieu link cung platform, map chung 1 hotel
7. Verify lai bang:
   - `GET /api/v1/hotels?limit=200&offset=0`
   - tong hotel phai = `8`
8. Sau do moi ban giao cho doi crawl sync review moi

## Endpoint moi cho DB/BE

- `POST /api/v1/system/hotels/purge`
- `POST /api/v1/system/hotels/reset-import`

Payload toi thieu de reset import:

```json
{
  "confirm_purge": true,
  "hotels": []
}
```

Script van hanh da them:

- `python ops/codex/reset_import_hotels.py --base-url http://localhost:13000`

## Blocker

- Blocker hien tai la thieu quyen xoa online.
- Main agent khong nen import chong len khi chua reset, vi se tang duplicate va mapping sai.
