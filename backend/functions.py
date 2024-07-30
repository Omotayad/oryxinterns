#Functions for past history and user management
import datetime
import pytz
from werkzeug.security import generate_password_hash, check_password_hash
from io import BytesIO
import pandas as pd
from flask import send_file, jsonify 
import re
from bson.objectid import ObjectId


def is_valid_card_code(card_code):
    return re.match("^[a-zA-Z0-9_]+$", card_code) is not None

def is_valid_username(username):
    return re.match("^[a-zA-Z0-9_]+$", username) is not None

def is_valid_password(password):
    return len(password) >= 8

def validate_customer_id(customer_id):
    pattern = r'^C\d{4}$'
    return bool(re.match(pattern, customer_id))


def save_request(connection, card_code, month, year, prediction,timestamp, username):
    conn = connection
    requests_collection = conn['PastRequests']
    requests_collection.insert_one({
        'cardCode': card_code,
        'month': month,
        'year': year,
        'prediction': prediction,
        'user': username,
        'timestamp': timestamp
    })
    return jsonify({'message': 'Request saved successfully.'}), 201


def get_requests(connection, username):
    conn = connection
    requests_collection = conn['PastRequests']
    requests = list(requests_collection.find({'user':username}).sort('timestamp', -1))
    for request in requests:
        request['_id'] = str(request['_id'])
    for request in requests:
        request['prediction'] = round(request['prediction'], 2)
    return jsonify(requests), 200


def clear_request(connection, username):
    conn = connection
    requests_collection = conn['PastRequests']
    requests_collection.delete_many({'user': username})
    return jsonify({'message': 'All past requests cleared successfully.'}), 200

def download_requests(connection, username):
     conn = connection
     result, status = get_requests(conn, username)
     if status != 200:
        return result, status
    
     try:
        result = result.get_json()

        if not isinstance(result, list):
            return "Invalid data format", 400
       
        df = pd.DataFrame(result, columns=['cardCode', 'month', 'year', 'prediction'])
       
        output = BytesIO()
        writer = pd.ExcelWriter(output, engine='openpyxl')
        df.to_excel(writer, index=False, sheet_name='Past Requests')
        writer.close()
        output.seek(0)
        
        return send_file(output, download_name='past_requests.xlsx', as_attachment=True)
    
     except Exception as e:
        print(f"Error generating Excel file: {e}")
        return "Error generating Excel file", 500



#tested
def get_all_users(connection):
    conn = connection
    users_collection = conn['Users']
    users = list(users_collection.find())
    for user in users:
        user['_id'] = str(user['_id'])
        user.pop('password', None) 
    return jsonify(users), 200

def get_a_user(connection, user_id):
    conn = connection
    users_collection = conn['Users']
    user = users_collection.find_one({'_id': ObjectId(user_id)})
    if user:
        user['_id'] = str(user['_id'])
        user.pop('password', None)
        return jsonify(user), 200
    return jsonify({'error': 'User not found'}), 404

#tested
def create_user(connection, first_name, last_name, username, role, password):
    if first_name == '':
        return jsonify({'message': ' First Name is required'}), 400
    if last_name == '':
        return jsonify({'message': 'Last Name is required'}), 400
    if not is_valid_username(username) or username == '':
        return jsonify({'message': 'Username is required. Only letters, numbers, and underscores are allowed.'}), 400
    if role == '':
        return jsonify({'message': 'Role is required'}), 400
    if not is_valid_password(password) or password == '':
        return jsonify({'message': 'Password must be at least 8 characters long.'}), 400
    
    
    conn = connection
    users_collection = conn['Users']

    existing_user = users_collection.find_one({'username': username})
    if existing_user:
        return jsonify({"message": "Username is already taken"}), 400

    user_id = users_collection.insert_one({
        'firstName': first_name,
        'lastName': last_name,
        'username': username,
        'role': role,
        'password': generate_password_hash(password)
    }).inserted_id

    new_user = users_collection.find_one({'_id': user_id})
    new_user['_id'] = str(new_user['_id'])

    user_data = {
        "_id": new_user['_id'],
        "firstName": new_user['firstName'],
        "lastName": new_user['lastName'],
        "username": new_user['username'],
        "role": new_user['role']
    }

    return jsonify(user_data), 201

#tested
def edit_user(connection, user_id, first_name, last_name, username, role, password):
  if first_name=='' or last_name=='' or username=='' or role==''or password=='':
      return jsonify({'message': 'All fields are required'}), 400
  update_fields = {}
  if first_name:
        update_fields['firstName'] = first_name
  if last_name:
        update_fields['lastName'] = last_name
  if username:
    if not is_valid_username(username):
            return jsonify({'message': 'Username is invalid. Only letters, numbers, and underscores are allowed.'}), 400
    update_fields['username'] = username
  if role:
        update_fields['role'] = role
  if password:
        if not is_valid_password(password):
            return jsonify({'message': 'Password must be at least 8 characters long.'}), 400
        update_fields['password'] = generate_password_hash(password)

  conn = connection
  users_collection = conn['Users']

  result = users_collection.update_one({'_id': ObjectId(user_id)}, {'$set': update_fields})
  if result.modified_count == 1:
        updated_user = users_collection.find_one({'_id': ObjectId(user_id)})
        updated_user['_id'] = str(updated_user['_id'])
        updated_user.pop('password', None)
        return jsonify(updated_user), 200
  return jsonify({'message': 'No changes made'}), 400

#tested
def delete_user(connection, user_id):
    conn = connection
    users_collection = conn['Users']
    deleted_user = users_collection.find_one_and_delete({'_id': ObjectId(user_id)})
    if deleted_user:
        deleted_user['_id'] = str(deleted_user['_id'])
        return jsonify(deleted_user), 200
    return jsonify({'message': 'User not found'}), 404

