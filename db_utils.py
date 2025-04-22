# db_utils.py
import mysql.connector
from mysql.connector import Error
import pandas as pd

def create_connection():
    connection = None
    try:
        connection = mysql.connector.connect(
            host='localhost',
            database='travel_planner',
            user='root',  # Replace with your MySQL username
            password='P@ssw0rd27'  # Replace with your MySQL password
        )
        if connection.is_connected():
            print("Connected to MySQL database")
            return connection
    except Error as e:
        print(f"Error: {e}")
        return None

def execute_query(connection, query, params=None):
    cursor = connection.cursor()
    try:
        cursor.execute(query, params or ())
        connection.commit()
        return True
    except Exception as e:
        connection.rollback()
        return False
    finally:
        cursor.close()

def execute_read_query(connection, query, params=None):
    cursor = connection.cursor(dictionary=True)
    try:
        cursor.execute(query, params or ())
        result = cursor.fetchall()
        return result
    finally:
        cursor.close()