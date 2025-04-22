# user_management.py
from db_utils import create_connection, execute_query, execute_read_query
from firebase_config import create_user, authenticate_user
import hashlib

def register_user(name, email, password):
    # Firebase Authentication
    firebase_user = create_user(email, password)
    
    if not firebase_user:
        return False, "Firebase authentication failed"
    
    # Store user in MySQL database
    connection = create_connection()
    if not connection:
        return False, "Database connection failed"
    
    # Hash password for database storage
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    query = f"""
    INSERT INTO users (name, email, password_hash)
    VALUES ('{name}', '{email}', '{hashed_password}')
    """
    
    success = execute_query(connection, query)
    connection.close()
    
    if success:
        return True, "User registered successfully"
    else:
        return False, "Failed to register user in database"

def login_user(email, password):
    # Authenticate with Firebase
    firebase_user = authenticate_user(email, password)
    
    if not firebase_user:
        return False, None, "Firebase authentication failed"
    
    # Get user details from database
    connection = create_connection()
    if not connection:
        return False, None, "Database connection failed"
    
    query = f"""
    SELECT * FROM users WHERE email = '{email}'
    """
    
    users = execute_read_query(connection, query)
    connection.close()
    
    if users and len(users) > 0:
        return True, users[0], "Login successful"
    else:
        return False, None, "User not found in database"

def get_user_by_id(user_id):
    connection = create_connection()
    if not connection:
        return None
    
    query = f"""
    SELECT * FROM users WHERE user_id = {user_id}
    """
    
    users = execute_read_query(connection, query)
    connection.close()
    
    if users and len(users) > 0:
        return users[0]
    else:
        return None

def update_user_profile(user_id, name=None, email=None):
    connection = create_connection()
    if not connection:
        return False, "Database connection failed"
    
    # Build update query dynamically
    update_parts = []
    if name:
        update_parts.append(f"name = '{name}'")
    if email:
        update_parts.append(f"email = '{email}'")
    
    if not update_parts:
        return False, "No fields to update"
    
    query = f"""
    UPDATE users
    SET {', '.join(update_parts)}
    WHERE user_id = {user_id}
    """
    
    success = execute_query(connection, query)
    connection.close()
    
    if success:
        return True, "Profile updated successfully"
    else:
        return False, "Failed to update profile"