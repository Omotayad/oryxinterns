import psycopg2
from psycopg2 import pool
import bcrypt

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