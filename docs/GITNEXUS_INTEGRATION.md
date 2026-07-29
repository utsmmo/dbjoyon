# GitNexus Integration

Tai lieu nay giai thich GitNexus nam o dau trong bo nay va no giai quyet bai toan gi.

## GitNexus co nam trong bo kit khong

Co, nhung can tach ro 2 lop:

### 1. Repo-local

Day la phan nam trong chinh project:

- `.gitnexus/` index cua repo
- `node .gitnexus/run.cjs analyze`
- docs va playbook cua repo yeu cau `leader`, `BE`, `FE`, `DB`, `DevOps`, `Tester` uu tien GitNexus khi can trace flow, impact, va route map

### 2. Machine-level connector

Day la phan nam o may cua nguoi dung:

- MCP server GitNexus trong `~/.codex/config.toml`
- GitNexus CLI da cai va setup cho Codex

Ly do:

- Index va graph cua tung repo la repo-local
- ket noi MCP de Codex goi GitNexus la machine-level

## GitNexus co ket noi "cac du lieu ve chung 1 ban" khong

Neu "du lieu" o day la:

### Code context, route, call graph, impact, relation

Co.
GitNexus rat hop de dua nhung thong tin nay ve mot graph chung de agent nao cung doc cung mot su that.

### Business data, database rows, operational data

Khong truc tiep.
GitNexus khong thay the PostgreSQL, Redis, data warehouse, hay memory store cho du lieu nghiep vu.
No la source of truth cho **code relationships**, khong phai source of truth cho business records.

## Cach dung trong repo nay

1. Setup GitNexus tren may mot lan
2. Analyze repo:

```powershell
node .gitnexus/run.cjs analyze
```

3. Khi task mo ho, dung:

- repo context
- query
- context
- impact
- route_map
- shape_check

## Cach dua vao kit moi

Kit scaffold:

- docs huong dan GitNexus
- model role matrix
- memory/task queue/compact docs

Kit khong tu dong sua global `~/.codex/config.toml`.
Dieu do duoc giu tach rieng vi no la machine-level, khong nen bi project bootstrap tu y ghi de.

## Neu muon dung GitNexus tren may moi

Tren may moi, can:

1. cai GitNexus
2. chay setup cho Codex
3. analyze repo

Sau do bo kit trong repo moi co the dung GitNexus ngay.
