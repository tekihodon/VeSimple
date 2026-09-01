# AGENTS.md - VeSimple Ticket System

## Critical Entry Point & Setup

**Run the application:**
```bash
# Install dependencies (usually done once)
pip install -r requirements.txt

# Initialize database schema
python -c "from app import init_schema; init_schema()"

# Seed initial data (run once)
python seed_data.py

# Run the Flask server (port 3333)
python app.py
```

## High-Signal Architecture Quirks

### Database Table Names - **MUST QUOTE**
All tables start with `9hkem15_` (digit), which PostgreSQL requires quoting:
```python
# WRONG - will fail
execute("INSERT INTO 9hkem15_orders ...", ...)

# CORRECT - use quotes
execute('INSERT INTO "9hkem15_orders" ...', ...)
```

**Affected files:** `services/*.py` (orders.py, seats.py, tiers.py, etc.)

### Seat Code Format - FRONTEND/BACKEND MISMATCH
The 3D chart seat codes must match exactly between frontend generation and database storage:

**FIXED in templates/index.html:**
```javascript
buildSeatMesh(r.tier, x, r.z + (x*x*0.008), -x*0.015, 
    r.tier.id.substring(0,4) + '_' + r.id + '_' + 
    String(i+1).padStart(2,'0'))
```

**NEEDS SAME FIX in templates/admin.html:**
```javascript
// Replace ${i+1:02d} with String(i+1).padStart(2,'0')
```

### VietQR Payment Integration
Payment QR URLs follow this pattern:
```javascript
GET https://img.vietqr.io/img/{bankBin}-{accountNo}.png
    ?amount={total}
    &addInfo={orderCode}
    &accountName={accountName.replace(' ', '%20')}
    &template={template}
```

From `config.json`:
```json
"vietqr": {
  "bankBin": "970424",
  "bankName": "Shinhan Bank", 
  "accountNo": "0988358941",
  "accountName": "BUI TUAN DUY",
  "template": "compact"
}
```

## Core APIs & Their Purposes

### Public APIs (Frontend Communication)
- `GET /api/tiers` - Get ticket tier definitions
- `GET /api/seats` - Fetch seats data for 3D chart rendering
- `POST /api/cart` - Add item to shopping cart
- `GET /api/cart` - Get current cart contents
- `POST /api/checkout` - Create order + generate payment QR
- `POST /api/orders/<code>/pay` - Mark order as paid

### Admin APIs (Protected)
- `GET /admin/api/orders` - Get all orders for admin dashboard
- `POST /admin/api/orders/<id>/assign` - Assign specific seats to orders
- `POST /admin/api/orders/<id>/mark-paid` - Approve payment
- `POST /admin/api/orders/<id>/cancel` - Cancel order

## Session Management

### Cart Storage
```python
# Cart key for Flask session
CART_KEY = 'gk15_cart'
```

### Admin Authentication
```python
# Admin session key  
ADMIN_SESSION_KEY = '_admin_authenticated'

# Check: session[ADMIN_SESSION_KEY] == hash_password(config['adminPass'])
```

## Seat Assignment Flow

1. **Customer selects seats** → Frontend chart click updates `cartState`
2. **Checkout creates order** → `api/checkout` endpoint
3. **Admin approves** → `/admin/api/orders/<id>/assign` with seat codes
4. **Seats marked assigned** → Database updated, customer notified

## File Structure & Entry Points

### Frontend
- `templates/index.html` - Main ticket purchasing page with 3D chart
- `templates/admin.html` - Admin dashboard with seat assignment tool
- `3d_seating_chart.html` - Standalone 3D chart (if used separately)

### Backend
- `app.py` - Flask application with all route definitions
- `services/` - Business logic modules
- `templates/` - HTML views rendered by Flask

### Data
- `schema.sql` - PostgreSQL schema (tables prefixed with "9hkem15_")
- `seed_data.py` - Initial data population
- `config.json` - Configuration (database, payment, event details)

## Critical Testing Commands

```bash
# Check Python syntax
python -m py_compile app.py services/*.py

# Check JS syntax in templates  
for f in templates/*.html; do
    node -e "fs.readFileSync('$f', 'utf8')" 2>/dev/null
    [ $? -eq 0 ] || echo "Syntax issue in: $f"
done
```

## Common Pitfalls & Gotchas

1. **SQL quoting:** Forgetting quotes on `9hkem15_` tables causes database errors
2. **Seat codes:** Format mismatch breaks seat assignment flow
3. **QR caching:** Order codes must be unique for cache lookup
4. **Admin auth:** Password comparison vs. plaintext comparison
5. **Email service:** Currently stubbed - implement Resend API integration

## Environment Variables

```bash
DATABASE_URL=postgresql://postgres.fxwmdpxlxlhktitrusnq:123!PhamDinhDuc@aws-0-ap-southeast-1.pooler.supabase.com:6543/postgres
```

If not set, system falls back to `config.json['dbUrl']`.

## Generated Code Warning

The 3D chart uses Three.js with real-time seat generation. Seat codes are concatenated:
```javascript
tier_id + '_' + row_id + '_' + seat_number
```

Match this format exactly between frontend generation and database storage.

## graphify

This project has a knowledge graph at graphify-out/ with god nodes, community structure, and cross-file relationships.

When the user types `/graphify`, use the installed graphify skill or instructions before doing anything else.

Rules:
- For codebase questions, first run `graphify query "<question>"` when graphify-out/graph.json exists. Use `graphify path "<A>" "<B>"` for relationships and `graphify explain "<concept>"` for focused concepts. These return a scoped subgraph, usually much smaller than GRAPH_REPORT.md or raw grep output.
- Dirty graphify-out/ files are expected after hooks or incremental updates; dirty graph files are not a reason to skip graphify. Only skip graphify if the task is about stale or incorrect graph output, or the user explicitly says not to use it.
- If graphify-out/wiki/index.md exists, use it for broad navigation instead of raw source browsing.
- Read graphify-out/GRAPH_REPORT.md only for broad architecture review or when query/path/explain do not surface enough context.
- After modifying code, run `graphify update .` to keep the graph current (AST-only, no API cost).

## Versioning & Release Workflow

**Mỗi lần user nói "commit" / "release" / "đẩy code" / "lên docker" → BẮT BUỘC tăng version trong `version.json` theo SemVer (mặc định patch `X.Y.Z` → `X.Y.(Z+1)`) trước khi commit.** Xem chi tiết trong skill `.kilo/skills/commit-release/SKILL.md`.

### Remote & Registry
- **GitHub repo:** `https://github.com/tekihodon/VeSimple` (default branch: `main`)
- **Docker Hub image:** `tekihodon/vesimple` — luôn push 2 tags: `<version>` và `latest`
- **Trigger skill:** dùng skill `commit-release` để tự động bump + commit + tag + push + build & push docker image

### Quick commands
```bash
VERSION=$(jq -r .version version.json)
git add -A && git commit -m "v$VERSION: <mô tả>"
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin main && git push origin "v$VERSION"
docker build -t tekihodon/vesimple:$VERSION -t tekihodon/vesimple:latest -f Dockerfile .
docker push tekihodon/vesimple:$VERSION
docker push tekihodon/vesimple:latest
```
