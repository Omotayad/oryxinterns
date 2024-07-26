import psycopg2
import random
import time
from datetime import datetime, timedelta
import string

# Database connection parameters
db_host = 'localhost'
db_name = 'NHP'
db_user = 'postgres'
db_password = 'Admin9114'
db_port = '5432'

# Connect to the database
conn = psycopg2.connect(
    host=db_host,
    dbname=db_name,
    user=db_user,
    password=db_password,
    port=db_port
)
cur = conn.cursor()

# Fetch sample data from the product_sales table
cur.execute("SELECT DISTINCT itemname FROM product_sales")
item_names = [row[0] for row in cur.fetchall()]
cur.execute("SELECT DISTINCT whscode FROM product_sales")
whs_codes = [row[0] for row in cur.fetchall()]

def generate_random_card_code():
    return 'C' + ''.join(random.choices(string.digits, k=4))

def generate_invoice_data():
    item_name = random.choice(item_names)
    card_code = generate_random_card_code()
    whs_code = random.choice(whs_codes)
    quantity = random.randint(1, 100)
    unit_price = random.uniform(10, 1000)
    line_total = quantity * unit_price
    doc_total = line_total * 1.1  # Adding 10% for taxes/fees
    gross_profit = line_total * random.uniform(0.1, 0.3)
    item_cost = line_total - gross_profit
    
    return (
        random.randint(10000, 99999),  # itemcode
        item_name,
        'NHP',  # sourcecompany
        card_code,
        datetime.now().strftime('%Y-%m-%d'),  # docdate
        round(doc_total, 2),
        quantity,
        round(line_total, 2),
        whs_code,
        round(doc_total * random.uniform(0, 1), 2),  # paidtodate
        round(gross_profit, 2),
        round(item_cost, 2),
        datetime.now().strftime('%Y-%m-%d'),  # datekey
        'Invoice'
    )

def generate_credit_memo_data():
    item_name = random.choice(item_names)
    card_code = generate_random_card_code()
    whs_code = random.choice(whs_codes)
    quantity = random.randint(-50, -1)  # Negative quantity for credit memo
    unit_price = random.uniform(10, 1000)
    line_total = quantity * unit_price
    doc_total = line_total * 1.1  # Adding 10% for taxes/fees
    gross_profit = line_total * random.uniform(0.1, 0.3)
    item_cost = line_total - gross_profit
    
    return (
        random.randint(10000, 99999),  # itemcode
        item_name,
        'NHP',  # sourcecompany
        card_code,
        datetime.now().strftime('%Y-%m-%d'),  # docdate
        round(doc_total, 2),
        quantity,
        round(line_total, 2),
        whs_code,
        round(doc_total * random.uniform(0, 1), 2),  # paidtodate
        round(gross_profit, 2),
        round(item_cost, 2),
        datetime.now().strftime('%Y-%m-%d'),  # datekey
        'Credit Memo'
    )

# Main loop to insert data every second
try:
    while True:
        # Randomly choose between invoice and credit memo
        if random.choice([True, False]):
            data = generate_invoice_data()
        else:
            data = generate_credit_memo_data()
        
        cur.execute("""
            INSERT INTO product_sales 
            (itemcode, itemname, sourcecompany, cardcode, docdate, doctotal, quantity, 
            linetotal, whscode, paidtodate, grssprofit, itemcost, datekey, doctype)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, data)
        conn.commit()
        
        # Print the inserted data
        print("Inserted:")
        print(f"Item Code: {data[0]}")
        print(f"Item Name: {data[1]}")
        print(f"Source Company: {data[2]}")
        print(f"Card Code: {data[3]}")
        print(f"Doc Date: {data[4]}")
        print(f"Doc Total: {data[5]}")
        print(f"Quantity: {data[6]}")
        print(f"Line Total: {data[7]}")
        print(f"WHS Code: {data[8]}")
        print(f"Paid to Date: {data[9]}")
        print(f"Gross Profit: {data[10]}")
        print(f"Item Cost: {data[11]}")
        print(f"Date Key: {data[12]}")
        print(f"Doc Type: {data[13]}")
        print("-" * 50)  # Separator line
        
        time.sleep(1)  # Wait for 1 second
except KeyboardInterrupt:
    print("Stopping data insertion...")
finally:
    cur.close()
    conn.close()
    print("Database connection closed.")