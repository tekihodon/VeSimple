from flask import Flask, request, jsonify, session, render_template, redirect, url_for, send_from_directory, abort
import os
import json

from services.db import get_config, get_pool, init_schema
from services.tiers import get_all_tiers, get_tier_stats
from services.seats import get_seats, get_seats_for_chart, assign_seats, get_seats_overview
from services.orders import (
    create_order, get_order, get_pending_orders, get_all_orders,
    assign_seats_to_order, reassign_seats_to_order, mark_paid, cancel_order,
    restore_order, edit_order, delete_orders, validate_seats_for_items,
    get_stats, unpay_order, get_order_seats_with_tiers
)
from services.vietqr import get_or_generate_qr, get_vietqr_url
from services.auth import login_admin, logout_admin, admin_required, check_admin_auth
from services.email_service import send_order_confirmation

app = Flask(__name__, template_folder='templates', static_folder='static')
config = get_config()
app.secret_key = config.get('sessionSecret', 'gk15-9h45-secret-2026-10-17-liveshow')

@app.template_filter('currency')
def currency_filter(value):
    if value is None:
        return '0 đ'
    try:
        n = int(value)
        formatted = f"{n:,}".replace(',', '.')
        return formatted + ' đ'
    except (ValueError, TypeError):
        return '0 đ'

@app.template_filter('number')
def number_filter(value):
    if value is None:
        return '0'
    try:
        return f"{int(value):,}".replace(',', ' ')
    except (ValueError, TypeError):
        return '0'

def get_version():
    try:
        with open(os.path.join(app.root_path, 'version.json'), encoding='utf-8') as f:
            data = json.load(f)
            return data.get('version', 'unknown')
    except (OSError, ValueError):
        return 'unknown'

CART_KEY = 'gk15_cart'

init_schema()

def cart():
    return session.get(CART_KEY, {})

def cart_total():
    c = cart()
    tiers = {t['id']: t for t in get_all_tiers()}
    total = 0
    count = 0
    for t_id, qty in c.items():
        if t_id in tiers:
            total += tiers[t_id]['price'] * qty
            count += qty
    return total, count

def cart_items():
    c = cart()
    tiers = {t['id']: t for t in get_all_tiers()}
    items = []
    for t_id, qty in c.items():
        if t_id in tiers:
            items.append({'tier': t_id, 'name': tiers[t_id]['name'], 'price': tiers[t_id]['price'], 'qty': qty})
    return items

@app.route('/')
def index():
    return render_template('index.html',
                           config=config,
                           event=config.get('event', {}),
                           show=config.get('show', {}),
                           tiers=get_all_tiers(),
                           version=get_version())

@app.route('/api/tiers')
def api_tiers():
    return jsonify(get_tier_stats())

@app.route('/api/seats')
def api_seats():
    seats = get_seats_for_chart()
    return jsonify(seats)

@app.route('/api/version')
def api_version():
    try:
        with open(os.path.join(app.root_path, 'version.json'), encoding='utf-8') as f:
            return jsonify(json.load(f))
    except (OSError, ValueError):
        return jsonify({'version': 'unknown'})

@app.route('/api/cart', methods=['GET'])
def api_get_cart():
    total, count = cart_total()
    return jsonify({'items': cart_items(), 'total': total, 'count': count})

@app.route('/api/cart', methods=['POST'])
def api_add_to_cart():
    data = request.get_json()
    tier_id = data.get('tier_id')
    qty = int(data.get('qty', 1))
    if tier_id not in {t['id'] for t in get_all_tiers()}:
        return jsonify({'error': 'Invalid tier'}), 400
    c = cart()
    c[tier_id] = c.get(tier_id, 0) + qty
    session[CART_KEY] = c
    total, count = cart_total()
    return jsonify({'ok': True, 'total': total, 'count': count})

