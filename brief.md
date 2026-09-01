# VeSimple — Brief Dự Án

Hệ thống bán vé sự kiện với sơ đồ chỗ ngồi 3D, tích hợp thanh toán VietQR và dashboard quản trị.

---

## 1. Tổng quan sản phẩm

| Mục | Giá trị |
|---|---|
| Tên dự án | VeSimple (Vé Simple) |
| Mục đích | Bán vé liveshow với giao diện 3D |
| Sự kiện hiện tại | SHOW ÂM NHẠC LIVE BAND: **9 GIỜ KÉM 15** |
| Ngày diễn | 17/10/2026 — 19:30 check-in, 20:45 showtime |
| Địa điểm | NHÀ HÁT NGÔI SAO, 87 Láng Hạ, Ba Đình, Hà Nội |
| Hotline | 0916206529 — ntn2906@gmail.com |
| Thời gian hold đơn | 30 phút |
| Stack | Python Flask + PostgreSQL + Three.js (vanilla JS) |

## 2. Nghiệp vụ (Business flow)

### Khách hàng
1. Vào `/` xem sơ đồ 3D khán phòng (xoay, zoom, click từng hạng vé).
2. Click tier → modal chọn số lượng → thêm vào giỏ (lưu session Flask).
3. Bấm checkout → điền họ tên + SĐT + email.
4. Hệ thống tạo đơn (`pending_payment`), generate VietQR (Shinhan Bank 970424, STK 0988358941, chủ TK BUI TUAN DUY), số tiền = tổng đơn, nội dung = mã đơn.
5. Khách quét QR chuyển khoản → admin xác nhận → đơn chuyển sang `paid`.
6. Admin gán ghế cụ thể trên sơ đồ 3D → đơn sang `assigned`.

### Admin
- `/admin` — đăng nhập bằng password (mặc định `admin123`).
- `/admin/dashboard` — danh sách đơn + thống kê từng hạng vé + sơ đồ 3D gán ghế.
- API admin: list orders, mark-paid, cancel, assign-seats.

## 3. Hạng vé & Sơ đồ

4 hạng (định nghĩa trong `seed_data.py` + `layout.json`):

| Tier ID | Tên | Giá (VNĐ) | Màu |
|---|---|---|---|
| `VIP` | Hạng Nở Hoa | 400.000 | `#f59e0b` vàng |
| `NEAR_VIP` | Hạng Thức Tỉnh | 350.000 | `#ef4444` đỏ |
| `STANDARD` | Hạng Thanh Xuân | 300.000 | `#3b82f6` xanh dương |
| `LAST_ROW` | Hạng Tích Tắc | 250.000 | `#ec4899` hồng |

Sơ đồ 272 ghế:
- **Trung tâm**: hàng C1–C9 (28 ghế VIP, 72 ghế NEAR_VIP). C7–C9 có split (gap 2.2).
- **Cánh trái**: L1–L10 (74 ghế, NEAR_VIP + STANDARD + LAST_ROW).
- **Cánh phải**: R1–R10 đối xứng trái.

Vị trí 3D: `pos_x`, `pos_z`, `rot_y`, hàng wing xoay ±0.28 rad.

## 4. Cơ sở dữ liệu (PostgreSQL)

3 bảng, tất cả prefix `9hkem15_` (bắt đầu bằng số → **phải quote** trong mọi query):

### `"9hkem15_tiers"`
```
id TEXT PK, name TEXT, description TEXT, price BIGINT, color TEXT, sort_order INT
```

### `"9hkem15_seats"`
```
id BIGSERIAL PK, code TEXT UNIQUE, tier_id TEXT FK→tiers, row_id TEXT,
pos_x REAL, pos_z REAL, rot_y REAL, side TEXT,
status TEXT CHECK ('available'|'held'|'assigned'),
order_id BIGINT FK→orders (ON DELETE SET NULL),
updated_at TIMESTAMPTZ
```
Indexes: `status`, `tier_id`, `order_id`.

### `"9hkem15_orders"`
```
id BIGSERIAL PK, code TEXT UNIQUE, full_name TEXT, phone TEXT, email TEXT,
total BIGINT, status TEXT CHECK ('pending_payment'|'paid'|'cancelled'|'assigned'),
items JSONB, note TEXT,
created_at TIMESTAMPTZ, paid_at TIMESTAMPTZ, assigned_at TIMESTAMPTZ
```
Index: `status`.

