from .db import query, execute, execute_one

def get_seats(tier_id=None, status=None, order_id=None):
    sql = 'SELECT id, code, tier_id, row_id, pos_x, pos_z, rot_y, status, order_id FROM "9hkem15_seats" WHERE 1=1'
    params = []
    if tier_id:
        sql += ' AND tier_id = %s'
        params.append(tier_id)
    if status:
        sql += " AND status = %s"
        params.append(status)
    if order_id:
        sql += ' AND order_id = %s'
        params.append(order_id)
    return query(sql, params if params else None)

def get_seats_for_chart():
    seats = query('SELECT code, tier_id, row_id, pos_x, pos_z, rot_y, status FROM "9hkem15_seats" ORDER BY row_id, code')
    return {s['code']: s for s in seats}

def hold_seats(tier_id, qty, session_id):
    seats = query('''
        SELECT id, code FROM "9hkem15_seats"
        WHERE tier_id = %s AND status = 'available'
        LIMIT %s FOR UPDATE SKIP LOCKED
    ''', (tier_id, qty))
    if not seats or len(seats) < qty:
        available = query('SELECT COUNT(*) FROM "9hkem15_seats" WHERE tier_id = %s AND status = \'available\'', (tier_id,), one=True)
        raise ValueError(f"Không đủ ghế. Chỉ còn {available['count']} ghế {tier_id}.")
    seat_ids = [s['id'] for s in seats]
    execute('UPDATE "9hkem15_seats" SET status = \'held\', order_id = NULL WHERE id = ANY(%s)', (seat_ids,))
    return [s['code'] for s in seats]

def release_seats(codes):
    if not codes:
        return
    execute('UPDATE "9hkem15_seats" SET status = \'available\', order_id = NULL WHERE code = ANY(%s)', (codes,))

def assign_seats(order_id, codes):
    if not codes:
        return
    execute('UPDATE "9hkem15_seats" SET status = \'assigned\', order_id = %s WHERE code = ANY(%s)', (order_id, codes))

def get_seats_by_codes(codes):
    return query('SELECT * FROM "9hkem15_seats" WHERE code = ANY(%s)', (codes,))

def get_seats_overview():
    seats = query('''
        SELECT s.code, s.tier_id, s.row_id, s.status,
               o.code AS order_code, o.full_name AS customer_name
        FROM "9hkem15_seats" s
        LEFT JOIN "9hkem15_orders" o ON s.order_id = o.id
        ORDER BY s.row_id, s.code
    ''')
    return {s['code']: s for s in seats}