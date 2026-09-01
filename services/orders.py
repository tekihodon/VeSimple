from .db import query, execute, execute_one
from .seats import assign_seats, release_seats
from datetime import datetime, timedelta
import json

def create_order(full_name, phone, email, items, config):
    from utils.order_code import generate_order_code
    order_code = generate_order_code(phone)
    total = sum(item['price'] * item['qty'] for item in items)

    order = execute_one("""
        INSERT INTO "9hkem15_orders" (code, full_name, phone, email, total, items, status)
        VALUES (%s, %s, %s, %s, %s, %s, 'pending_payment')
        RETURNING *
    """, (order_code, full_name, phone, email, total, json.dumps(items)))
    return order

def get_order(order_id=None, code=None):
    if order_id:
        return query("SELECT * FROM \"9hkem15_orders\" WHERE id = %s", (order_id,), one=True)
    if code:
        return query("SELECT * FROM \"9hkem15_orders\" WHERE code = %s", (code,), one=True)
    return None

def get_pending_orders():
    return query("""
        SELECT o.*,
               COALESCE(json_agg(json_build_object('code', s.code, 'tier_id', s.tier_id, 'row_id', s.row_id))
                         FILTER (WHERE s.code IS NOT NULL), '[]') as seats
        FROM "9hkem15_orders" o
        LEFT JOIN "9hkem15_seats" s ON s.order_id = o.id
        WHERE o.status IN ('pending_payment', 'paid')
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """)

def get_all_orders():
    return query("""
        SELECT o.*,
               COALESCE(json_agg(json_build_object('code', s.code, 'tier_id', s.tier_id, 'row_id', s.row_id))
                         FILTER (WHERE s.code IS NOT NULL), '[]') as seats
        FROM "9hkem15_orders" o
        LEFT JOIN "9hkem15_seats" s ON s.order_id = o.id
        GROUP BY o.id
        ORDER BY o.created_at DESC
    """)

def update_order_status(order_id, status):
    now = datetime.utcnow()
    if status == 'paid':
        execute("UPDATE \"9hkem15_orders\" SET status = %s, paid_at = %s WHERE id = %s", (status, now, order_id))
    elif status == 'assigned':
        execute("UPDATE \"9hkem15_orders\" SET status = %s, assigned_at = %s WHERE id = %s", (status, now, order_id))
    elif status == 'cancelled':
        order = get_order(order_id)
        if order:
            seats = query("SELECT code FROM \"9hkem15_seats\" WHERE order_id = %s", (order_id,))
            release_seats([s['code'] for s in seats])
        execute("UPDATE \"9hkem15_orders\" SET status = %s WHERE id = %s", (status, order_id))
    else:
        execute("UPDATE \"9hkem15_orders\" SET status = %s WHERE id = %s", (status, order_id))

def _release_order_seats(order_id):
    seats = query("SELECT code FROM \"9hkem15_seats\" WHERE order_id = %s", (order_id,))
    if seats:
        release_seats([s['code'] for s in seats])

def validate_seats_for_items(seat_codes, items):
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except (ValueError, TypeError):
            items = []
    required = {}
    for i in (items or []):
        t = i.get('tier') or i.get('tier_id')
        qty = int(i.get('qty', 0))
        if not t or qty <= 0:
            continue
        required[t] = required.get(t, 0) + qty
    if not required:
        return {'ok': False, 'error': 'Đơn không có hạng vé hợp lệ'}
    expected_total = sum(required.values())
    if len(seat_codes) != expected_total:
        return {'ok': False, 'error': f'Đơn cần đúng {expected_total} ghế (hiện chọn {len(seat_codes)})'}
    seats = query('SELECT code, tier_id, status FROM "9hkem15_seats" WHERE code = ANY(%s)', (list(seat_codes),))
    found = {s['code']: s for s in seats}
    missing = [c for c in seat_codes if c not in found]
    if missing:
        return {'ok': False, 'error': f'Ghế không tồn tại: {", ".join(missing[:5])}'}
    counts = {}
    for c in seat_codes:
        s = found[c]
        if s['status'] == 'assigned':
            counts_by_tier = query('SELECT order_id FROM "9hkem15_seats" WHERE code = %s', (c,), one=True)
            if not counts_by_tier or counts_by_tier.get('order_id') != getattr(validate_seats_for_items, '_current_order_id', None):
                return {'ok': False, 'error': f'Ghế {c} đã được phân cho đơn khác'}
        counts[s['tier_id']] = counts.get(s['tier_id'], 0) + 1
    for t, q in required.items():
        if counts.get(t, 0) != q:
            return {'ok': False, 'error': f'Cần {q} ghế hạng {t}, đang chọn {counts.get(t, 0)}'}
    for t in counts:
        if t not in required:
            return {'ok': False, 'error': f'Ghế hạng {t} không nằm trong đơn này'}
    return {'ok': True}

