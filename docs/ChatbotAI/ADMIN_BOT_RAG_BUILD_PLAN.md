# Kế Hoạch Chức Năng Admin Cho Bot Và RAG

## Mục tiêu

Tài liệu này chốt rõ:

- admin cần có những chức năng gì để vận hành BotAI
- phần nào là source of truth
- phần nào chỉ là dữ liệu sync cho RAG
- thứ tự triển khai từ MVP đến production

Mục tiêu là để team làm đúng ngay từ đầu, không trộn lẫn:

- website admin
- knowledge cho bot
- runtime data
- handoff
- workflow chatbot

## Nguyên tắc tổng thể

### 1. Website admin là nơi vận hành

Website admin là nơi người dùng:

- tạo và sửa dữ liệu knowledge
- map channel với khách sạn
- bật hoặc tắt bot theo khách sạn
- cấu hình ngưỡng confidence và handoff
- kiểm tra log chat
- kiểm tra job sync knowledge

### 2. Database là nguồn chạy của bot

Bot không nên đọc file rời trực tiếp trong thư mục website khi trả lời thật.

Bot nên đọc từ database:

- `knowledge_documents`
- `knowledge_chunks`
- `hotels`
- `hotel_channels`
- `guests`
- `conversations`
- `messages`
- `handoff_queue`
- `feedback_learning`
- `knowledge_sync_jobs`

### 3. Tách rõ knowledge và runtime

Không được trộn hai nhóm này với nhau.

`Knowledge` là dữ liệu ổn định hoặc bán ổn định:

- mô tả khách sạn
- FAQ
- policy
- breakfast
- airport transfer
- facilities
- SOP

`Runtime` là dữ liệu cần query tại thời điểm hiện tại:

- giá
- tồn phòng
- booking status
- tình trạng đơn

Knowledge được sync vào RAG.
Runtime không đưa vào RAG cố định, mà phải query theo thời điểm.

## Phân vùng chức năng admin

Admin nên tách thành 6 khu vực rõ ràng.

## 1. Hotel Bot Settings

Mục tiêu:

- mỗi khách sạn có cấu hình bot riêng

Thông tin cần có:

- `hotel_id`
- tên khách sạn
- mã khách sạn
- `default_language`
- `supported_languages`
- `confidence_threshold`
- `handoff_threshold`
- cho phép auto reply hay không
- cho phép trả lời ngoài giờ hay không
- có cho phép quote giá tự động hay không
- channel Lark nhận handoff
- trạng thái bot: `draft`, `pilot`, `active`, `paused`

Chức năng admin:

- xem danh sách khách sạn
- bật hoặc tắt bot theo khách sạn
- chỉnh ngưỡng confidence
- chỉnh rule handoff
- cấu hình ca trực hoặc trạng thái ngoài giờ

## 2. Knowledge Management

Đây là khu vực quan trọng nhất.

Mục tiêu:

- admin tạo và sửa knowledge dùng cho bot

Loại knowledge nên có:

- `hotel_description`
- `faq`
- `policy`
- `breakfast`
- `airport_transfer`
- `facility`
- `room_info`
- `sop`

Mỗi bản ghi knowledge source nên có:

- `id`
- `hotel_id`
- `document_type`
- `title`
- `content`
- `language`
- `status`
- `source_ref`
- `version`
- `updated_at`
- `updated_by`

Trạng thái nên có:

- `draft`
- `review`
- `published`
- `archived`

Chức năng admin:

- tạo bài knowledge
- sửa bài knowledge
- publish bài knowledge
- duplicate từ khách sạn này sang khách sạn khác
- xem version
- xem ai sửa gần nhất
- bấm sync sang `knowledge_documents`
- bấm re-index sang `knowledge_chunks`

Quy tắc:

- chỉ `published` mới được sync sang RAG production
- `draft` và `review` không được dùng để bot trả lời thật

## 3. Channel Mapping

Mục tiêu:

- map đúng kênh chat vào đúng khách sạn

Ví dụ:

- Pancake page
- Pancake inbox
- Facebook page
- Zalo OA
- WhatsApp

Thông tin cần có:

