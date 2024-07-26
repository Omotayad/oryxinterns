from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import jwt
import threading
import time
import datetime
import requests
from functools import wraps
from db_utils import (get_user, add_user, check_password, get_all_users, 
                      update_last_login, update_user_role_in_db, remove_user,
                      is_token_invalidated, invalidate_token, cleanup_invalidated_tokens,get_user_count)

total_predictions = 0

app = Flask(__name__, static_url_path='', static_folder='.')
CORS(app)
app.config['SECRET_KEY'] = 'ANHP25'  # Change this to a secure random key

def admin_token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'message': 'Token is missing!'}), 401
        try:
            if is_token_invalidated(token):
                return jsonify({'message': 'Token has been invalidated!'}), 401
            
            data = jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=["HS256"])
            if data['role'] != 'admin':
                return jsonify({'message': 'Admin privileges required!'}), 403
        except:
            return jsonify({'message': 'Token is invalid!'}), 401
        return f(*args, **kwargs)
    return decorated


def generate_token(username, is_admin=True):
    token = jwt.encode({
        'user': username,
        'is_admin': is_admin,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }, app.config['SECRET_KEY'], algorithm="HS256")
    return token

@app.route('/')
def serve_index():
    return send_from_directory('.', 'admin.html')

@app.route('/admin-login', methods=['POST'])
def admin_login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = get_user(username)
    if user and user['role'] == 'admin' and check_password(password, user['password']):
        token = jwt.encode({
            'user': username,
            'role': 'admin',
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }, app.config['SECRET_KEY'], algorithm="HS256")

        update_last_login(username)

        return jsonify({"message": "Admin login successful", "token": token}), 200
    
    return jsonify({"message": "Wrong Password or Username!"}), 401

@app.route('/logout', methods=['POST'])
def admin_logout():
    token = request.headers.get('Authorization')
    if not token:
        return jsonify({'message': 'Token is missing!'}), 401
    try:
        # Decode the token to verify it's valid
        jwt.decode(token.split()[1], app.config['SECRET_KEY'], algorithms=["HS256"])
        
        # Invalidate the token
        invalidate_token(token)
        
        return jsonify({"message": "Logged out successfully"}), 200
    except jwt.ExpiredSignatureError:
        return jsonify({"message": "Token has expired"}), 401
    except jwt.InvalidTokenError:
        return jsonify({"message": "Invalid token"}), 401

@app.route('/admin/user-stats', methods=['GET'])
@admin_token_required
def get_user_stats():
    # Get active users count from the main server
    try:
        response = requests.get('http://127.0.0.1:5001/active-users-count')
        active_users = response.json()['active_users_count']
    except:
        active_users = 0

    # Get total users count from the database
    total_users = get_user_count()

    return jsonify({
        'total_users': total_users,
        'active_users': active_users,
        'total_predictions': total_predictions
    })

@app.route('/admin/increment-predictions', methods=['POST'])
def increment_predictions():
    global total_predictions
    total_predictions += 1
    return jsonify({"message": "Prediction count incremented"}), 200

@app.route('/admin/add-user', methods=['POST'])
@admin_token_required
def add_new_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role')
    
    if not all([username, password, role]):
        return jsonify({"message": "Missing required fields"}), 400
    
    if get_user(username):
        return jsonify({"message": "Username already exists"}), 400
    
    add_user(username, password, role)
    return jsonify({"message": "User added successfully"}), 201

@app.route('/admin/users', methods=['GET'])
@admin_token_required
def get_users():
    users = get_all_users()
    return jsonify(users), 200

@app.route('/admin/user-login', methods=['POST'])
def user_login_notification():
    data = request.json
    username = data.get('username')
    role = data.get('role')
    login_time = data.get('login_time')
    
    # Update the last login time in the database
    update_last_login(username, login_time)
    
    return jsonify({"message": "User login information received"}), 200

@app.route('/admin/update-user-role', methods=['POST'])
@admin_token_required
def update_user_role():
    data = request.get_json()
    username = data.get('username')
    new_role = data.get('newRole')
    
    if not all([username, new_role]):
        return jsonify({"message": "Missing required fields"}), 400
    
    user = get_user(username)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Update the user's role in the database
    update_user_role_in_db(username, new_role)
    
    return jsonify({"message": f"User {username}'s role updated to {new_role}"}), 200

@app.route('/admin/delete-user/<username>', methods=['DELETE'])
@admin_token_required
def delete_user(username):
    user = get_user(username)
    if not user:
        return jsonify({"message": "User not found"}), 404
    
    # Delete the user from the database
    remove_user(username)
    
    return jsonify({"message": f"User {username} has been deleted"}), 200

def run_cleanup():
    while True:
        time.sleep(3600)  # Sleep for 1 hour
        cleanup_invalidated_tokens()

cleanup_thread = threading.Thread(target=run_cleanup)
cleanup_thread.start()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5002, debug=True)