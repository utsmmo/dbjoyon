# Model Role Matrix

Tai lieu nay chot model mac dinh cho tung role de tranh tat ca agent cung dung chung mot cau hinh ton token.

## Role defaults

| Role | Model | Reasoning | Muc dich |
| --- | --- | --- | --- |
| `leader` | `gpt-5.6` | `high` | Ra quyet dinh cross-layer, tong hop, xu ly conflict |
| `BE` | `gpt-5.6` | `medium` | Contract, service, API logic can bang chat luong va chi phi |
| `FE` | `gpt-5.6-terra` | `medium` | Read-heavy, UI mapping, impact nhe va nhanh |
| `DB` | `gpt-5.6` | `high` | Migration, rollback, index, query risk can suy luan ky |
| `DevOps` | `gpt-5.6-terra` | `medium` | Docker, deploy, config wiring nhanh va co cau truc |
| `Tester` | `gpt-5.4` | `high` | Review regression, test gap, risk-focused pass voi chi phi thap hon `gpt-5.6` |

## Quy tac dieu chinh

- Tang reasoning truoc khi tang model neu task van cung vai tro nhung kho hon binh thuong.
- Chi day `FE` hoac `DevOps` len `gpt-5.6` khi task thuc su can suy luan mo hoac refactor lon.
- Neu `Tester` chi chay checklist nho, co the ha reasoning xuong `medium`.
- `leader` khong nen dung model re hon trong task cross-layer quan trong vi role nay la noi giu state va chot huong.

## Ghi chu ve chi phi

- `gpt-5.6-terra` phu hop cho worker nhanh, scan nhieu, tong hop gon.
- `gpt-5.6` phu hop cho xu ly ambiguity, validation, va follow-through.
- `gpt-5.4` la diem giua hop ly cho role reviewer/tester khi muon tiet kiem hon `gpt-5.6`.
