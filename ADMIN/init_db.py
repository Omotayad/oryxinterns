import psycopg2
import bcrypt

# Database connection parameters
db_params = {
    "database": "NHP USERS",
    "user": "postgres",
    "password": "Admin9114",
    "host": "localhost",
    "port": "5432"
}

# Admin user details
admin_username = "Admin"
admin_password = "Adminpass"  # The actual password you want to set
admin_role = "admin"

# Hash the password
hashed_password = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

# Connect to the database and insert the admin user
try:
    conn = psycopg2.connect(**db_params)
    cur = conn.cursor()
    
    cur.execute(
        "INSERT INTO users (username, password, role) VALUES (%s, %s, %s)",
        (admin_username, hashed_password, admin_role)
    )
    
    conn.commit()
    print("Admin user created successfully.")
    
except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)

finally:
    if conn:
        cur.close()
        conn.close()
        print("PostgreSQL connection is closed")