**Format seat code** (phải khớp frontend ↔ backend):
```
{tier_id.substring(0,4)}_{row_id}_{seat_number_padded_2}
```
Ví dụ: `VIP__C1_01`, `NEAR_C2_03`, `LAST_L10_08`.

## 5. Cấu trúc thư mục

```
VeSimple/
├── app.py                    # Flask app, routes, cart logic
├── config.json               # DB url, admin pass, VietQR, event info, Resend
├── layout.json               # Định nghĩa hàng ghế (rows × seats × position)
├── schema.sql                # CREATE TABLE cho 3 bảng
├── seed_data.py              # INSERT tiers + seats (dùng layout.json)
├── requirements.txt          # Flask, psycopg2-binary, Werkzeug, requests
├── AGENTS.md                 # Quy tắc dev + quirks (đọc trước khi sửa)
│
├── services/                 # Business logic
│   ├── __init__.py
│   ├── db.py                 # Pool psycopg2, query/execute, init_schema
│   ├── tiers.py              # get_all_tiers, get_tier_stats
│   ├── seats.py              # get_seats, hold/release/assign
│   ├── orders.py             # create_order, get_order, update_status
│   ├── vietqr.py             # Sinh URL ảnh QR (Quick Link)
│   ├── auth.py               # SHA256 admin password + session
│   └── email_service.py      # STUB — chưa implement (Resend)
│
├── utils/
│   ├── __init__.py
│   └── order_code.py         # Sinh mã đơn: GK15-YYMMDD-XXXX
│
├── templates/                # Jinja2
│   ├── index.html            # 3D chart + cart + checkout modal (535 dòng)
│   ├── admin.html            # Dashboard + seat assignment (523 dòng)
│   ├── admin_login.html      # Form login admin
│   └── (khác nếu có)
│
├── static/
│   └── qr/                   # Cache ảnh QR đã generate (tránh gọi lại API)
│
├── 3d_seating_chart.html     # Standalone 3D chart (không dùng qua Flask)
├── banner.jpg, banner_ngang.png  # Assets trang
│
└── venv/                     # Python virtualenv (KHÔNG commit, tạo lại khi move)
```

## 6. API Endpoints

### Public
| Method | URL | Mục đích |
|---|---|---|
| GET | `/` | Trang chủ 3D chart |
| GET | `/api/tiers` | Danh sách hạng vé |
| GET | `/api/seats` | Map seat_code → {tier_id, row_id, pos_x, pos_z, rot_y, status} |
| GET | `/api/cart` | Lấy cart hiện tại |
| POST | `/api/cart` | Thêm `{tier_id, qty}` |
| POST | `/api/cart/clear` | Xóa cart |
| POST | `/api/checkout` | Tạo order, trả QR URL |
| GET | `/api/orders/<code>` | Tra cứu đơn |
| POST | `/api/orders/<id>/pay` | Khách tự đánh dấu đã trả |

### Admin (cần session `_admin_authenticated`)
| Method | URL | Mục đích |
|---|---|---|
| GET | `/admin` | Login form |
| POST | `/admin/login` | Submit password |
| GET | `/admin/logout` | Đăng xuất |
| GET | `/admin/dashboard` | Trang dashboard |
| GET | `/admin/api/orders` | List tất cả orders |
| POST | `/admin/api/orders/<id>/assign` | Gán seat codes cho order |
| POST | `/admin/api/orders/<id>/mark-paid` | Duyệt thanh toán |
| POST | `/admin/api/orders/<id>/cancel` | Hủy order |

### Static
`/static/<path>` → `static/`

## 7. Cấu hình (`config.json`)

```json
{
  "dbUrl": "postgresql://USER:PASS@HOST:PORT/DB",
  "adminPass": "admin123",
  "sessionSecret": "chuỗi-bí-mật-flask",
  "vietqr": {
    "bankBin": "970424",
    "bankName": "Shinhan Bank",
    "accountNo": "0988358941",
    "accountName": "BUI TUAN DUY",
    "template": "compact"
  },
  "resend": {
    "apiKey": "re_xxx",
    "from": "9 GIO KEM 15 <onboarding@resend.dev>"
  },
  "event": {
    "name": "SHOW ÂM NHẠC LIVE BAND: 9 GIỜ KÉM 15",
    "date": "17/10/2026",
    "checkinTime": "19:30",
    "showTime": "20:45",
    "venue": "NHÀ HÁT NGÔI SAO",
    "address": "87 Láng Hạ, Ba Đình, Hà Nội",
    "mapsQuery": "Nhà hát Ngôi Sao 87 Láng Hạ Hà Nội",
    "hotline": "0916206529",
    "email": "ntn2906@gmail.com",
    "holdMinutes": 30
  }
}
```

