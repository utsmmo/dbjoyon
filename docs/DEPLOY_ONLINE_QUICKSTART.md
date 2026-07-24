# Deploy Online Quickstart

Tai lieu nay dung cho truong hop anh/chị muon dua he thong len online nhanh qua Cloudflare Tunnel.

## Muc tieu

- Domain online: `data.datac.click`
- Domain nay se tro vao app/API
- PostgreSQL van private

## Kien truc

```text
Internet User / External Tool
-> https://data.datac.click
-> Cloudflare Tunnel
-> http://localhost:13000
-> app/API
-> PostgreSQL private
```

## Chay local truoc

```bash
docker compose up -d
```

Kiem tra:

- `http://localhost:13000/health`
- `http://localhost:13000/docs`
- `http://localhost:5050`
- PostgreSQL host port: `localhost:15432`

## Cloudflare Tunnel map domain

Thay vi `review.example.com`, anh/chị dung:

- `data.datac.click`

Lenh mau:

```bash
cloudflared tunnel login
cloudflared tunnel create hotel-review
cloudflared tunnel route dns hotel-review data.datac.click
```

## config.yml mau

```yaml
tunnel: YOUR_TUNNEL_ID
credentials-file: C:\Users\YOUR_USER\.cloudflared\YOUR_TUNNEL_ID.json

  ingress:
  - hostname: data.datac.click
    service: http://localhost:13000
  - service: http_status:404
```

## Ket qua

Sau khi chay:

```bash
cloudflared tunnel run hotel-review
```

Anh/chị co the dung:

- `https://data.datac.click/docs`
- `https://data.datac.click/health`
- `https://data.datac.click/api/v1/sync/reviews/booking`

## Luu y quan trong

- `data.datac.click` o day la domain cua app/API, khong phai port PostgreSQL
- Khong map domain nay vao `15432`
- Khong public PostgreSQL ra internet
