# Hotel Knowledge Template

## Purpose

Use this template to prepare hotel knowledge for `n8n + LangGraph`.

This template is designed for:

- one hotel per block
- one topic per section
- easy review by admin
- easy conversion into `knowledge_sources`

## Recommended rule

- Keep the real hotel name in the source file if the file is private.
- Add the internal hotel code used by the system, for example `DN1`, `DN2`, `HA5`.
- Do not rely only on sheet names for mapping.
- Each hotel should have a stable `hotel_code`.

## Required fields per hotel

```yaml
hotel_code:
hotel_name:
language: vi
source_type: excel_manual
source_ref:
status: draft
```

## Recommended sections per hotel

### 1. Overview

```yaml
document_type: overview
title:
content:
```

### 2. Location

```yaml
document_type: location
title: Location
content:
google_map_url:
nearby_points:
```

### 3. Room types

```yaml
document_type: room_types
title: Room types
content:
```

### 4. Breakfast

```yaml
document_type: breakfast
title: Breakfast
content:
```

### 5. Facilities

```yaml
document_type: facilities
title: Facilities
content:
```

### 6. Pool

```yaml
document_type: pool
title: Pool
content:
```

### 7. Contact and wifi

```yaml
document_type: contact_wifi
title: Contact and wifi
content:
hotline:
wifi_name:
wifi_password:
```

### 8. Check-in and check-out

```yaml
document_type: checkin_checkout
title: Check-in and check-out
content:
checkin_time:
checkout_time:
```

### 9. Extra guest / child policy

```yaml
document_type: surcharge_policy
title: Extra guest and child policy
content:
```

### 10. Cancellation policy

```yaml
document_type: cancellation_policy
title: Cancellation policy
content:
```

### 11. Airport transfer

```yaml
document_type: airport_transfer
title: Airport transfer
content:
```

### 12. FAQ

```yaml
document_type: faq
title:
content:
```

## Example

```yaml
hotel_code: DN1
hotel_name: A Danang Beach Hotel
language: vi
source_type: excel_manual
source_ref: workbook_sheet_a_danang_beach_hotel
status: draft

sections:
  - document_type: location
    title: Location
    content: |
      11 An Thuong 32, Ngu Hanh Son, Da Nang.
      Gan bien My Khe khoang 300m.
    google_map_url:

  - document_type: breakfast
    title: Breakfast
    content: |
      Khong phuc vu an sang. Xung quanh co nhieu quan an va nha hang.

  - document_type: checkin_checkout
    title: Check-in and check-out
    content: |
      Check-in sau 14:00. Check-out truoc 12:00.
    checkin_time: "14:00"
    checkout_time: "12:00"
```

## Best practice for your current Excel file

For your current workbook:

- keep each sheet as one hotel
- add one new first row or metadata block with `hotel_code`
- map every line like `Phục vụ ăn sáng`, `Hồ bơi`, `Check in/ Check out` into its own `document_type`

Suggested mapping:

- `Địa điểm` -> `location`
- `Vị trí gần` -> `location_nearby`
- `Các hạng phòng` -> `room_types`
- `Phục vụ ăn sáng` -> `breakfast`
- `Tiện ích` -> `facilities`
- `Hồ bơi` -> `pool`
- `Hotline/ Wifi` -> `contact_wifi`
- `Check in/ Check out` -> `checkin_checkout`
- `Chính sách phụ thu phát sinh khách` -> `surcharge_policy`
- `Chính sách hoàn/huỷ đặt phòng` -> `cancellation_policy`

## Upload direction in ChatBot admin

When the UI is completed, this workbook should go into:

- `ChatBot`
- choose one hotel
- `Knowledge`
- import or create sections by `document_type`

It should not go into:

- `System Settings`
- `AI panel`
- `Runtime sources`

## Security recommendation

If you do not want to expose real names in the system UI:

- keep the private workbook with real names
- add `hotel_code` like `DN1`, `DN2`, `HA5`
- let the system store and display by `hotel_code`
- keep the real hotel name only in private source files or admin-only metadata

This is better than renaming everything manually without a mapping field.
