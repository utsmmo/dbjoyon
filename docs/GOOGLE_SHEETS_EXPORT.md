# Dong Bo Review Tu Database Sang Google Sheets

## Muc tieu

- PostgreSQL van la source of truth
- Google Sheets chi la lop hien thi
- Moi khach san la 1 sheet/tab
- Header co dinh:

```text
hotel_name	reviewed_at	reviewer_name	reviewer_country_code	rating	is_bad_review	translated_title_vi	translated_text_vi
```

## Bien moi truong can set

Them vao file `.env`:

```env
GOOGLE_SHEETS_SPREADSHEET_ID=18PzGrAOQIKFPv9mhcY_9fBL6t2EbyIuRpc8_tcFb8Rc
GOOGLE_OAUTH_CLIENT_ID=300601645125-1hjkhqkgsps6o6475aoqusvcp68fo2nr.apps.googleusercontent.com
GOOGLE_OAUTH_CLIENT_SECRET=your_client_secret
GOOGLE_OAUTH_REFRESH_TOKEN=your_refresh_token
```

Sau do rebuild lai:

```bash
docker compose up -d --build
```

## Endpoint export

```http
POST /api/v1/exports/google-sheets/reviews
```

## Payload mau

### Export tat ca hotel active va dang bat sync

```json
{
  "replace_sheet": true,
  "only_active_hotels": true,
  "only_enabled_hotels": true
}
```

### Export mot so hotel cu the

```json
{
  "hotel_ids": [
    "155ced91-f79c-4ddc-b498-0399858aebf4",
    "918f2940-65e2-4b10-a621-970b9d60aeee"
  ],
  "replace_sheet": true
}
```

### Override spreadsheet id neu can

```json
{
  "spreadsheet_id": "18PzGrAOQIKFPv9mhcY_9fBL6t2EbyIuRpc8_tcFb8Rc",
  "hotel_ids": [],
  "replace_sheet": true
}
```

## Curl mau

```bash
curl -X POST "https://data.datac.click/api/v1/exports/google-sheets/reviews" \
  -H "Content-Type: application/json" \
  -d '{
    "replace_sheet": true,
    "only_active_hotels": true,
    "only_enabled_hotels": true
  }'
```

## Cach chon hotel nao duoc sync

Mac dinh he thong se doc `metadata` cua hotel:

- `google_sheet_sync_enabled = true` -> duoc sync
- `google_sheet_sync_enabled = false` -> bo qua
- `sheet_tab_name` -> ten tab trong Google Sheet

Vi du metadata:

```json
{
  "google_sheet_sync_enabled": true,
  "sheet_tab_name": "The Grace An Thuong"
}
```

Neu metadata khong co `sheet_tab_name`, he thong mac dinh dung `hotel_name`.

Hien tai code da co map mac dinh cho 7 hotel dang co trong he thong:

- `ania_airport_residences_next_to_holiday_inn` -> `Ania Airport Residences`
- `luxury_private_pool_villas_village_danang_resort` -> `Luxury Pool Villas Danang`
- `republic_airport_residences` -> `Republic Airport Residences`
- `resort_pool_villa_beach_access_premier_village_dan` -> `Premier Village Beach Access`
- `resort_private_pool_villa_premier_village_danang` -> `Premier Village Private Pool`
- `the_grace_an_thuong_apartment` -> `The Grace An Thuong`
- `urbanr_danang_beach` -> `UrbanR Danang Beach`

## Luu y

- He thong dang dung che do `replace_sheet = true`
- Moi lan export se xoa du lieu cu trong tab roi ghi lai toan bo
- Neu review chua co ban dich VI, he thong se co gang dich bu luc export