@app.route('/api/cart/clear', methods=['POST'])
def api_clear_cart():
    session.pop(CART_KEY, None)
    return jsonify({'ok': True})

@app.route('/api/checkout', methods=['POST'])
def api_checkout():
    data = request.get_json()
    full_name = data.get('full_name', '').strip()
    phone = data.get('phone', '').strip()
    email = data.get('email', '').strip()
    if not full_name or not phone or not email:
        return jsonify({'error': 'Vui lòng điền đầy đủ thông tin'}), 400
    items = cart_items()
    if not items:
        return jsonify({'error': 'Giỏ hàng đang trống'}), 400

    order = create_order(full_name, phone, email, items, config)
    session.pop(CART_KEY, None)

    qr_url = get_or_generate_qr(config, order['total'], order['code'])
    return jsonify({
        'ok': True,
        'order': {
            'id': order['id'],
            'code': order['code'],
            'total': order['total'],
            'full_name': order['full_name'],
            'phone': order['phone'],
            'email': order['email'],
            'items': order['items'],
            'status': order['status'],
        },
        'qr_url': qr_url,
        'qr_live': get_vietqr_url(config, order['total'], order['code'])
    })

@app.route('/api/orders/<code>')
def api_get_order(code):
    order = get_order(code=code)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    seats = get_seats(order_id=order['id'])
    return jsonify({'order': order, 'seats': seats})

@app.route('/admin')
def admin_login_page():
    if check_admin_auth(config):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html', config=config, version=get_version())

@app.route('/admin/login', methods=['POST'])
def admin_login():
    password = request.form.get('password', '')
    if login_admin(config, password):
        return redirect(url_for('admin_dashboard'))
    return render_template('admin_login.html', error='Sai mật khẩu', config=config, version=get_version())

@app.route('/admin/logout')
def admin_logout():
    logout_admin()
    return redirect(url_for('admin_login_page'))

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    orders = get_pending_orders()
    stats = get_tier_stats()
    return render_template('admin.html', config=config, orders=orders, tiers=stats, version=get_version())

@app.route('/admin/api/orders')
@admin_required
def admin_api_orders():
    orders = get_all_orders()
    return jsonify(orders)

@app.route('/admin/api/seats-overview')
@admin_required
def admin_api_seats_overview():
    return jsonify(get_seats_overview())

@app.route('/admin/api/stats')
@admin_required
def admin_api_stats():
    date_from = request.args.get('from') or None
    date_to = request.args.get('to') or None
    return jsonify(get_stats(date_from, date_to))

@app.route('/admin/api/orders/<int:order_id>/assign', methods=['POST'])
@admin_required
def admin_assign_seats(order_id):
    data = request.get_json()
    seat_codes = data.get('seats', [])
    order = get_order(order_id=order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order['status'] == 'cancelled':
        return jsonify({'ok': False, 'error': 'Đơn đã bị hủy, không thể phân ghế'}), 400
    items = order['items']
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except (ValueError, TypeError):
            items = []
    validation = validate_seats_for_items(seat_codes, items, current_order_id=order_id)
    if not validation.get('ok'):
        return jsonify(validation), 400
    if order['status'] == 'assigned':
        assigned = reassign_seats_to_order(order_id, seat_codes)
    else:
        assigned = assign_seats_to_order(order_id, seat_codes)
    return jsonify({'ok': True, 'order': assigned})

@app.route('/admin/api/orders/<int:order_id>/cancel', methods=['POST'])
@admin_required
def admin_cancel_order(order_id):
    order = cancel_order(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'ok': True, 'status': order['status']})

@app.route('/admin/api/orders/<int:order_id>/restore', methods=['POST'])
@admin_required
def admin_restore_order(order_id):
    order = restore_order(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'ok': True, 'status': order['status']})

