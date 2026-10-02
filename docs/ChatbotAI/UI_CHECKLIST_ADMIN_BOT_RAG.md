# UI Checklist Cho Admin Bot Và RAG

## Mục tiêu

Checklist này dành cho FE để dựng màn hình admin bot mà không đoán thêm logic.

## Cấu trúc menu admin đề xuất

Trong mục admin, nên có group riêng:

- `Bot Control`
- `Knowledge`
- `Channels`
- `Runtime Sources`
- `Conversations`
- `Handoffs`
- `Sync Jobs`

## 1. Bot Control

### Màn hình danh sách khách sạn

Phải có:

- tên khách sạn
- mã khách sạn
- trạng thái bot
- default language
- confidence threshold
- handoff threshold
- trạng thái auto reply
- nút `Edit`

### Màn hình edit bot settings

Phải có:

- select `bot_status`
- input `confidence_threshold`
- input `handoff_threshold`
- toggle:
  - auto reply
  - after-hours reply
  - price quote
  - inventory lookup
  - booking status lookup
- input `handoff channel`
- input `handoff target`
- editor cho `business_hours_json`
- textarea `notes`

Validation FE:

- threshold phải trong `0 -> 1`
- `handoff_threshold` không nên lớn hơn `confidence_threshold`

## 2. Knowledge

### Danh sách knowledge

Phải có filter:

- hotel
- document type
- status
- language
- search text

Cột cần có:

- title
- hotel
- type
- language
- status
- version
- updated_at
- updated_by
- action

Action nên có:

- view
- edit
- publish
- sync
- reindex
- archive
- duplicate

### Form tạo và sửa knowledge

Phải có:

- hotel
- document type
- title
- language
- source_ref
- version
- status
- tags
- content editor

UI state bắt buộc:

- draft
- review
- published
- archived

Nút nên có:

- save draft
- submit review
- publish
- sync to rag

### Lưu ý UX

- hiển thị cảnh báo nếu content thay đổi nhưng chưa sync
- hiển thị version hiện tại
- hiển thị sync status gần nhất

## 3. Channels

### Danh sách channels

Cột cần có:

- hotel
- channel type
- channel name
- external key
- page id
- inbox id
- active
- updated_at

Action:

- add
- edit
- disable
- test mapping

### Form channel

Phải có:

- hotel
- channel type
- channel name
- external channel key
- page id
- inbox id
- routing notes
- active toggle

## 4. Runtime Sources

### Danh sách runtime sources

Cột cần có:

- hotel
- source group
- source code
- source type
- target ref
- active
- last status
- last checked at

Action:

- add
- edit
- test source

### Form runtime source

Phải có:

- hotel
- source group
- source code
- source type
- connection name
- target ref
- query template
- mapping json
- active toggle

### UX cần có

- test result box
- error box nếu fail
- sample response nếu test thành công

## 5. Conversations

### Danh sách conversations

Filter:

- hotel
- channel
- guest
- status

Cột:

- guest name
- hotel
- channel
- last message
- last message at
- status

Action:

- view thread

### Màn hình conversation detail

Phải hiển thị:

- message role
- content gốc
- translated content nếu có
- intent
- confidence score
- risk level
- handoff flag
- sources used
- created_at

FE cần lưu ý:

- text dài phải wrap tốt trên mobile
- JSON evidence không đổ raw toàn bộ mặc định
- chỉ expand khi cần

## 6. Handoffs

### Danh sách handoff

Filter:

- hotel
- status
- risk level
- assigned_to

Cột:

- hotel
- guest
- reason
- confidence score
- risk level
- assigned_to
- created_at
- status

Action:

- assign
- resolve
- retry notify

## 7. Sync Jobs

### Danh sách sync jobs

Cột:

- hotel
- document type
- source ref
- status
- started_at
- finished_at
- error message

Action:

- view log
- retry nếu backend hỗ trợ

## Phân quyền FE

`admin` nhìn và sửa được tất cả.

`editor`:

- sửa knowledge
- publish knowledge nếu business cho phép
- không sửa runtime source nhạy cảm
- không sửa bot thresholds hệ thống

`viewer`:

- xem conversations
- xem handoff
- xem sync jobs
- không sửa config

## Trạng thái UI bắt buộc

Mỗi màn hình phải có:

- loading
- empty state
- error state
- success toast
- validation message rõ ràng

## Checklist test FE

### Knowledge

- tạo draft được
- sửa draft được
- publish được
- sync được
- trạng thái cập nhật đúng

### Channels

- thêm channel được
- không thêm trùng external key
- disable được

### Runtime Sources

- test source chạy được
- lỗi hiển thị rõ

### Conversations

- xem message dài không bể layout
- mobile không cắt text sai

### Handoff

- assign được
- resolve được
- retry notify được

## Thứ tự FE nên làm

1. Bot Control
2. Knowledge list + form
3. Channel list + form
4. Sync jobs
5. Conversations
6. Handoffs
7. Runtime Sources

## Chốt ngắn

Nếu chỉ dựng 2 màn đầu cho MVP:

1. `Knowledge`
2. `Channels`

Đây là phần giúp bot chạy được nhanh nhất và ít phụ thuộc nhất.
