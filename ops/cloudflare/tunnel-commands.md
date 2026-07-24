# Cloudflare Tunnel Quick Setup

Muc tieu:

- Public `app/api` qua `https://db.datac.click`
- Hoac public `pgAdmin` qua `https://pgadmin.example.com`
- Khong public PostgreSQL truc tiep

## 1. Cai cloudflared

Tai va cai `cloudflared` tren may chay Docker host.

## 2. Dang nhap Cloudflare

```bash
cloudflared tunnel login
```

## 3. Tao tunnel

```bash
cloudflared tunnel create hotel-review
```

Lenh nay se tra ra `TUNNEL_ID` va tao file credentials trong thu muc `.cloudflared`.

## 4. Tao DNS route

```bash
cloudflared tunnel route dns hotel-review review.example.com
cloudflared tunnel route dns hotel-review pgadmin.example.com
```

## 5. Tao file config

Copy file:

- [ops/cloudflare/config.example.yml](D:/AutoCode/DB/Review/ops/cloudflare/config.example.yml)

Thanh:

- `%USERPROFILE%\\.cloudflared\\config.yml`

Sau do thay:

- `YOUR_TUNNEL_ID`
- `db.datac.click`
- `pgadmin.example.com`
- duong dan credentials file thuc te

## 6. Chay tunnel

```bash
cloudflared tunnel run hotel-review
```

## Luong truy cap dung

```text
User -> Cloudflare DNS/Subdomain -> Cloudflare Tunnel -> localhost:13000 (API/App)
User -> Cloudflare DNS/Subdomain -> Cloudflare Tunnel -> localhost:5050 (pgAdmin)
App/API -> postgres:5432 (internal container network)
```

## Luong truy cap khong nen dung

```text
Internet -> PostgreSQL host port 15432
```

## Ghi chu van hanh

- Neu chi muon public app, bo dong `pgadmin.example.com`.
- Neu chi muon public pgAdmin tam thoi, bo dong `db.datac.click`.
- Neu dua vao production noi bo, uu tien bat Cloudflare Access/Zero Trust cho subdomain pgAdmin.
