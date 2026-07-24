# Database Backup Và Upload Google Drive

Tài liệu này mô tả cách backup PostgreSQL hằng ngày và đẩy file backup lên Google Drive.

## Mục tiêu

- backup database mỗi ngày
- lưu file backup local trong máy deploy
- tự động upload lên Google Drive
- có lệnh restore khi cần

## Kiến trúc backup đề nghị

```text
Docker PostgreSQL -> pg_dump (.dump) -> thư mục backups local -> rclone -> Google Drive
```

Khuyến nghị:

- backup ít nhất 1 lần/ngày
- giữ local 7-14 ngày
- giữ Google Drive lâu hơn để phòng máy host hỏng

## File đã có sẵn

- [ops/backup/backup-db.ps1](D:/AutoCode/DB/Review/ops/backup/backup-db.ps1)
- [ops/backup/restore-db.ps1](D:/AutoCode/DB/Review/ops/backup/restore-db.ps1)

## 1. Cài rclone

Trên Windows:

1. cài `rclone`
2. mở terminal
3. chạy:

```powershell
rclone config
```

Tạo một remote, ví dụ:

- remote name: `gdrive`
- storage type: `drive`

Sau khi config xong, test:

```powershell
rclone lsd gdrive:
```

Nếu thấy danh sách folder trên Google Drive thì là OK.

## 2. Backup thủ công 1 lần

Chạy lệnh:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\backup\backup-db.ps1 -RcloneRemote gdrive -RclonePath "hotel-review-db/daily"
```

Lệnh này sẽ:

1. tạo file `pg_dump` dạng custom format `.dump`
2. copy file về thư mục local `.\backups`
3. upload file lên `gdrive:hotel-review-db/daily`
4. xóa local backup cũ hơn 14 ngày

## 3. Thư mục local backup

Mặc định:

- `D:\AutoCode\DB\Review\backups`

Muốn đổi sang thư mục khác:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\backup\backup-db.ps1 -OutputDir "D:\DBBackups" -RcloneRemote gdrive -RclonePath "hotel-review-db/daily"
```

## 4. Lịch backup hằng ngày

### Cách dễ nhất trên Windows: Task Scheduler

Tạo task mới:

- Name: `HotelReviewDailyBackup`
- Trigger: Daily
- Time: ví dụ `01:30`
- Action:

Program:

```text
powershell.exe
```

Arguments:

```text
-ExecutionPolicy Bypass -File "D:\AutoCode\DB\Review\ops\backup\backup-db.ps1" -RcloneRemote gdrive -RclonePath "hotel-review-db/daily"
```

Start in:

```text
D:\AutoCode\DB\Review
```

## 5. Nếu muốn chỉ backup local, chưa upload Google Drive

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\backup\backup-db.ps1
```

## 6. Restore database

Ví dụ restore từ file:

```powershell
powershell -ExecutionPolicy Bypass -File .\ops\backup\restore-db.ps1 -BackupFile ".\backups\hotel_review_db-20260723-013000.dump"
```

Cảnh báo:

- restore sẽ ghi đè dữ liệu hiện tại trong database
- chỉ restore khi đã chắc chắn

## 7. Google Drive upload command nếu muốn gọi trực tiếp

Nếu đã có file backup local rồi, có thể upload bằng lệnh:

```powershell
rclone copy ".\backups\hotel_review_db-20260723-013000.dump" "gdrive:hotel-review-db/daily"
```

Hoặc upload cả folder:

```powershell
rclone copy ".\backups" "gdrive:hotel-review-db/daily"
```

## 8. Kiểm tra backup đã tạo

### Local

```powershell
Get-ChildItem .\backups
```

### Google Drive

```powershell
rclone ls "gdrive:hotel-review-db/daily"
```

## 9. Định dạng backup

Đang dùng:

- `pg_dump -Fc`

Ý nghĩa:

- custom format
- nén tốt hơn SQL text
- phù hợp để restore bằng `pg_restore`

## 10. Ghi chú quan trọng

- chỉ backup PostgreSQL, không backup volume bằng cách copy thư mục data thẳng khi DB đang chạy
- nên ưu tiên `pg_dump`
- database không nên public ra internet để backup
- backup script đang nhắm vào container:
  - `hotel-review-postgres`

Nếu sau này đổi tên container, nhớ đổi:

- `-ContainerName`

## 11. Lệnh mẫu đầy đủ cho máy hiện tại

```powershell
powershell -ExecutionPolicy Bypass -File "D:\AutoCode\DB\Review\ops\backup\backup-db.ps1" `
  -ContainerName "hotel-review-postgres" `
  -DatabaseName "hotel_review_db" `
  -DatabaseUser "hotel_admin" `
  -DatabasePassword "hotel_admin_123" `
  -RcloneRemote "gdrive" `
  -RclonePath "hotel-review-db/daily" `
  -KeepLocalDays 14
```
