# VeSimple - Docker Compose cho CasaOS

App dùng DB cố định (Supabase) — kết nối từ `config.json` mount vào container.

## File cần upload (4 thứ)

Đặt cùng thư mục `/DATA/AppData/vesimple/` trên CasaOS:

```
docker-compose.yml       ← file này
.env                     ← VESIMPLE_PORT=3333
config.json              ← BẮT BUỘC, copy từ local (chứa Supabase connection string)
static/                  ← thư mục (kể cả rỗng + file .gitkeep)
└── qr/
    └── .gitkeep         ← để đảm bảo Docker không nhầm thành file
```

## Bước 1: Upload

```bash
scp docker-compose.yml .env config.json casa@<IP-CASAOS>:/DATA/AppData/vesimple/
ssh casa@<IP-CASAOS>
cd /DATA/AppData/vesimple
mkdir -p static/qr && touch static/qr/.gitkeep
```

Trong CasaOS UI → **Custom App** → trỏ vào thư mục này → Start.

## Bước 2: Đảm bảo `config.json` tồn tại

QUAN TRỌNG: nếu thiếu `config.json`, Docker sẽ tự tạo một **thư mục** tên `config.json` → app sẽ crash khi đọc file. Fix:

```bash
cd /DATA/AppData/vesimple
ls -la config.json    # phải là file, không phải dir
# Nếu là dir: rm -rf config.json && touch config.json
# Sau đó edit: nano config.json  (paste connection string)
```

Để chắc chắn, copy `config.json` từ local lên CasaOS (KHÔNG commit file này vào git).

## Bước 3: Khởi động

Qua CasaOS UI (Start) hoặc SSH:
```bash
cd /DATA/AppData/vesimple
docker compose up -d
docker logs -f veapp
```

App chạy ở `http://<IP-CasaOS>:<VESIMPLE_PORT>` (mặc định 3333).

## Bước 4: Init database (chỉ lần đầu, vì Supabase còn trống)

```bash
docker exec -it veapp python -c "from app import init_schema; init_schema()"
docker exec -it veapp python seed_data.py
```

## Lưu ý

- `config.json` mount `read-only` (`:ro`) — app đọc cố định, không ghi đè.
- File `config.json` không có trong git (đã untrack). Bạn tự copy thủ công lên CasaOS.
- Backup DB dùng Supabase dashboard của bạn.
- Nếu muốn dùng DB local thay Supabase: thêm 1 service `vepostgres` và đổi `dbUrl` trong `config.json` thành `postgresql://veuser:...@vepostgres:5432/vesimple`.
