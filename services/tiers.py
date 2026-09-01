from .db import query, execute, execute_one

T = '"9hkem15_'

def get_all_tiers():
    return query(f'SELECT id, name, description, price, color, sort_order FROM {T}tiers" ORDER BY sort_order')

def get_tier(tier_id):
    return query(f'SELECT * FROM {T}tiers" WHERE id = %s', (tier_id,), one=True)

def get_tier_stats():
    return query(f'''
        SELECT t.id, t.name, t.price, t.color,
               COUNT(s.id) as total,
               COUNT(s.id) FILTER (WHERE s.status = 'available') as available,
               COUNT(s.id) FILTER (WHERE s.status = 'held') as held,
               COUNT(s.id) FILTER (WHERE s.status = 'assigned') as assigned
        FROM {T}tiers" t
        LEFT JOIN {T}seats" s ON s.tier_id = t.id
        GROUP BY t.id, t.name, t.price, t.color, t.sort_order
        ORDER BY t.sort_order
    ''')