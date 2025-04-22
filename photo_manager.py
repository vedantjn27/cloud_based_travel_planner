# photo_manager.py
import os
from datetime import datetime
from firebase_config import upload_file, download_file
from db_utils import create_connection, execute_query, execute_read_query
from firebase_config import storage
import uuid
import os

def save_travel_photo(user_id, trip_id, photo_file, description):
    connection = create_connection()
    if not connection:
        return False, None, "Database connection failed"

    try:
        # Read the file bytes
        photo_bytes = photo_file.read()
        
        # Generate a filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        file_extension = os.path.splitext(photo_file.name)[1]
        filename = f"user_{user_id}trip{trip_id}_{timestamp}{file_extension}"
        
        # Store in database (explicitly including created_at)
        cursor = connection.cursor()
        cursor.execute(
            """INSERT INTO travel_photos 
            (user_id, trip_id, filename, description, file_data, created_at) 
            VALUES (%s, %s, %s, %s, %s, NOW())""",
            (user_id, trip_id, filename, description, photo_bytes)
        )
        photo_id = cursor.lastrowid
        connection.commit()
        
        return True, photo_id, "Photo uploaded successfully"
    except Exception as e:
        connection.rollback()
        return False, None, f"Error saving photo: {str(e)}"
    finally:
        if connection:
            connection.close()
def get_trip_photos(trip_id):
    connection = create_connection()
    if not connection:
        return None
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(
            "SELECT photo_id, filename, description, file_data FROM travel_photos WHERE trip_id = %s ORDER BY created_at DESC",
            (trip_id,)
        )
        return cursor.fetchall()
    except Exception as e:
        print(f"Error fetching photos: {str(e)}")
        return None
    finally:
        if connection:
            connection.close()