- `hotel_id`
- `channel_type`
- `external_channel_key`
- `page_id`
- `inbox_id`
- `is_active`
- `routing_notes`

Chức năng admin:

- thêm channel mới
- map channel vào khách sạn
- bật hoặc tắt channel
- kiểm tra channel nào chưa map
- khóa không cho 1 channel map vào 2 khách sạn cùng lúc

## 4. Runtime Source Registry

Mục tiêu:

- chốt rõ bot lấy dữ liệu runtime từ đâu

Admin không cần nhập dữ liệu runtime bằng tay nhiều, nhưng cần cấu hình nguồn.

Nhóm nguồn cần có:

- `price_source`
- `inventory_source`
- `booking_status_source`

Mỗi nguồn nên có:

- `source_code`
- `source_type`: `table`, `view`, `api`
- `connection_name`
- `target_table_or_endpoint`
- `query_key`
- `response_mapping`
- `is_active`
- `last_checked_at`

Chức năng admin:

- khai báo nguồn runtime
- kiểm tra nguồn có hoạt động không
- test query
- log lỗi kết nối

Lưu ý:

- phần này chỉ để cấu hình và kiểm tra
- không biến admin thành nơi sửa giá hoặc sửa tồn phòng nếu dữ liệu đó đến từ PMS hay hệ khác

## 5. Handoff Và Notification

Mục tiêu:

- khi bot không tự trả lời an toàn thì chuyển đúng người

Thông tin cấu hình:

- channel Lark
- nhóm tiếp nhận
- rule trong giờ hoặc ngoài giờ
- rule theo khách sạn
- rule theo mức độ rủi ro

Chức năng admin:

- cấu hình webhook hoặc bot channel
- xem hàng chờ handoff
- xem trạng thái gửi notify
- retry notify lỗi
- xem lịch sử notify

## 6. Bot QA Và Audit

Mục tiêu:

- kiểm tra bot trả lời đúng hay sai

Chức năng admin:

- xem hội thoại theo khách sạn
- lọc các câu confidence thấp
- lọc các case handoff
- đánh dấu câu trả lời đúng hoặc sai
- lưu feedback vào `feedback_learning`
- xem source knowledge đã dùng
- xem runtime nào đã được gọi

Đây là nơi giúp bạn biết:

- bot đang thiếu knowledge gì
- bot đang bịa ở đâu
- runtime nào đang lỗi

## Phân quyền admin đề xuất

Nên chia tối thiểu 4 nhóm:

- `super_admin`
- `bot_admin`
- `knowledge_editor`
- `operator_viewer`

Quyền gợi ý:

- `super_admin`: toàn quyền
- `bot_admin`: quản lý bot settings, channel mapping, handoff, runtime source
- `knowledge_editor`: chỉ sửa knowledge và publish knowledge
- `operator_viewer`: chỉ xem log, QA, handoff, conversation

Nếu muốn đơn giản ở giai đoạn đầu:

- chỉ cần `admin`
- `editor`
- `viewer`

## Thứ tự làm từng bước đến khi hoàn thiện

Nên đi theo 8 giai đoạn.

## Giai đoạn 1. Chốt data boundary

Phải chốt trước:

- bảng nào là knowledge source
- bảng nào là runtime source
- bảng nào là log chatbot

Kết quả cần có:

- 1 sơ đồ source of truth
- 1 danh sách bảng
- 1 danh sách field bắt buộc

## Giai đoạn 2. Làm Knowledge Source Trong Admin

Phải làm trước tiên vì đây là phần dễ chạy MVP nhất.

Việc cần làm:

- tạo UI quản lý knowledge
- tạo bảng knowledge source nếu chưa có
- thêm `draft/review/published`
- thêm `version`, `updated_by`, `updated_at`
- thêm nút `Publish`

Done khi:

- admin tạo được 1 FAQ
- publish được
- lưu đúng theo khách sạn

## Giai đoạn 3. Sync Knowledge Sang RAG

Việc cần làm:

- viết job sync từ knowledge source sang `knowledge_documents`
- viết bước chunk sang `knowledge_chunks`
- ghi log vào `knowledge_sync_jobs`
- có retry nếu lỗi

