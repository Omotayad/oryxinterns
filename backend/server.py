import os
import datetime
import pandas as pd 
from functools import wraps
from sklearn.ensemble import GradientBoostingRegressor 
from sklearn.preprocessing import OneHotEncoder, StandardScaler 
from sklearn.compose import ColumnTransformer 
from sklearn.pipeline import Pipeline 
from flask import Flask, request, jsonify, make_response
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, unset_access_cookies
from flask_cors import CORS
import mysql.connector
from dotenv import load_dotenv
from pymongo import MongoClient
from apscheduler.schedulers.background import BackgroundScheduler
from functions import get_all_users, create_user, edit_user,delete_user, get_requests, save_request, download_requests,clear_request, validate_customer_id,get_a_user,is_valid_username,is_valid_password
from werkzeug.security import check_password_hash


load_dotenv()
app = Flask(__name__)
CORS(app, supports_credentials=True, origins=["http://localhost:3000"])
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY')
app.config['JWT_TOKEN_LOCATION'] = ['cookies']
app.config['JWT_COOKIE_CSRF_PROTECT'] = False
app.config['JWT_COOKIE_SECURE'] = False 
app.config['JWT_ACCESS_COOKIE_PATH'] = '/'
jwt = JWTManager(app)

#dbconfig = {
 #   "host": "localhost",
#    "port": 3306,
#    "user": "root",
#    "database": "NHPTestDb"
#}

#cnxpool = mysql.connector.pooling.MySQLConnectionPool(
   # pool_name="mypool",
   # pool_size=32,  
   # **dbconfig
#)

#def db_connection():
    #connection = cnxpool.get_connection() 
    #return connection
    

def get_db_connection():
    
    connection_string = os.getenv('DATABASE_URL')
    client = MongoClient(connection_string)
    db = client['NHPDB']
    return db


def load_initial_data():
    data = pd.read_excel('/Users/michyb/Downloads/Coding/NHPapp/backend/data/Sales.xlsx') 
    return data

#def get_new_data():
    connection = db_connection()
    query = "SELECT * FROM ProductSales WHERE CardCode NOT IN ('C0003','C0004','C0005')"
    new_data = pd.read_sql(query, connection)
    connection.close()
    return new_data

def update_dataset(initial_data, new_data):
    updated_data = pd.concat([initial_data, new_data],ignore_index= True)
    return updated_data

def preprocessing(data):
    data['DateKey'] = pd.to_datetime(data['DateKey'], format='%Y%m%d') 
    data['Month'] = data['DateKey'].dt.month 
    data['Year'] = data['DateKey'].dt.year 
    data2 = data[data['DocType']!= 'CreditMemo'] 
    customer_monthly_sales = data2.groupby(['CardCode','Year','Month'])['LineTotal'].sum().reset_index() 


    customer_monthly_sales['Month'] = customer_monthly_sales['Month'].replace({
        1: 'January', 2: 'February', 3: 'March', 4: 'April', 5: 'May', 6: 'June',
        7: 'July', 8: 'August', 9: 'September', 10: 'October', 11: 'November', 12: 'December'
    })

    yearly_aggregates = customer_monthly_sales.groupby(['CardCode', 'Year'])['LineTotal'].sum().reset_index() 
    yearly_aggregates.columns = ['CardCode', 'Year', 'YearlyTotal'] 
    customer_monthly_sales = customer_monthly_sales.merge(yearly_aggregates, on=['CardCode', 'Year'], how='left') 
    return customer_monthly_sales

def train_model(sales):
    X = sales[['CardCode','Year','Month', 'YearlyTotal']] 
    y = sales['LineTotal'] 

    encode_cols = ['CardCode', 'Month'] 
    scale_cols = ['Year', 'YearlyTotal'] 

    encode_transformer = Pipeline(steps = [ 
    ('encode', OneHotEncoder()) 
    ]) 

    scale_transformer = Pipeline(steps = [ 
    ('scale', StandardScaler()) 
    ]) 

 

    preprocessor = ColumnTransformer(transformers = [ 
    ('num', scale_transformer, scale_cols) 
    ,('cat', encode_transformer, encode_cols) 
    ])

    gradient_model = Pipeline(steps = [ 
    ('preprocessor', preprocessor), 
    ('model', GradientBoostingRegressor(n_estimators=1200, learning_rate=0.3, max_depth=7)) 
    ]) 

    gradient_model.fit(X, y)
    return gradient_model

def predict_future_sales(model, card_code, year, month, sales):
    previous_years_data = sales[(sales['CardCode'] == card_code) & (sales['Year'] < year)]
    yearly_total = previous_years_data['LineTotal'].sum()
    
    new_data = {
        'CardCode': [card_code],
        'Year': [year],
        'Month': [month],
        'YearlyTotal': [yearly_total]
    }
    new_df = pd.DataFrame(new_data)
    prediction = model.predict(new_df)
    return prediction[0]


data = load_initial_data()
customer_monthly_sales = preprocessing(data)
gradient_model = train_model(customer_monthly_sales)
connection = get_db_connection()


