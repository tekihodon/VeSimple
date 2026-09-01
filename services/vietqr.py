import requests
import json
import os

def get_vietqr_url(config, amount, order_code):
    vq = config['vietqr']
    template = vq.get('template', 'compact')
    return (f"https://img.vietqr.io/image/{vq['bankBin']}-{vq['accountNo']}-{template}.png"
            f"?amount={amount}&addInfo={order_code}&accountName={vq['accountName'].replace(' ', '%20')}")

def get_qr_path(order_code):
    return os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'qr', f'{order_code}.png')

def get_or_generate_qr(config, amount, order_code):
    qr_path = get_qr_path(order_code)
    if os.path.exists(qr_path):
        return f'/static/qr/{order_code}.png'
    url = get_vietqr_url(config, amount, order_code)
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            with open(qr_path, 'wb') as f:
                f.write(resp.content)
            return f'/static/qr/{order_code}.png'
    except Exception as e:
        print(f"QR generation failed: {e}")
    return url

def clear_cached_qr(order_code):
    qr_path = get_qr_path(order_code)
    if os.path.exists(qr_path):
        os.remove(qr_path)