Done khi:

- một bài knowledge publish xong được sync
- chunk sinh ra đúng
- log sync xem được trong admin

## Giai đoạn 4. Làm Channel Mapping

Việc cần làm:

- tạo UI map channel vào khách sạn
- chống trùng channel
- thêm test connection hoặc test inbound payload

Done khi:

- mỗi kênh chat map đúng 1 khách sạn
- team workflow biết `page_id/inbox_id` đi vào đâu

## Giai đoạn 5. Làm Bot Settings Theo Khách Sạn

Việc cần làm:

- thêm UI chỉnh `confidence_threshold`
- thêm UI chỉnh `handoff_threshold`
- thêm `bot_status`
- thêm `allow_auto_reply`
- thêm `allow_price_quote`
- thêm `after_hours_policy`

Done khi:

- mỗi khách sạn có rule bot riêng
- có thể bật pilot cho 1 khách sạn mà không ảnh hưởng khách sạn khác

## Giai đoạn 6. Làm Runtime Source Registry

Việc cần làm:

- khai báo nguồn `price`
- khai báo nguồn `inventory`
- khai báo nguồn `booking_status`
- thêm nút test nguồn

Giai đoạn này chưa cần bot xử lý toàn bộ.
Chỉ cần biết bot sẽ lấy từ đâu và test được kết nối.

Done khi:

- admin nhìn được nguồn nào đang có
- nguồn nào đang thiếu
- test query tối thiểu chạy được

## Giai đoạn 7. Làm QA Và Handoff

Việc cần làm:

- tạo màn hình xem conversation
- tạo filter confidence thấp
- tạo màn hình handoff queue
- tạo lịch sử notification
- cho phép đánh dấu feedback đúng/sai

Done khi:

- operator nhìn được case lỗi
- biết bot dùng knowledge nào
- biết vì sao handoff

## Giai đoạn 8. Nối workflow thật

Việc cần làm:

- map payload Pancake thật
- nối outbound reply
- nối Lark thật
- test end-to-end

Thứ tự chạy thật:

1. inbound message
2. map hotel/channel
3. tìm knowledge
4. gọi runtime nếu cần
5. trả lời hoặc handoff
6. ghi log và feedback

Done khi:

- 1 khách sạn chạy pilot hoàn chỉnh
- có knowledge thật
- có channel thật
- có handoff thật

## Thứ tự ưu tiên thực chiến

Nếu bạn muốn ra bản dùng được nhanh nhất, làm theo thứ tự này:

1. Knowledge source admin
2. Publish và sync sang RAG
3. Channel mapping
4. Bot settings per hotel
5. QA conversation screen
6. Handoff queue
7. Runtime source registry
8. Nối Pancake thật
9. Nối Lark thật
10. Mở pilot cho 1 khách sạn

## Những gì chưa nên làm quá sớm

Không nên làm ngay từ đầu:

- multi-channel quá nhiều cùng lúc
- full auto price quote cho tất cả khách sạn
- booking status automation sâu
- learning loop tự update knowledge không qua duyệt

Nên giữ an toàn:

- FAQ và policy có thể auto
- giá, tồn phòng, booking status thì query runtime hoặc handoff

## Kết quả hoàn thiện mong muốn

Khi làm xong đúng hướng, admin sẽ có:

- nơi nhập knowledge chuẩn
- nơi publish knowledge
- nơi sync sang RAG
- nơi map channel về khách sạn
- nơi cấu hình bot theo khách sạn
- nơi xem conversation và QA
- nơi quản lý handoff
- nơi kiểm tra nguồn runtime

Bot sẽ có:

- knowledge sạch
- boundary rõ
- không đọc file rời lung tung
- không bịa giá khi chưa có runtime source thật
- không nhầm khách sạn khi inbound message vào

## Chốt ngắn

Nếu chỉ chọn một điểm bắt đầu, hãy bắt đầu từ:

- `Knowledge Management`

Nếu chọn hai điểm bắt đầu song song, hãy làm:

- `Knowledge Management`
- `Channel Mapping`

Đây là hai phần đem lại MVP nhanh nhất và ít rủi ro nhất.