Env override: `DATABASE_URL` nếu set sẽ thắng `config.json['dbUrl']`.

## 8. Cách move dự án sang máy khác

### Bước 1 — Copy code
Copy toàn bộ thư mục NGOẠI TRỪ:
- `venv/` (tạo lại)
- `static/qr/*.png` (cache, sẽ tự sinh lại)
- `__pycache__/` (Python tự tạo)
- `test_qr.png`, `test_qr2.png` (file test tạm)

### Bước 2 — Python & dependencies
Yêu cầu Python ≥ 3.10. Tại thư mục dự án:
```bash
python -m venv venv
# Windows
venv\Scripts\python -m pip install -r requirements.txt
# Linux/macOS
venv/bin/pip install -r requirements.txt
```

### Bước 3 — Database
Có 2 lựa chọn:

**(a) Dùng lại Supabase hiện tại** — chỉ cần giữ `dbUrl` trong `config.json`. Chạy:
```bash
venv\Scripts\python -c "from app import init_schema; init_schema()"
venv\Scripts\python seed_data.py
```

**(b) Local PostgreSQL** — tạo DB mới, sửa `dbUrl`:
```
postgresql://USER:PASS@localhost:5432/vesimple
```
Rồi chạy schema + seed như trên.

### Bước 4 — Chạy server
```bash
venv\Scripts\python app.py
# Mặc định 0.0.0.0:3333, debug=True
```

Truy cập:
- `http://127.0.0.1:3333/` — mua vé
- `http://127.0.0.1:3333/admin` — admin (pass mặc định `admin123`)

### Bước 5 — Secrets cần đổi
- `adminPass` trong `config.json`
- `sessionSecret` trong `config.json`
- `resend.apiKey` (khi implement email)
- `vietqr.accountNo` / `accountName` (nếu dùng tài khoản khác)

## 9. Quirks quan trọng (từ AGENTS.md)

1. **Quote tên bảng** — `9hkem15_` bắt đầu bằng số, luôn dùng `"9hkem15_xxx"` trong SQL.
2. **Seat code format** — frontend tạo bằng `tier.substring(0,4) + '_' + row_id + '_' + String(i+1).padStart(2,'0')`. Backend `seed_data.py` dùng `tier[:4]`. Phải khớp để admin gán ghế tìm thấy.
3. **VietQR URL** — Template nằm trong **path**, không phải query:
   `https://img.vietqr.io/image/{bankBin}-{accountNo}-{template}.png?amount=&addInfo=&accountName=`
4. **Cart key** — Flask session key `gk15_cart`.
5. **Admin auth** — SHA256 hash password, so sánh với session key `_admin_authenticated`.
6. **Email service** — hiện là stub `NotImplementedError`. Cần implement Resend API.

## 10. Trạng thái kỹ thuật hiện tại

| Thành phần | Trạng thái |
|---|---|
| 3D chart (Three.js) | ✅ Hoạt động, hiển thị 272 ghế, click chọn |
| Cart + checkout | ✅ Session-based, tạo order OK |
| VietQR generation | ✅ Đã fix (template trong path), cache tại `static/qr/` |
| Admin login + dashboard | ✅ Có đầy đủ |
| Order status flow | ✅ pending_payment → paid → assigned |
| Email service | ❌ Stub (chưa implement Resend) |
| Auto-release hold 30 phút | ❌ Chưa có cron (config có `holdMinutes: 30` nhưng không dùng) |
| Webhook thanh toán | ❌ Khách tự báo "đã trả" hoặc admin duyệt tay |
| Production WSGI | ❌ Dùng Flask dev server |

## 11. Test nhanh sau khi move

```bash
# Python syntax
python -m py_compile app.py services/*.py utils/*.py

# Database
python -c "from app import init_schema; init_schema()"
python seed_data.py
# Kỳ vọng: "Seeded 272 seats across 4 tiers"

# Server up + endpoints
curl http://127.0.0.1:3333/api/tiers
curl http://127.0.0.1:3333/api/seats | python -c "import sys,json; d=json.load(sys.stdin); print(len(d),'seats')"
```

## 12. Liên hệ / Người sở hữu

- Hotline: **0916206529**
- Email: **ntn2906@gmail.com**
- Project key trong DB: `9hkem15` (= "9 giờ kém 15")
- Order code prefix: `GK15-`