# TODO MVP Chatbot AI

## Mục tiêu

Checklist này dùng để triển khai chatbot AI theo hướng:

- dùng chung `PostgreSQL`
- tách riêng dữ liệu bằng bảng `chatbot_*`
- không ảnh hưởng dữ liệu review cũ đang chạy
- đi theo MVP trước, mở rộng sau

## Trạng thái hiện tại

- [x] Đã có tài liệu chuẩn tại `docs/ChatbotAI/README.md`
- [x] Đã có migration riêng `db/migrations/015_chatbot_foundation.sql`
- [x] Dữ liệu chatbot được tách riêng khỏi bảng review cũ
- [ ] Chưa chốt đầy đủ mapping nguồn dữ liệu website/admin -> knowledge
- [ ] Chưa có flow webhook Pancake tối thiểu
- [ ] Chưa có flow AI tối thiểu
- [ ] Chưa có seed và test end-to-end cho 1 khách sạn thật

## Giai đoạn 1. Chốt schema và migration

- [x] Dùng bảng riêng `chatbot_*`
- [x] `handoff_queue` có `risk_level`
- [x] `knowledge_documents` có unique `(hotel_id, document_type, source_ref, version)`
- [x] `knowledge_documents.source_ref` là bắt buộc
- [x] `knowledge_sync_jobs` có `source_ref`
- [x] `knowledge_sync_jobs` có `started_at`
- [x] `knowledge_sync_jobs` có `finished_at`
- [x] `guest_memory` có `created_at`
- [x] `feedback_learning` có `updated_at`
- [x] Vector đang để optional bằng `vector_ref`, chưa phụ thuộc `pgvector`
- [ ] Chạy migration trên môi trường staging hoặc local test
- [ ] Kiểm tra thật bằng `\dt chatbot*`

## Giai đoạn 2. Chốt chiến lược vector

- [x] Migration chính không phụ thuộc `pgvector`
- [ ] Chốt dùng `pgvector` hay vector store ngoài
- [ ] Nếu dùng `pgvector`, xác nhận production đã cài extension `vector`
- [ ] Nếu dùng vector store ngoài, chốt naming cho `vector_ref`

## Giai đoạn 3. Chốt mapping với database hiện tại

- [x] Bảng khách sạn master hiện tại là `hotels`
- [x] Khóa chính hiện tại là `hotels.id`
- [ ] Chốt bảng nguồn cho `channel/page/inbox`
- [ ] Chốt bảng nguồn cho guest
- [ ] Chốt bảng nguồn cho conversation
- [ ] Chốt bảng nguồn cho message
- [x] Quyết định hiện tại là tạo bảng AI riêng, không merge vào bảng cũ

## Giai đoạn 4. Chốt knowledge source of truth

- [ ] Xác định bảng nguồn cho mô tả khách sạn
- [ ] Xác định bảng nguồn cho policy
- [ ] Xác định bảng nguồn cho breakfast
- [ ] Xác định bảng nguồn cho airport transfer
- [ ] Xác định bảng nguồn cho FAQ
- [ ] Xác định bảng nguồn cho SOP
- [ ] Đảm bảo bảng nguồn có `source_ref`
- [ ] Đảm bảo bảng nguồn có `updated_at`
- [ ] Ghi nhận `updated_by` nếu admin đang hỗ trợ

## Giai đoạn 5. Chốt dữ liệu không đưa vào RAG

- [x] Không đưa giá vào knowledge tĩnh
- [x] Không đưa tồn phòng vào knowledge tĩnh
- [x] Không đưa booking status vào knowledge tĩnh
- [x] Không đưa khuyến mãi realtime vào knowledge tĩnh
- [x] Không đưa surcharge theo ngày vào knowledge tĩnh
- [ ] Xác định các dữ liệu này đang nằm ở DB nào
- [ ] Xác định các dữ liệu này đang nằm ở bảng nào hoặc API nào

## Giai đoạn 6. Dựng luồng sync knowledge

- [ ] Tạo job sync `website/admin -> chatbot_knowledge_documents`
- [ ] Tạo bước chunk `chatbot_knowledge_documents -> chatbot_knowledge_chunks`
- [ ] Tạo log vào `chatbot_knowledge_sync_jobs`
- [ ] Lưu `error_message` nếu sync lỗi
- [ ] Re-index lại nếu tài liệu thay đổi

## Giai đoạn 7. Dựng inbound MVP

- [ ] Nhận webhook Pancake
- [ ] Normalize payload
- [ ] Map `page_id/inbox_id -> hotel_id`
- [ ] Upsert guest
- [ ] Upsert conversation
- [ ] Insert message
- [ ] Trả lời 1 tin nhắn cứng hoặc FAQ đơn giản

## Giai đoạn 8. Dựng AI MVP

- [ ] Xử lý `check-in`
- [ ] Xử lý `check-out`
- [ ] Xử lý `địa chỉ`
- [ ] Xử lý `breakfast`
- [ ] Xử lý `tiện ích cơ bản`
- [ ] Chưa bật booking automation sâu

## Giai đoạn 9. Dựng confidence và handoff

- [ ] Rule `>= 0.85` auto
- [ ] Rule `0.65 - 0.84` chỉ auto cho FAQ rõ
- [ ] Rule `< 0.65` handoff
- [ ] Khi handoff, gửi khách tin nhắn chờ
- [ ] Insert `chatbot_handoff_queue`
- [ ] Gửi notify sang Lark

## Giai đoạn 10. Test query và verify

- [ ] Query kiểm tra channel map đúng
- [ ] Query kiểm tra guest upsert đúng
- [ ] Query kiểm tra conversation tạo đúng
- [ ] Query kiểm tra message ghi đúng
- [ ] Query kiểm tra handoff tạo đúng
- [ ] Query kiểm tra knowledge document sync đúng
- [ ] Query kiểm tra knowledge chunk sync đúng

## Giai đoạn 11. Chạy thử với 1 khách sạn thật

- [ ] Chọn 1 khách sạn thật
- [ ] Chọn 1 kênh Pancake thật
- [ ] Seed đúng hotel và channel
- [ ] Test 1 webhook thật
- [ ] Test 1 câu FAQ
- [ ] Test 1 case confidence thấp
- [ ] Test handoff Lark

## Giai đoạn 12. Mở rộng sau MVP

- [ ] Nhân ra nhiều khách sạn
- [ ] Thêm nhiều intent
- [ ] Thêm staff feedback collector
- [ ] Thêm review dashboard
- [ ] Thêm learning loop định kỳ

## Thứ tự làm ngay

1. Chạy `015_chatbot_foundation.sql`
2. Kiểm tra bảng `chatbot_*`
3. Chốt mapping DB hiện tại
4. Seed 1 hotel + 1 channel
5. Test webhook Pancake
6. Test insert message
7. Test reply đơn giản
8. Test handoff Lark
9. Test sync knowledge
10. Sau đó mới nối Dify sâu hơn
