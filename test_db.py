# test_db_connection.py
from db_utils import create_connection

def test_connection():
    connection = create_connection()
    if connection:
        print("Connection test successful!")
        connection.close()
    else:
        print("Connection failed!")

if __name__ == "__main__":
    test_connection()