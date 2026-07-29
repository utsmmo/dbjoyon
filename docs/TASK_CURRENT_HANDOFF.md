# Task Current Handoff

## Status

- Active hotel-list correction and admin rollout.
- As of `2026-07-29`, online hotel data da duoc chot lai theo danh sach moi.

## Scope

- Xoa danh sach hotel cu.
- Nhap danh sach hotel moi dung theo ten business da chot.
- Quan ly hotel va OTA links ngay tren website admin.
- Giu crawler chay dung voi rule `1 hotel + nhieu link cung platform`.

## Decision

- Danh sach dung hien tai la `9` hotel:
  - `Danang Beach`
  - `The Grace`
  - `Villa`
  - `Beachfront Hotel Hoi An`
  - `Sala Hoian Hotel`
  - `Old Town Hotel`
  - `Eco hoian Hotel`
  - `La Alba Villa`
  - `SLIVIN SG`
- Ten hotel noi bo do business cung cap la source of truth.
- Ten tren OTA khong duoc dung de override ten noi bo.
- Agoda links phai duoc clean ve canonical URL.
- `1 hotel + 1 platform` co the co nhieu links, nhung van map ve cung `hotel_id`.

## Owner Plan

- `DB`
  - verify manifest `8` hotel
  - verify `hotel_platform_accounts` luu duoc nhieu links cung platform
  - sau deploy, chay reset-import va verify tong hotel = `8`
- `BE`
  - deploy endpoint admin hotel CRUD
  - deploy endpoint `reset-import/default-manifest`
  - giu rule metadata:
    - `canonical_links`
    - `source_links`
- `FE`
  - dung `/review/admin` lam man quan ly hotel
  - cho phep xem, them, sua, xoa hotel
  - cho phep reset theo manifest
- `Tester`
  - check `/review/api/hotels?limit=200&offset=0`
  - check `/review/admin`
  - check danh sach sau reset-import co dung `8` hotel
- `DevOps`
  - deploy backend/frontend moi
  - restart service neu can

## Risks

- Code da xong local nhung online chua deploy thi web van hien data cu.
- Neu chay import khi online van dung code cu thi danh sach hotel se khong doi.
- Neu FE vao admin truoc khi BE deploy endpoint moi thi se thao tac that bai.

## Files

- `ops/codex/raon_hotel_import_manifest.json`
- `app/api/routes/system.py`
- `app/services/hotel_service.py`
- `app/repositories/hotel_repository.py`
- `web-hotel-review/frontend-web/app/admin/page.tsx`
- `web-hotel-review/frontend-web/components/admin-hotel-manager.tsx`
- `docs/DB_IMPORT_HANDOFF_2026-07-27.md`
- `docs/Crawl/ADMIN_CRAWLER_HOTEL_LINK_PLAN.md`

## Tests

1. Deploy backend/frontend moi.
2. Mo `http://localhost:3000/review/admin`.
3. Check `GET /review/api/hotels?limit=200&offset=0`.
4. Xac nhan danh sach tra ve dung `9` hotel business names.
