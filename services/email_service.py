import resend
from datetime import datetime
import json


def _event(config):
    e = config.get('event', {}) or {}
    return {
        'name': e.get('name', 'LIVESHOW 9 GIỜ KÉM 15'),
        'date': e.get('date', '17/10/2026'),
        'checkin': e.get('checkinTime', '19:00'),
        'show_time': e.get('showTime', '20:00'),
        'venue': e.get('venue', 'NHÀ HÁT NGÔI SAO'),
        'address': e.get('address', '87 Láng Hạ, Ba Đình, Hà Nội'),
        'hotline': e.get('hotline', '0916206529'),
        'email': e.get('email', ''),
        'support_name': e.get('supportName', 'BTC 9 Giờ Kém 15'),
    }


def _seats_by_tier(seats):
    grouped = {}
    for s in seats:
        tid = s['tier_id']
        grouped.setdefault(tid, []).append(s)
    return grouped


def _render_seats_html(seats_by_tier, tiers_map):
    out = []
    for tid, tier_seats in seats_by_tier.items():
        info = tiers_map.get(tid, {})
        name = info.get('name', tid)
        price = info.get('price', 0)
        chips = ''.join(f'<span class="seat-badge">{s["code"]}</span>' for s in tier_seats)
        out.append(f'<div class="tier-block"><div class="tier-name">{name} <span class="tier-price">{price:,}đ/ghế</span></div><div class="seat-row">{chips}</div></div>')
    return '\n'.join(out)


