import streamlit as st
from datetime import datetime
from db_utils import execute_query, execute_read_query, create_connection

def add_travel_note(trip_id, title, content, date, location=None, mood=None):
    """
    Add a new travel note to the database.
    """
    if not title or not content:
        return False, "Title and content are required.", None

    conn = create_connection()
    cursor = conn.cursor(dictionary=True)

    query = """
    INSERT INTO travel_notes (trip_id, title, content, date, location, mood)
    VALUES (%s, %s, %s, %s, %s, %s)
    """

    params = (trip_id, title, content, date, location, mood)

    try:
        cursor.execute(query, params)
        conn.commit()
        note_id = cursor.lastrowid
        return True, f"Travel note '{title}' added successfully.", note_id
    except Exception as e:
        return False, f"Failed to add travel note: {str(e)}", None
    finally:
        cursor.close()
        conn.close()

def get_travel_notes(trip_id):
    """
    Get all travel notes for a specific trip.
    """
    conn = create_connection()
    query = """
    SELECT note_id, title, content, date, location, mood, created_at
    FROM travel_notes
    WHERE trip_id = %s
    ORDER BY date DESC, created_at DESC
    """
    
    notes = execute_read_query(conn, query, (trip_id,))
    return notes

def get_travel_note(note_id):
    """
    Get a specific travel note by ID.
    """
    conn = create_connection()
    query = """
    SELECT note_id, trip_id, title, content, date, location, mood, created_at
    FROM travel_notes
    WHERE note_id = %s
    """
    
    result = execute_read_query(conn, query, (note_id,))
    
    if result and result[0]:
        return result[0]
    else:
        return None

def update_travel_note(note_id, title, content, date, location=None, mood=None):
    """
    Update an existing travel note.
    """
    if not title or not content:
        return False, "Title and content are required."
    
    conn = create_connection()
    query = """
    UPDATE travel_notes
    SET title = %s, content = %s, date = %s, location = %s, mood = %s
    WHERE note_id = %s
    """
    
    params = (title, content, date, location, mood, note_id)
    result = execute_query(conn, query, params)
    
    if result:
        return True, f"Travel note '{title}' updated successfully."
    else:
        return False, "Failed to update travel note. Please try again."

def delete_travel_note(note_id):
    """
    Delete a travel note.
    """
    conn = create_connection()
    query = """
    DELETE FROM travel_notes
    WHERE note_id = %s
    """
    
    result = execute_query(conn, query, (note_id,))
    
    if result:
        return True, "Travel note deleted successfully."
    else:
        return False, "Failed to delete travel note. Please try again."

def get_mood_counts(trip_id):
    """
    Get counts of different moods for a trip.
    """
    conn = create_connection()
    query = """
    SELECT mood, COUNT(*) as count
    FROM travel_notes
    WHERE trip_id = %s AND mood IS NOT NULL
    GROUP BY mood
    ORDER BY count DESC
    """
    
    mood_counts = execute_read_query(conn, query, (trip_id,))
    return mood_counts

def get_locations(trip_id):
    """
    Get all unique locations mentioned in travel notes for a trip.
    """
    conn = create_connection()
    query = """
    SELECT DISTINCT location
    FROM travel_notes
    WHERE trip_id = %s AND location IS NOT NULL AND location != ''
    ORDER BY location
    """
    
    locations = execute_read_query(conn, query, (trip_id,))
    return [loc['location'] for loc in locations]