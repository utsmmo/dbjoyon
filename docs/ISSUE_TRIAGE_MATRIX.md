# Issue Triage Matrix

Tai lieu nay dung de khoanh nhanh ben nao can nhan viec dau tien khi co sai lech.

| Trieu chung | Ben nghi van dau tien | Ben phoi hop tiep theo | Ghi chu |
| --- | --- | --- | --- |
| UI hien sai field, label, trang thai loading/empty/error | FE | BE | Kiem tra field mapping va fallback UI |
| API tra 400/422/500 | BE | Tester | Xac dinh validation, service error, data contract |
| API dung field khac tai lieu | BE | Tester | Sinh lai `docs/API_ENDPOINTS.md`, cap nhat query guide neu can |
| Query cham, timeout, filter sai | DB | BE | Kiem tra index, query path, aggregate path |
| Migration loi hoac rollback khong an toan | DB | BE | DB la owner chinh |
| Frontend can field moi nhung API chua co | FE | BE | Ghi vao `docs/TASK_CURRENT_HANDOFF.md` |
| Backend doi contract ma UI vo | BE | FE | Cap nhat handoff va tai lieu endpoint |
| So lieu tong hop dashboard sai | DB | BE | Kiem tra aggregate tables, backfill, summary endpoints |
| Test pass nhung hanh vi that sai | Tester | FE/BE/DB | Bo sung test gap va reproduction steps |
| Tai lieu docs lech voi code | Tester | Owner layer lien quan | Chay drift checker, sinh lai docs |
| Docker build loi, compose sai, env sai, deploy loi | DevOps | BE/DB | Kiem tra image, compose, env wiring, migration order, health checks |

## Quy tac owner

- Loi contract API: `BE`
- Loi schema, migration, index, sync watermark: `DB`
- Loi hien thi, interaction, local state: `FE`
- Loi test gap, regression, doc drift, reproduce: `Tester`
- Loi Docker, compose, deploy, runtime config, backup path: `DevOps`
- Loi cross-layer, conflict vai tro, chot huong xu ly: `leader`