def assign_seats_to_order(order_id, seat_codes):
    _release_order_seats(order_id)
    assign_seats(order_id, seat_codes)
    update_order_status(order_id, 'assigned')
    order = get_order(order_id)
    return order

def reassign_seats_to_order(order_id, seat_codes):
    return assign_seats_to_order(order_id, seat_codes)

def mark_paid(order_id):
    update_order_status(order_id, 'paid')
    return get_order(order_id)

def cancel_order(order_id):
    update_order_status(order_id, 'cancelled')
    return get_order(order_id)

def restore_order(order_id):
    order = get_order(order_id)
    if not order:
        return None
    new_status = 'assigned' if order.get('assigned_at') else 'paid'
    update_order_status(order_id, new_status)
    return get_order(order_id)

def edit_order(order_id, full_name=None, phone=None, email=None, items=None, total=None):
    order = get_order(order_id)
    if not order:
        return None
    fields = []
    params = []
    if full_name is not None:
        fields.append('full_name = %s')
        params.append(full_name)
    if phone is not None:
        fields.append('phone = %s')
        params.append(phone)
    if email is not None:
        fields.append('email = %s')
        params.append(email)
    if items is not None:
        fields.append('items = %s')
        params.append(json.dumps(items))
    if total is not None:
        fields.append('total = %s')
        params.append(total)
    if items is not None:
        _release_order_seats(order_id)
        if order.get('status') == 'assigned':
            fields.append('status = %s')
            params.append('paid')
            fields.append('assigned_at = NULL')
    if not fields:
        return get_order(order_id)
    params.append(order_id)
    sql = f'UPDATE "9hkem15_orders" SET {", ".join(fields)} WHERE id = %s'
    execute(sql, params)
    return get_order(order_id)

def delete_orders(order_ids):
    if not order_ids:
        return 0
    seats = query('SELECT code FROM "9hkem15_seats" WHERE order_id = ANY(%s)', (list(order_ids),))
    if seats:
        release_seats([s['code'] for s in seats])
    execute('UPDATE "9hkem15_seats" SET order_id = NULL WHERE order_id = ANY(%s)', (list(order_ids),))
    return execute('DELETE FROM "9hkem15_orders" WHERE id = ANY(%s)', (list(order_ids),))

def get_stats(date_from=None, date_to=None):
    paid_clause = "status IN ('paid','assigned')"
    where = paid_clause
    params = []
    if date_from:
        where += ' AND created_at >= %s'
        params.append(f"{date_from} 00:00:00")
    if date_to:
        where += ' AND created_at <= %s'
        params.append(f"{date_to} 23:59:59")
    total_revenue = query(f"SELECT COALESCE(SUM(total),0) AS s FROM \"9hkem15_orders\" WHERE {where}", params, one=True)
    total_orders = query(f"SELECT COUNT(*) AS c FROM \"9hkem15_orders\" WHERE {where}", params, one=True)
    by_day = query(f"""
        SELECT TO_CHAR(created_at, 'YYYY-MM-DD') AS day,
               COALESCE(SUM(total),0) AS revenue,
               COUNT(*) AS orders
        FROM "9hkem15_orders"
        WHERE {where}
        GROUP BY 1
        ORDER BY 1
    """, params)
    seats_by_tier = query("""
        SELECT t.id, t.name, t.price, t.color,
               COALESCE(SUM((sub.i->>'qty')::int), 0) AS qty,
               COALESCE(SUM((sub.i->>'qty')::int * (sub.i->>'price')::int), 0) AS revenue
        FROM "9hkem15_tiers" t
        LEFT JOIN LATERAL (
            SELECT i
            FROM "9hkem15_orders" o, jsonb_array_elements(o.items) i
            WHERE o.id IS NOT NULL
              AND o.status IN ('paid','assigned')
              AND (i->>'tier') = t.id
              AND (%s::date IS NULL OR o.created_at >= %s::date)
              AND (%s::date IS NULL OR o.created_at < (%s::date + INTERVAL '1 day'))
        ) sub ON TRUE
        GROUP BY t.id, t.name, t.price, t.color, t.sort_order
        ORDER BY t.sort_order
    """, (date_from, date_from, date_to, date_to))
    return {
        'total_revenue': int(total_revenue['s'] or 0),
        'total_orders': int(total_orders['c'] or 0),
        'seats_by_tier': [{'id': r['id'], 'name': r['name'], 'price': int(r['price']), 'color': r['color'],
                           'qty': int(r['qty'] or 0), 'revenue': int(r['revenue'] or 0)} for r in seats_by_tier],
        'daily_revenue': [{'day': r['day'], 'revenue': int(r['revenue'] or 0), 'orders': int(r['orders'] or 0)} for r in by_day],
    }