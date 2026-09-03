import resend
from datetime import datetime

def send_ticket_email(order, seats, config):
    api_key = config.get('resend', {}).get('apiKey')
    from_email = config.get('resend', {}).get('from', '9 GIO KEM 15 <onboarding@resend.dev>')
    event_name = config.get('event', {}).get('name', 'LIVESHOW 9 GIỜ KÉM 15')
    event_date = config.get('event', {}).get('date', '17/10/2026')
    event_time = config.get('event', {}).get('checkinTime', '19:00')
    event_venue = config.get('event', {}).get('venue', 'NHÀ HÁT NGÔI SAO')
    event_address = config.get('event', {}).get('address', '87 Láng Hạ, Ba Đình, Hà Nội')
    show_time = config.get('event', {}).get('showTime', '20:00')
    hotline = config.get('event', {}).get('hotline', '0916206529')

    items = order.get('items', [])
    if isinstance(items, str):
        import json
        try:
            items = json.loads(items)
        except Exception:
            items = []

    tiers_map = {}
    for item in items:
        tid = item.get('tier') or item.get('tier_id')
        if tid:
            tiers_map[tid] = {'name': item.get('name', tid), 'price': int(item.get('price', 0))}

    seats_by_tier = {}
    for seat in seats:
        tid = seat['tier_id']
        if tid not in seats_by_tier:
            seats_by_tier[tid] = []
        seats_by_tier[tid].append(seat)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ font-family: Arial, sans-serif; background: #0f172a; margin: 0; padding: 20px; color: #fff; }}
  .ticket-wrap {{ max-width: 600px; margin: 0 auto; background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%); border-radius: 16px; overflow: hidden; border: 1px solid rgba(245,158,11,0.3); }}
  .header {{ background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%); padding: 24px; text-align: center; }}
  .header h1 {{ margin: 0; font-size: 22px; color: #0f172a; font-weight: 800; letter-spacing: 1px; }}
  .header .subtitle {{ margin: 6px 0 0; font-size: 13px; color: #0f172a; opacity: 0.8; }}
  .event-info {{ padding: 20px 24px; border-bottom: 1px solid rgba(255,255,255,0.1); }}
  .event-info .row {{ display: flex; justify-content: space-between; margin-bottom: 8px; font-size: 14px; }}
  .event-info .label {{ color: #94a3b8; }}
  .event-info .value {{ color: #fff; font-weight: 600; text-align: right; }}
  .order-info {{ padding: 20px 24px; background: rgba(245,158,11,0.05); border-bottom: 1px solid rgba(255,255,255,0.1); }}
  .order-info .code {{ font-size: 24px; font-weight: 800; color: #f59e0b; letter-spacing: 2px; text-align: center; margin-bottom: 12px; }}
  .order-info .name {{ font-size: 18px; font-weight: 700; text-align: center; margin-bottom: 4px; }}
  .order-info .phone {{ font-size: 13px; color: #94a3b8; text-align: center; }}
  .seats-section {{ padding: 20px 24px; }}
  .seats-section h3 {{ font-size: 12px; color: #94a3b8; text-transform: uppercase; letter-spacing: 1px; margin: 0 0 16px; }}
  .tier-block {{ margin-bottom: 16px; }}
  .tier-name {{ font-size: 13px; font-weight: 700; color: #f59e0b; margin-bottom: 8px; }}
  .seat-row {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .seat-badge {{ background: rgba(255,255,255,0.1); border: 1px solid rgba(255,255,255,0.2); border-radius: 6px; padding: 5px 10px; font-size: 12px; font-weight: 600; }}
  .paid-banner {{ margin: 0 24px 20px; background: rgba(16,185,129,0.15); border: 1px solid #10b981; border-radius: 10px; padding: 12px; text-align: center; color: #10b981; font-weight: 700; font-size: 14px; }}
  .total-row {{ padding: 16px 24px; background: rgba(255,255,255,0.03); border-top: 1px solid rgba(255,255,255,0.1); display: flex; justify-content: space-between; align-items: center; }}
  .total-label {{ font-size: 14px; color: #94a3b8; }}
  .total-value {{ font-size: 22px; font-weight: 800; color: #10b981; }}
  .footer {{ padding: 16px 24px; text-align: center; font-size: 11px; color: #64748b; border-top: 1px solid rgba(255,255,255,0.05); }}
  .footer a {{ color: #f59e0b; text-decoration: none; }}
</style>
</head>
<body>
<div class="ticket-wrap">
  <div class="header">
    <h1>🎵 {event_name}</h1>
    <div class="subtitle">{event_date} • {show_time} • {event_venue}</div>
  </div>

  <div class="event-info">
    <div class="row">
      <span class="label">📍 Địa điểm</span>
      <span class="value">{event_venue}</span>
    </div>
    <div class="row">
      <span class="label">📍 Địa chỉ</span>
      <span class="value" style="font-size:12px;">{event_address}</span>
    </div>
    <div class="row">
      <span class="label">🕐 Check-in</span>
      <span class="value">{event_time}</span>
    </div>
    <div class="row">
      <span class="label">📞 Hotline</span>
      <span class="value">{hotline}</span>
    </div>
  </div>

  <div class="order-info">
    <div class="code">{order['code']}</div>
    <div class="name">{order['full_name']}</div>
    <div class="phone">{order['phone']}</div>
  </div>

  <div class="seats-section">
    <h3>🎟 Ghế của bạn</h3>"""

    for tid, tier_seats in seats_by_tier.items():
        tier_name = tiers_map.get(tid, {}).get('name', tid)
        tier_price = tiers_map.get(tid, {}).get('price', 0)
        html += f"""<div class="tier-block">
      <div class="tier-name">{tier_name} — {tier_price:,}đ/ghế</div>
      <div class="seat-row">"""
        for seat in tier_seats:
            html += f'<div class="seat-badge">{seat["code"]}</div>'
        html += """</div></div>"""

    html += f"""</div>

  <div class="paid-banner">✓ ĐÃ THANH TOÁN</div>

  <div class="total-row">
    <span class="total-label">TỔNG CỘNG</span>
    <span class="total-value">{int(order['total']):,}đ</span>
  </div>

  <div class="footer">
    Vé này là xác nhận chính thức của bạn. Vui lòng giữ mã đơn <strong>{order['code']}</strong> để đối chiếu khi check-in.<br>
    Cần hỗ trợ? Liên hệ <strong>{hotline}</strong>
  </div>
</div>
</body>
</html>"""

    subject = f"🎫 Vé của bạn – {event_name} ({event_date})"

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


def send_order_confirmation(email, order, seats, config):
    raise NotImplementedError("Email service is stubbed. Set up Resend API key to enable.")

def send_seat_assignment(email, order, seats, config):
    raise NotImplementedError("Email service is stubbed. Set up Resend API key to enable.")