#def update():
   # global data
   # global customer_monthly_sales
   # global gradient_model

   # new_data = get_new_data()
   # if not new_data.empty:
     #   data = update_dataset(data, new_data)
      #  customer_monthly_sales = preprocessing(data)
      #  gradient_model = train_model(customer_monthly_sales)
      #  print("Dataset and model successfully updated")
   # else:
    #    print("No new data. Verify database.")

def admin_required(f):
    @wraps(f)
    @jwt_required(locations=['cookies'])
    def decorated_function(*args, **kwargs):
        current_user = get_jwt_identity()
        if current_user.get('role') != 'Admin':
            return jsonify({"msg": "Admins only!"}), 403
        return f(*args, **kwargs)
    return decorated_function





@app.route('/predrevenue', methods=['POST'])
@jwt_required(locations=['cookies'])
def predict():
    data = request.get_json()
    card_code = data['card_code']
    month = data['month']
    year = data['year']
    if card_code == '' or month == '' or year == None:
        return jsonify({'message': 'All fields are required'}), 400
    elif not validate_customer_id(card_code):
        return jsonify({'message': 'Invalid customer Id'}), 400
    elif not card_code in customer_monthly_sales['CardCode'].values:
        return jsonify({'message': 'Customer not found.'}), 400
    else:
        prediction = predict_future_sales(gradient_model, card_code, year, month, customer_monthly_sales)
        return jsonify({'prediction': prediction, 'customerId': card_code, 'month': month, 'year': year})

@app.route('/pastsales', methods=['POST'])
@jwt_required(locations=['cookies'])
def pastsales():
    data = request.get_json()
    card_code = data['card_code']
    past_sales = customer_monthly_sales[customer_monthly_sales['CardCode'] == card_code]
    past_sales = past_sales.sort_values(by=['Year', 'Month'], ascending=[False, False])
    last_three_records = past_sales.head(4)
    results = last_three_records.to_dict(orient='records')
    
    return jsonify(results)
    
@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data['username']
    password = data['password']
    if not is_valid_username(username) or username == '':
        return jsonify({'message': 'Username is required. Only letters, numbers, and underscores are allowed.'}), 400
    if not is_valid_password(password) or password == '':
        return jsonify({'message': 'Password must be at least 8 characters long.'}), 400
    conn = connection
    users_collection = conn['Users']
    user = users_collection.find_one({'username': username})
    if user:
        if check_password_hash(user['password'], password):
            access_token = create_access_token(identity={'username': user['username'],'role':user['role']},expires_delta=datetime.timedelta(hours=1))
            response = make_response(jsonify({'id':str(user['_id']),'username': user['username'],'role': user['role']}), 200)
            response.set_cookie('access_token_cookie', access_token, httponly=True, samesite='None' ,secure=True,max_age=3600)
            return response
        return jsonify({'message': 'Incorrect password'}), 401
    return jsonify({'message': 'Wrong username'}), 404

@app.route('/logout', methods=['POST'])
@jwt_required(locations=['cookies'])
def logout():
    response = jsonify({"logout": True})
    unset_access_cookies(response)
    return response, 200


@app.route('/users', methods = ['GET'])
@admin_required
def get_users():
    users = get_all_users(connection)
    return users

@app.route('/users/<user_id>', methods = ['GET'])
@jwt_required(locations=['cookies'])
def get_user(user_id):
    user = get_a_user(connection, user_id)
    return user

@app.route('/users', methods = ['POST'])
@admin_required
def add_user():
   data = request.get_json()
   first_name = data['firstname']
   last_name = data['lastname']
   username = data['username']
   role = data['role']
   password = data['password']
   result = create_user(connection,first_name, last_name, username, role, password)
   return result

@app.route('/users/<user_id>', methods=['PUT'])
@admin_required
def update_user(user_id):
    data = request.get_json()
    first_name = data['firstName']
    last_name = data['lastName']
    username = data['username']
    role = data['role']
    password = data['password']
    result = edit_user(connection, user_id,first_name, last_name, username, role, password)
    return result

@app.route('/users/<user_id>', methods=['DELETE'])
@admin_required
def remove_user(user_id):
    result = delete_user(connection, user_id)
    return result


@app.route('/history', methods=['GET'])
@jwt_required(locations=['cookies'])
def get_history():
    current_user = get_jwt_identity()
    username = current_user['username']
    result = get_requests(connection, username)
    return result

@app.route('/history', methods=['POST'])
@jwt_required(locations=['cookies'])
def save_history():
    data = request.get_json()
    current_user = get_jwt_identity()
    username = current_user['username']
    card_code = data['card_code']
    month = data['month']
    year = data['year']
    prediction = data['prediction']
    timestamp = data['timestamp']
    result = save_request(connection, card_code, month, year, prediction,timestamp, username)
    return result

@app.route('/clear-history', methods=['POST'])
@jwt_required(locations=['cookies'])
def clear_history():
    result = clear_request(connection)
    return result

@app.route('/download-history', methods=['GET'])
@jwt_required(locations=['cookies'])
def download_history():
    current_user = get_jwt_identity()
    username = current_user['username']
    result = download_requests(connection, username)
    return result



if __name__ == '__main__':
    #scheduler = BackgroundScheduler()
    #scheduler.add_job(update, 'interval', minutes=5)  
    #scheduler.start()



    app.run(debug=True)