def _base_html(config, title_color='#0f172a', title_bg='linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'):
    ev = _event(config)
    return f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif; background: #f1f5f9; margin: 0; padding: 24px; color: #0f172a; }}
  .ticket-wrap {{ max-width: 620px; margin: 0 auto; background: #ffffff; border-radius: 16px; overflow: hidden; box-shadow: 0 8px 24px rgba(15,23,42,0.12); border: 1px solid #e2e8f0; }}
  .header {{ background: {title_bg}; padding: 28px 24px; text-align: center; }}
  .header h1 {{ margin: 0; font-size: 24px; color: {title_color}; font-weight: 800; letter-spacing: 1px; }}
  .header .subtitle {{ margin: 8px 0 0; font-size: 14px; color: {title_color}; opacity: 0.9; font-weight: 600; }}
  .alert {{ padding: 18px 24px; text-align: center; font-weight: 800; font-size: 18px; color: #ffffff; letter-spacing: 0.5px; }}
  .alert-success {{ background: #059669; }}
  .alert-warning {{ background: #d97706; }}
  .alert-danger {{ background: #dc2626; }}
  .alert-info {{ background: #2563eb; }}
  .event-info {{ padding: 24px; background: #f8fafc; border-bottom: 1px solid #e2e8f0; }}
  .event-info .row {{ display: flex; justify-content: space-between; margin-bottom: 10px; font-size: 15px; line-height: 1.5; }}
  .event-info .row:last-child {{ margin-bottom: 0; }}
  .event-info .label {{ color: #475569; font-weight: 500; }}
  .event-info .value {{ color: #0f172a; font-weight: 700; text-align: right; }}
  .order-info {{ padding: 24px; background: #fff7ed; border-bottom: 1px solid #fed7aa; text-align: center; }}
  .order-info .code-label {{ font-size: 12px; color: #92400e; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 700; margin-bottom: 4px; }}
  .order-info .code {{ font-size: 32px; font-weight: 900; color: #c2410c; letter-spacing: 3px; margin-bottom: 14px; }}
  .order-info .name {{ font-size: 20px; font-weight: 700; color: #0f172a; margin-bottom: 6px; }}
  .order-info .phone {{ font-size: 14px; color: #57534e; font-weight: 500; }}
  .seats-section {{ padding: 24px; }}
  .seats-section h3 {{ font-size: 14px; color: #0f172a; text-transform: uppercase; letter-spacing: 1.5px; margin: 0 0 18px; font-weight: 800; padding-bottom: 10px; border-bottom: 2px solid #f59e0b; }}
  .tier-block {{ margin-bottom: 20px; }}
  .tier-block:last-child {{ margin-bottom: 0; }}
  .tier-name {{ font-size: 15px; font-weight: 700; color: #0f172a; margin-bottom: 10px; }}
  .tier-name .tier-price {{ font-size: 13px; color: #78716c; font-weight: 600; margin-left: 8px; }}
  .seat-row {{ display: flex; flex-wrap: wrap; gap: 8px; }}
  .seat-badge {{ background: #0f172a; color: #f59e0b; border: 2px solid #f59e0b; border-radius: 8px; padding: 7px 14px; font-size: 14px; font-weight: 800; letter-spacing: 0.5px; }}
  .old-seat-badge {{ background: #fef2f2; color: #b91c1c; border: 2px solid #fca5a5; border-radius: 8px; padding: 7px 14px; font-size: 14px; font-weight: 700; text-decoration: line-through; }}
  .total-row {{ padding: 20px 24px; background: #f8fafc; border-top: 1px solid #e2e8f0; display: flex; justify-content: space-between; align-items: center; }}
  .total-label {{ font-size: 15px; color: #475569; font-weight: 600; }}
  .total-value {{ font-size: 26px; font-weight: 900; color: #059669; }}
  .support-box {{ padding: 20px 24px; background: #eff6ff; border-top: 1px solid #bfdbfe; }}
  .support-box .title {{ font-size: 13px; color: #1e40af; text-transform: uppercase; letter-spacing: 1.5px; font-weight: 800; margin-bottom: 10px; }}
  .support-row {{ display: flex; align-items: center; gap: 8px; font-size: 15px; color: #0f172a; margin-bottom: 6px; font-weight: 600; }}
  .support-row .icon {{ width: 24px; text-align: center; }}
  .footer {{ padding: 18px 24px; text-align: center; font-size: 12px; color: #64748b; background: #f1f5f9; border-top: 1px solid #e2e8f0; }}
  .footer strong {{ color: #0f172a; }}
  .change-box {{ margin: 0 24px 20px; padding: 16px; background: #fef3c7; border: 2px solid #f59e0b; border-radius: 10px; }}
  .change-box .change-title {{ font-size: 14px; font-weight: 800; color: #92400e; margin-bottom: 10px; text-transform: uppercase; letter-spacing: 1px; }}
  .change-box .old-seats {{ margin-bottom: 6px; font-size: 13px; color: #78716c; font-weight: 600; }}
  .change-box .old-seats-list {{ display: flex; flex-wrap: wrap; gap: 6px; margin-top: 4px; }}
</style>
</head><body>"""


def _footer_html(config):
    ev = _event(config)
    return f"""<div class="support-box">
    <div class="title">Hỗ trợ / Support</div>
    <div class="support-row"><span class="icon">👤</span> <span>{ev['support_name']}</span></div>
    <div class="support-row"><span class="icon">📞</span> <span>{ev['hotline']}</span></div>
    {f'<div class="support-row"><span class="icon">✉️</span> <span>{ev["email"]}</span></div>' if ev['email'] else ''}
  </div>
  <div class="footer">
    Mọi thắc mắc vui lòng liên hệ BTC theo thông tin phía trên.<br>
    Vé này là xác nhận chính thức cho đơn <strong>{'{ORDER_CODE}'}</strong> — giữ mã để đối chiếu khi check-in.
  </div>
</div>
</body></html>"""


def _common_event_info(ev):
    return f"""
  <div class="event-info">
    <div class="row"><span class="label">📍 Địa điểm</span><span class="value">{ev['venue']}</span></div>
    <div class="row"><span class="label">📍 Địa chỉ</span><span class="value" style="font-size:13px;">{ev['address']}</span></div>
    <div class="row"><span class="label">🕐 Check-in</span><span class="value">{ev['checkin']}</span></div>
    <div class="row"><span class="label">🎬 Show bắt đầu</span><span class="value">{ev['show_time']}</span></div>
  </div>
  <div class="order-info">
    <div class="code-label">Mã đơn hàng</div>
    <div class="code">{ev['_code']}</div>
    <div class="name">{ev['_name']}</div>
    <div class="phone">📱 {ev['_phone']}</div>
  </div>"""


def send_ticket_email(order, seats, config, kind='new', old_seats=None):
    """
    kind: 'new' (first send), 'reassign' (seats changed after first email)
    """
    api_key = config.get('resend', {}).get('apiKey')
    from_email = config.get('resend', {}).get('from', 'BTC 9hkem15 <admin@8keyslive.store>')
    ev = _event(config)

    items = order.get('items', [])
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            items = []

    tiers_map = {}
    for item in items:
        tid = item.get('tier') or item.get('tier_id')
        if tid:
            tiers_map[tid] = {'name': item.get('name', tid), 'price': int(item.get('price', 0))}

    seats_by_tier = _seats_by_tier(seats)
    ev['_code'] = order['code']
    ev['_name'] = order['full_name']
    ev['_phone'] = order['phone']

    if kind == 'reassign':
        alert_cls = 'alert-warning'
        alert_text = '⚠️ BTC THÔNG BÁO: BẠN ĐÃ ĐƯỢC XẾP GHẾ MỚI'
        title_bg = 'linear-gradient(135deg, #d97706 0%, #b45309 100%)'
        subject = f"⚠️ Cập nhật ghế mới – {ev['name']} ({ev['date']})"
        old_seats_html = ''
        if old_seats:
            old_codes = [s['code'] for s in old_seats] if old_seats and isinstance(old_seats[0], dict) else (old_seats if isinstance(old_seats, list) else [])
            if old_codes:
                old_chips = ''.join(f'<span class="old-seat-badge">{c}</span>' for c in old_codes)
                old_seats_html = f'<div class="change-box"><div class="change-title">Ghế cũ đã huỷ</div><div class="old-seats-list">{old_chips}</div></div>'
    else:
        alert_cls = 'alert-success'
        alert_text = '✓ VÉ CỦA BẠN – ĐÃ THANH TOÁN'
        title_bg = 'linear-gradient(135deg, #f59e0b 0%, #d97706 100%)'
        subject = f"🎫 Vé của bạn – {ev['name']} ({ev['date']})"
        old_seats_html = ''

    seats_html = _render_seats_html(seats_by_tier, tiers_map)
    common_info = _common_event_info(ev)

    html = _base_html(config, title_bg=title_bg)
    html += f'<div class="ticket-wrap">'
    html += f'<div class="header"><h1>🎵 {ev["name"]}</h1><div class="subtitle">{ev["date"]} • {ev["show_time"]} • {ev["venue"]}</div></div>'
    html += f'<div class="alert {alert_cls}">{alert_text}</div>'
    html += common_info
    html += old_seats_html
    html += f'<div class="seats-section"><h3>🎟 Ghế của bạn</h3>{seats_html}</div>'
    html += f'<div class="total-row"><span class="total-label">TỔNG CỘNG</span><span class="total-value">{int(order["total"]):,}đ</span></div>'
    html += _footer_html(config).replace('{ORDER_CODE}', order['code'])
    html = html.replace('{ORDER_CODE}', order['code'])

    if not api_key:
        return {'ok': False, 'error': 'Resend API key not configured'}

    try:
        resend.api_key = api_key
        resp = resend.Emails.send({
            "from": from_email,
            "to": order['email'],
            "subject": subject,
            "html": html,
        })
        if resp and resp.get('id'):
            from services.orders import mark_email_sent
            seat_codes = [s['code'] for s in seats]
            mark_email_sent(order['id'], seat_codes)
            return {'ok': True, 'email_id': resp['id']}
        return {'ok': False, 'error': 'No email ID returned'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def send_cancel_email(order, config, seats=None):
    """
    Email thông báo vé bị huỷ
    """
    api_key = config.get('resend', {}).get('apiKey')
    from_email = config.get('resend', {}).get('from', 'BTC 9hkem15 <admin@8keyslive.store>')
    ev = _event(config)
    ev['_code'] = order['code']
    ev['_name'] = order['full_name']
    ev['_phone'] = order['phone']

    items = order.get('items', [])
    if isinstance(items, str):
        try:
            items = json.loads(items)
        except Exception:
            items = []

    tiers_map = {}
    for item in items:
        tid = item.get('tier') or item.get('tier_id')
        if tid:
            tiers_map[tid] = {'name': item.get('name', tid), 'price': int(item.get('price', 0))}

    seats_html = ''
    if seats:
        seats_by_tier = _seats_by_tier(seats)
        seats_html = _render_seats_html(seats_by_tier, tiers_map)

    title_bg = 'linear-gradient(135deg, #b91c1c 0%, #7f1d1d 100%)'
    subject = f"❌ Vé bị huỷ – {ev['name']} ({ev['date']})"

    common_info = _common_event_info(ev)

    html = _base_html(config, title_bg=title_bg)
    html += f'<div class="ticket-wrap">'
    html += f'<div class="header"><h1>🎵 {ev["name"]}</h1><div class="subtitle">{ev["date"]} • {ev["show_time"]} • {ev["venue"]}</div></div>'
    html += f'<div class="alert alert-danger">❌ VÉ CỦA BẠN ĐÃ BỊ HUỶ</div>'
    html += common_info
    if seats_html:
        html += f'<div class="seats-section"><h3>🎟 Ghế đã huỷ</h3>{seats_html}</div>'
    html += f'<div style="padding:20px 24px;background:#fef2f2;border-top:1px solid #fecaca;"><div style="font-size:15px;color:#7f1d1d;font-weight:700;line-height:1.6;">Đơn hàng <strong>{order["code"]}</strong> của bạn đã bị BTC huỷ. Nếu bạn đã thanh toán, BTC sẽ liên hệ để hoàn tiền trong thời gian sớm nhất. Vui lòng liên hệ support nếu có thắc mắc.</div></div>'
    html += _footer_html(config).replace('{ORDER_CODE}', order['code'])
    html = html.replace('{ORDER_CODE}', order['code'])

    if not api_key:
        return {'ok': False, 'error': 'Resend API key not configured'}

    try:
        resend.api_key = api_key
        resp = resend.Emails.send({
            "from": from_email,
            "to": order['email'],
            "subject": subject,
            "html": html,
        })
        if resp and resp.get('id'):
            return {'ok': True, 'email_id': resp['id']}
        return {'ok': False, 'error': 'No email ID returned'}
    except Exception as e:
        return {'ok': False, 'error': str(e)}


def send_order_confirmation(email, order, seats, config):
    return send_ticket_email(order, seats, config, kind='new')


def send_seat_assignment(email, order, seats, config):
    return send_ticket_email(order, seats, config, kind='reassign')
