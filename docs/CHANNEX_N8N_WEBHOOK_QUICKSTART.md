# Channex -> data.datac.click -> n8n

## URL webhook Channex cần gọi

- `POST https://data.datac.click/api/v1/integrations/channex/webhook`

## Header từ Channex nên set

- `X-Channex-Webhook-Secret: <secret-cua-ban>`

## Env cần set trong n8n

```env
CHANNEX_WEBHOOK_SECRET=your-secret
```

## Env nên set trong `data.datac.click`

```env
CHANNEX_ENV_FILE=./env.channex
```

## Flow

1. Channex bắn webhook vào `data.datac.click`
2. `data.datac.click` check `X-Channex-Webhook-Secret`
3. `data.datac.click` forward ngay sang `https://n8n2.joyon.asia/webhook/channex`
4. n8n lấy `booking_id`
5. n8n gọi API summary:

`GET https://data.datac.click/api/v1/integrations/channex/channexapi/bookings/{booking_id}?relationships=all`

6. backend trả bản gọn
7. n8n chuẩn hóa phone
8. n8n route theo `customer_country`

## Payload Channex gửi sang

```json
{
  "event": "booking",
  "booking_id": "54e5f3ae-e466-47af-bf90-028aaf9c2498",
  "revision_id": "761b2ebf-cd5a-40ee-8fcd-fb6d372a1bb4",
  "property_id": "b9da283a-181d-4a0c-9bb4-f92a94b21b22"
}
```

## File workflow import sẵn

- `D:\AutoCode\CMS\n8n\channex-booking-router.json`

## Workflow này làm gì

1. nhận `POST /webhook/channex` từ `data.datac.click`
2. lấy `booking_id`
3. gọi `data.datac.click` để lấy booking summary gọn
4. normalize `customer_phone`
5. route theo `customer_country`
6. trả JSON gọn để nối tiếp sang Pancake / WhatsApp / Zalo

## Kết quả trả về mẫu

```json
{
  "success": true,
  "booking_id": "54e5f3ae-e466-47af-bf90-028aaf9c2498",
  "property_id": "b9da283a-181d-4a0c-9bb4-f92a94b21b22",
  "hotel_id": "135233192",
  "hotel_code": "DN3",
  "hotel_name": "DN3",
  "ota_name": "CTrip",
  "ota_reservation_code": "1658114189155607",
  "channel_id": "a41fb5c5-94bd-4b7b-a2f6-1d1a4b4a18b5",
  "revision_id": "761b2ebf-cd5a-40ee-8fcd-fb6d372a1bb4",
  "customer_name": "Elizaveta Mironova",
  "customer_phone": "+842873031966(110400)",
  "customer_phone_normalized": "+842873031966110400",
  "customer_email": "welcomeoldtownh.4rr2yvlax0g30rt@guest.trip.com",
  "customer_country": null,
  "guest_message": null,
  "arrival_date": "2026-08-21",
  "departure_date": "2026-08-22",
  "amount": "399000",
  "currency": "VND",
  "target_channel": "whatsapp",
  "route_key": "DN3:zalo"
}
```

## Rule route hien tai

- `customer_country = VN` -> `zalo`
- con lai -> `whatsapp`
