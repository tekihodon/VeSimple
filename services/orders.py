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

def assign_seats_to_order(order_id, seat_codes):
    assign_seats(order_id, seat_codes)
    update_order_status(order_id, 'assigned')
    order = get_order(order_id)
    return order

def mark_paid(order_id):
    update_order_status(order_id, 'paid')
    return get_order(order_id)

def cancel_order(order_id):
    update_order_status(order_id, 'cancelled')
    return get_order(order_id)