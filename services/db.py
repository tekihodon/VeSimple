import psycopg2
from psycopg2 import pool
import json
import os

_config = None

def get_config():
    global _config
    if _config is None:
        config_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        with open(config_path, encoding='utf-8') as f:
            _config = json.load(f)
    return _config

def get_db_url():
    return get_config()['dbUrl']

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = psycopg2.pool.ThreadedConnectionPool(1, 10, get_db_url())
    return _pool

def get_conn():
    return get_pool().getconn()

def close_conn(conn):
    get_pool().putconn(conn)

def quote_table(name):
    return f'"{name}"'

def query(sql, params=None, one=False):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        if cur.description:
            cols = [d[0] for d in cur.description]
            rows = cur.fetchall()
            result = [dict(zip(cols, r)) for r in rows]
            return result[0] if one and result else result
        return None
    finally:
        cur.close()
        close_conn(conn)

def execute(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()
        return cur.rowcount
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        close_conn(conn)

def execute_one(sql, params=None):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(sql, params)
        conn.commit()
        cols = [d[0] for d in cur.description]
        row = cur.fetchone()
        return dict(zip(cols, row)) if row else None
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        close_conn(conn)

def init_schema():
    schema_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'schema.sql')
    with open(schema_path, encoding='utf-8') as f:
        schema_sql = f.read()
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute(schema_sql)
        conn.commit()
    finally:
        cur.close()
        close_conn(conn)