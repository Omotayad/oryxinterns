import psycopg2
from psycopg2 import pool
import bcrypt
import datetime

# Create a connection pool
connection_pool = psycopg2.pool.SimpleConnectionPool(
    1, 20,
    database="NHP USERS",
    user="postgres",
    password="Admin9114",
    host="localhost",
    port="5432"
)

def get_user(username):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE username = %s", (username,))
            user = cur.fetchone()
            if user:
                return {'id': user[0], 'username': user[1], 'password': user[2], 'role': user[3]}
            return None
    finally:
        connection_pool.putconn(conn)

def add_user(username, password, role):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            hashed_password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            cur.execute(
                "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
                (username, hashed_password, role)
            )
            conn.commit()
    finally:
        connection_pool.putconn(conn)

def check_password(provided_password, stored_password):
    return bcrypt.checkpw(provided_password.encode('utf-8'), stored_password.encode('utf-8'))

def get_all_users():
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT username, role, last_login FROM users")
            users = cur.fetchall()
            return [{'username': user[0], 'role': user[1], 'lastLogin': user[2].isoformat() if user[2] else None} for user in users]
    finally:
        connection_pool.putconn(conn)

def update_last_login(username, login_time=None):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            if login_time is None:
                login_time = datetime.datetime.now()
            cur.execute(
                "UPDATE users SET last_login = %s WHERE username = %s",
                (login_time, username)
            )
            conn.commit()
    finally:
        connection_pool.putconn(conn)

def update_user_role_in_db(username, new_role):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE users SET role = %s WHERE username = %s",
                (new_role, username)
            )
            conn.commit()
    finally:
        connection_pool.putconn(conn)

def remove_user(username):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM users WHERE username = %s",
                (username,)
            )
            conn.commit()
    finally:
        connection_pool.putconn(conn)

def is_token_invalidated(token):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM invalidated_tokens WHERE token = %s", (token,))
            return cur.fetchone() is not None
    finally:
        connection_pool.putconn(conn)

def invalidate_token(token):
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("INSERT INTO invalidated_tokens (token) VALUES (%s)", (token,))
            conn.commit()
    finally:
        connection_pool.putconn(conn)

def cleanup_invalidated_tokens():
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM invalidated_tokens WHERE invalidated_at < NOW() - INTERVAL '24 hours'")
            conn.commit()
    finally:
        connection_pool.putconn(conn)

def get_user_count():
    conn = connection_pool.getconn()
    try:
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM users WHERE role = 'user'")
            count = cur.fetchone()[0]
            return count
    finally:
        connection_pool.putconn(conn)