import hashlib
import secrets
from flask import session, request
from functools import wraps

ADMIN_SESSION_KEY = '_admin_authenticated'

def check_admin_auth(config):
    auth = session.get(ADMIN_SESSION_KEY)
    return auth == hash_password(config['adminPass'])

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def login_admin(config, password):
    if password == config['adminPass']:
        session[ADMIN_SESSION_KEY] = hash_password(password)
        session.permanent = True
        return True
    return False

def logout_admin():
    session.pop(ADMIN_SESSION_KEY, None)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        from .db import get_config
        if not check_admin_auth(get_config()):
            from flask import jsonify, abort
            return jsonify({'error': 'Unauthorized'}), 401
        return f(*args, **kwargs)
    return decorated