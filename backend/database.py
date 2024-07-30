import mysql.connector
from random import choice, randint, uniform
from datetime import datetime, timedelta


db_connection = mysql.connector.connect(
    host="localhost",
    port=3306,
    user="root",
    password="Mich@el113",
    database="NHPTestDb"
)


cursor = db_connection.cursor()


products = [
    "DUOTRAV EYE DROPS 2.5ML", "VISTA EYE DROPS 5ML", "VISTA EYE DROPS 5ML",
    "VISTA EYE DROPS 5ML", "VISTA EYE DROPS 5ML", "EYEDITEN EYE DROPS 5ML",
    "PEFLOTAB 400MG CAPS x10", "PEFLOTAB 400MG CAPS x10", "PEFLOTAB 400MG CAPS x10",
    "PEFLOTAB 400MG CAPS x10", "CIPROTAB 500MG TABS x14", "MEPRASIL CAPS x20",
    "ARTHOCARE CAPS x30", "ASTYMIN CAPS x20", "CIPROTAB 500MG TABS x14",
    "ASTYMIN LIQUID 250ML", "ARTHOCARE CAPS x30", "ASTYMIN CAPS x20",
    "CIPROTAB 500MG TABS x14", "ARTHOCARE CAPS x30", "CIPROTAB 500MG TABS x14",
    "MEPRASIL CAPS x20", "ASTYMIN CAPS x20", "CIPROTAB 500MG TABS x14",
    "IVYBETANEOCIN EYE DROPS", "OPTIMOL EYE DROPS", "IVYZINC EYE DROPS",
    "COMBIGAN EYE DROPS", "PATANOL 0.1% EYE DROPS 5ML"
]

start_date = datetime.strptime('20240515', '%Y%m%d')
end_date = datetime.strptime('20240831', '%Y%m%d')

def random_date(start, end):
    return (start + timedelta(days=randint(0, (end - start).days))).strftime('%Y%m%d')


def generate_random_data():
    item_code = randint(10000, 10030)
    item_name = choice(products)
    source_company = "NHP"
    card_code = f"C{randint(1, 9):04d}"
    doc_total = round(uniform(100, 10000), 2)
    quantity = randint(1, 10)
    line_total = round(quantity * doc_total, 2)
    gross_profit = round(line_total * 0.1, 2)
    item_cost = round(line_total * 0.9, 2)
    date_key = random_date(start_date, end_date)
    doc_type = "Invoice"
    
    return (item_code, item_name, source_company, card_code, doc_total, quantity, line_total, gross_profit, item_cost, date_key, doc_type)

def generate_random_credit_memo_data():
    item_code = randint(10000, 10030)
    item_name = choice(products)
    source_company = "NHP"
    card_code = f"C{randint(1, 9):04d}"
    doc_total = -round(uniform(100, 10000), 2)
    quantity = -randint(1, 10)
    line_total = -round(quantity * doc_total, 2)
    gross_profit = -round(line_total * 0.1, 2)
    item_cost = -round(line_total * 0.9, 2)
    date_key = random_date(start_date, end_date)
    doc_type = "CreditMemo"
    
    return (item_code, item_name, source_company, card_code, doc_total, quantity, line_total, gross_profit, item_cost, date_key, doc_type)

#for _ in range(150):  
  #  data = generate_random_data()
    #cursor.execute("""
        #INSERT INTO ProductSales 
        #(ItemCode, ItemName, `Source Company`, CardCode, DocTotal, Quantity, LineTotal, GrssProfit, ItemCost, DateKey, DocType) 
        #VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
   # """, data)

for _ in range(100):  
    data = generate_random_credit_memo_data()
    cursor.execute("""
        INSERT INTO ProductSales 
        (ItemCode, ItemName, `Source Company`, CardCode, DocTotal, Quantity, LineTotal, GrssProfit, ItemCost, DateKey, DocType) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """, data)

# Commit changes and close connection
db_connection.commit()
db_connection.close()
