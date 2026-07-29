# Filter Test Plan

## Muc tieu

- Tao bo case co thu tu ro rang cho `Tester`.
- Moi case phai tra loi duoc 3 cau hoi:
  - UI co nhan filter khong
  - Request/du lieu co thay doi khong
  - Card, chart, table, pagination co dong bo khong

## Cach chay

- URL test chinh: `http://localhost:3000/review`
- Chup `baseline` truoc khi test:
  - `Visible reviews`
  - `Average score / 10`
  - `Hotels in view`
  - `Top guest country`
  - `Review Table rows`
  - `Page x of y`
- Moi case deu phai ghi:
  - `Before`
  - `Action`
  - `After`
  - `Pass/Fail`
  - `Owner if fail`

## Thu tu uu tien

1. Smoke filter state
2. Date filter
3. Flag filter
4. Rating filter
5. OTA filter
6. Guest country filter
7. Combined filters
8. Reset filter

## Test cases

### 1. Smoke filter state

- Action:
  - Mo trang `review`
  - Khong chon gi
- Expected:
  - Nut la `Applied`
  - Khong co banner unsupported
  - Card va table co du lieu
- Owner if fail:
  - `FE`

### 2. Date filter

- Action:
  - Nhap `From`
  - Nhap `To`
  - Xac nhan nut doi tu `Applied` sang `Filter`
  - Bam `Filter`
- Expected:
  - Date hien dung trong control
  - `Visible reviews` thay doi neu tap du lieu thay doi
  - `rows` va `Page x of y` doi theo du lieu moi
  - Card va table khop nhau
- Owner if fail:
  - `FE` truoc
  - `BE` neu request da gui dung ma data sai

### 3. Flag filter

- Action:
  - Chon `Bad`
  - Bam `Filter`
- Expected:
  - `Visible reviews`, `Average score`, `Hotels in view`, `Top guest country`, `rows`, `Page x of y` phai dong bo
  - Khong duoc co truong hop table doi ma KPI tong khong doi
- Owner if fail:
  - `FE`

### 4. Rating filter

- Action:
  - Test `Min rating`
  - Test `Max rating`
  - Test ca 2 cung luc
- Expected:
  - Nut doi sang `Filter`
  - Data sau loc phai hop ly voi score hien tren row
  - Neu analytics khong support hoan toan thi phai co thong bao ro
- Owner if fail:
  - `FE` neu UI/hien thi sai
  - `BE` neu contract analytics sai

### 5. OTA filter

- Action:
  - Chon 1 OTA
  - Bam `Filter`
  - Reset
  - Chon OTA khac
- Expected:
  - UI phai phan anh dung `single-select`
  - Table va KPI thay doi theo OTA da chon
  - Khong duoc co state "chon nhieu nhung request bo filter"
- Owner if fail:
  - `FE`
  - `BE` neu can doi contract multi-OTA

### 6. Guest country filter

- Action:
  - Chon 1 guest country co san
  - Bam `Filter`
- Expected:
  - Row trong table phai thuoc country do
  - KPI tong va summary khop voi table
  - Neu chart aggregate khong support thi phai bao ro
- Owner if fail:
  - `FE` neu proxy/hien thi sai
  - `BE` neu summary/aggregate contract sai

### 7. Combined filters

- Action:
  - Test `Date + Flag`
  - Test `OTA + Country`
  - Test `Rating + Country`
- Expected:
  - Moi lan doi filter deu phai doi nut sang `Filter`
  - Sau apply, card, table, pagination phai cung mot nguon su that
  - Neu unsupported phai co banner/thong diep ro
- Owner if fail:
  - `leader` khoanh lai
  - Sau do giao `FE` / `BE` / `DB`

### 8. Reset filter

- Action:
  - Sau khi da loc, bam `Reset`
- Expected:
  - Tat ca control ve default
  - KPI va table ve baseline
  - Nut tro lai `Applied`
- Owner if fail:
  - `FE`

## Quy tac giao viec sau test

- Neu control doi sai, state sai, pagination sai, card/table lech nhau:
  - giao `FE`
- Neu request dung nhung response sai, summary sai, contract sai:
  - giao `BE`
- Neu aggregate, query, index, tong hop du lieu sai:
  - giao `DB`
- Neu khong ro owner hoac loi cat ngang nhieu lop:
  - `leader` tao handoff trong `docs/TASK_CURRENT_HANDOFF.md`

## Mau bao cao cho Tester

- `Case`
- `Before`
- `Action`
- `After`
- `Expected`
- `Actual`
- `Pass/Fail`
- `Owner`
