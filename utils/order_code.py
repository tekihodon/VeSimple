import hashlib
import time
import re

def generate_order_code(phone):
    timestamp = int(time.time())
    combined = f"{phone}{timestamp}"
    hash_val = hashlib.md5(combined.encode()).hexdigest()[:4]
    month = time.strftime('%m')
    day = time.strftime('%d')
    year = time.strftime('%y')
    code = f"GK15-{year}{month}{day}-{hash_val.upper()}"
    return code