@app.route('/admin/api/orders/<int:order_id>/edit', methods=['POST'])
@admin_required
def admin_edit_order(order_id):
    data = request.get_json(silent=True) or {}
    items = data.get('items')
    total = None
    if isinstance(items, list):
        total = sum(int(i.get('price', 0)) * int(i.get('qty', 0)) for i in items)
    order = edit_order(
        order_id,
        full_name=(data.get('full_name') or None),
        phone=(data.get('phone') or None),
        email=(data.get('email') or None),
        items=items,
        total=total,
    )
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'ok': True, 'order': order})

@app.route('/admin/api/orders/<int:order_id>/mark-paid', methods=['POST'])
@admin_required
def admin_mark_paid(order_id):
    order = mark_paid(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'ok': True, 'status': order['status']})

@app.route('/admin/api/orders/<int:order_id>/unpay', methods=['POST'])
@admin_required
def admin_unpay_order(order_id):
    order = unpay_order(order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    return jsonify({'ok': True, 'status': order['status']})

@app.route('/admin/api/orders/<int:order_id>/send-ticket', methods=['POST'])
@admin_required
def admin_send_ticket(order_id):
    from services.email_service import send_ticket_email
    order = get_order(order_id=order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order['status'] != 'assigned':
        return jsonify({'error': 'Chỉ gửi vé khi đã phân ghế xong'}), 400
    seats = get_order_seats_with_tiers(order_id)
    current_codes = sorted([s['code'] for s in seats])
    old_codes = sorted([c.strip() for c in (order.get('email_sent_seats') or '').split(',') if c.strip()])
    is_reassign = bool(order.get('email_sent_at')) and current_codes != old_codes
    if is_reassign:
        old_seats = [{'code': c} for c in old_codes]
        result = send_ticket_email(order, seats, config, kind='reassign', old_seats=old_seats)
    else:
        result = send_ticket_email(order, seats, config, kind='new')
    if result.get('ok'):
        return jsonify({'ok': True, 'kind': 'reassign' if is_reassign else 'new'})
    return jsonify({'ok': False, 'error': result.get('error', 'Lỗi gửi email')}), 500

@app.route('/admin/api/orders/<int:order_id>/send-cancel-email', methods=['POST'])
@admin_required
def admin_send_cancel_email(order_id):
    from services.email_service import send_cancel_email
    order = get_order(order_id=order_id)
    if not order:
        return jsonify({'error': 'Order not found'}), 404
    if order['status'] != 'cancelled':
        return jsonify({'error': 'Chỉ gửi mail huỷ khi đơn đã huỷ'}), 400
    seats = None
    try:
        seats = get_order_seats_with_tiers(order_id)
    except Exception:
        seats = None
    result = send_cancel_email(order, config, seats=seats)
    if result.get('ok'):
        return jsonify({'ok': True})
    return jsonify({'ok': False, 'error': result.get('error', 'Lỗi gửi email')}), 500

@app.route('/admin/api/orders/delete', methods=['POST'])
@admin_required
def admin_delete_orders():
    data = request.get_json(silent=True) or {}
    ids = data.get('ids') or []
    if not isinstance(ids, list) or not ids:
        return jsonify({'ok': False, 'error': 'Vui lòng chọn ít nhất 1 đơn'}), 400
    try:
        ids = [int(x) for x in ids]
    except (TypeError, ValueError):
        return jsonify({'ok': False, 'error': 'ID đơn không hợp lệ'}), 400
    deleted = delete_orders(ids)
    return jsonify({'ok': True, 'deleted': deleted})

@app.route('/admin/api/orders/<int:order_id>', methods=['DELETE'])
@admin_required
def admin_delete_order(order_id):
    deleted = delete_orders([order_id])
    if not deleted:
        return jsonify({'ok': False, 'error': 'Order not found'}), 404
    return jsonify({'ok': True, 'deleted': deleted})

@app.route('/static/<path:filename>')
def serve_static(filename):
    return send_from_directory(os.path.join(app.root_path, 'static'), filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3333, debug=True)