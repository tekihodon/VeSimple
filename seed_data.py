import json
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_URL = os.environ.get('DATABASE_URL') or json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'config.json'), encoding='utf-8'))['dbUrl']

import psycopg2

LAYOUT = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'layout.json'), encoding='utf-8'))

TIER_MAP = [
    {'id': 'VIP', 'name': 'Hạng Nở Hoa', 'description': 'A, B, C VIP', 'price': 400000, 'color': '#f59e0b', 'sort_order': 1},
    {'id': 'NEAR_VIP', 'name': 'Hạng Thức Tỉnh', 'description': 'Cận VIP', 'price': 350000, 'color': '#ef4444', 'sort_order': 2},
    {'id': 'STANDARD', 'name': 'Hạng Thanh Xuân', 'description': 'Tiêu Chuẩn', 'price': 300000, 'color': '#3b82f6', 'sort_order': 3},
    {'id': 'LAST_ROW', 'name': 'Hạng Tích Tắc', 'description': 'Hàng Cuối', 'price': 250000, 'color': '#ec4899', 'sort_order': 4},
]

def generate_seats():
    seats = []
    for row in LAYOUT['rows']:
        tier = row['tier']
        row_id = row['id']
        count = row['count']
        z = row['z']
        spacing = row['spacing']
        side = row['side']

        if row.get('split'):
            # Split row (center with gap)
            half = row['split']
            gap = row['gap']
            left_width = (half - 1) * spacing
            for i in range(half):
                local_x = -(gap / 2) - left_width + (i * spacing)
                x = local_x + (local_x * local_x * 0.008)
                rot_y = -local_x * 0.015
                code = f"{tier[:4]}_{row_id}_{i+1:02d}"
                seats.append((code, tier, row_id, round(x, 4), round(z, 4), round(rot_y, 4), 'center'))
            for i in range(half):
                local_x = (gap / 2) + (i * spacing)
                x = local_x + (local_x * local_x * 0.008)
                rot_y = -local_x * 0.015
                code = f"{tier[:4]}_{row_id}_{half + i + 1:02d}"
                seats.append((code, tier, row_id, round(x, 4), round(z, 4), round(rot_y, 4), 'center'))
        else:
            # Non-split row
            if side in ['left', 'right']:
                # Wing row - use wing positioning
                if side == 'left':
                    wing_start_x = -13.0 - (count * 0.4)
                    for i in range(count):
                        local_x = (i - count / 2) * spacing
                        x = wing_start_x + (local_x * math.cos(0.28))
                        z_pos = z - (local_x * math.sin(0.28))
                        code = f"{tier[:4]}_{row_id}_{i+1:02d}"
                        seats.append((code, tier, row_id, round(x, 4), round(z_pos, 4), round(0.28, 4), 'left'))
                else:  # side == 'right'
                    wing_start_x = 13.0 + (count * 0.4)
                    for i in range(count):
                        local_x = (i - count / 2) * spacing
                        x = wing_start_x + (local_x * math.cos(-0.28))
                        z_pos = z - (local_x * math.sin(-0.28))
                        code = f"{tier[:4]}_{row_id}_{i+1:02d}"
                        seats.append((code, tier, row_id, round(x, 4), round(z_pos, 4), round(-0.28, 4), 'right'))
            else:
                # Center row (no wings)
                total_width = (count - 1) * spacing
                for i in range(count):
                    local_x = -(total_width / 2) + (i * spacing)
                    x = local_x + (local_x * local_x * 0.008)
                    rot_y = -local_x * 0.015
                    code = f"{tier[:4]}_{row_id}_{i+1:02d}"
                    seats.append((code, tier, row_id, round(x, 4), round(z, 4), round(rot_y, 4), side))

    return seats

def seed():
    conn = psycopg2.connect(DB_URL)
    cur = conn.cursor()

    for t in TIER_MAP:
        cur.execute(
            "INSERT INTO \"9hkem15_tiers\" (id, name, description, price, color, sort_order) VALUES (%s,%s,%s,%s,%s,%s) ON CONFLICT (id) DO UPDATE SET name=EXCLUDED.name, description=EXCLUDED.description, price=EXCLUDED.price, color=EXCLUDED.color, sort_order=EXCLUDED.sort_order",
            (t['id'], t['name'], t['description'], t['price'], t['color'], t['sort_order'])
        )

    seats = generate_seats()
    for code, tier_id, row_id, pos_x, pos_z, rot_y, side in seats:
        cur.execute(
            "INSERT INTO \"9hkem15_seats\" (code, tier_id, row_id, pos_x, pos_z, rot_y, side, status) VALUES (%s,%s,%s,%s,%s,%s,%s,'available') ON CONFLICT (code) DO NOTHING",
            (code, tier_id, row_id, pos_x, pos_z, rot_y, side)
        )

    conn.commit()
    cur.close()
    conn.close()
    print(f"Seeded {len(seats)} seats across {len(TIER_MAP)} tiers")

if __name__ == '__main__':
    seed()