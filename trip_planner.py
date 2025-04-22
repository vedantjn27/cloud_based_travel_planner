# trip_planner.py
from db_utils import create_connection, execute_query, execute_read_query
from api_integration import get_weather_data, get_place_recommendations
from datetime import datetime, timedelta
import random

def create_trip(user_id, destination, start_date, end_date, budget):
    connection = create_connection()
    if not connection:
        return False, None, "Database connection failed"
    
    query = f"""
    INSERT INTO trips (user_id, destination, start_date, end_date, budget)
    VALUES ({user_id}, '{destination}', '{start_date}', '{end_date}', {budget})
    """
    
    success = execute_query(connection, query)
    
    if not success:
        connection.close()
        return False, None, "Failed to create trip"
    
    # Get the new trip ID
    trip_id_query = "SELECT LAST_INSERT_ID() as trip_id"
    result = execute_read_query(connection, trip_id_query)
    connection.close()
    
    if result and len(result) > 0:
        trip_id = result[0]['trip_id']
        return True, trip_id, "Trip created successfully"
    else:
        return False, None, "Failed to retrieve trip ID"

def generate_itinerary(trip_id):
    connection = create_connection()
    if not connection:
        return False, "Database connection failed"
    
    try:
        # Get trip details using parameterized query
        trip_query = "SELECT * FROM trips WHERE trip_id = %s"
        trips = execute_read_query(connection, trip_query, (trip_id,))
        
        if not trips:
            return False, "Trip not found"
        
        trip = trips[0]
        destination = trip['destination']
        start_date = datetime.strptime(str(trip['start_date']), '%Y-%m-%d')
        end_date = datetime.strptime(str(trip['end_date']), '%Y-%m-%d')
        
        # Get recommendations
        attractions = get_place_recommendations(destination, "tourist_attraction") or [{"name": "Local sightseeing"}]
        restaurants = get_place_recommendations(destination, "restaurant") or [{"name": "Local dining"}]
        
        # Generate daily itinerary
        days = (end_date - start_date).days + 1
        
        # Delete existing itinerary
        delete_query = "DELETE FROM itineraries WHERE trip_id = %s"
        execute_query(connection, delete_query, (trip_id,))
        
        # Create new itinerary
        for day in range(1, days + 1):
            current_date = start_date + timedelta(days=day-1)
            
            morning_attraction = random.choice(attractions)
            lunch_place = random.choice(restaurants)
            afternoon_attraction = random.choice([a for a in attractions if a != morning_attraction])
            dinner_place = random.choice([r for r in restaurants if r != lunch_place])
            
            full_day = (
                f"Day {day} ({current_date.strftime('%Y-%m-%d')}):\n"
                f"Morning: Visit {morning_attraction['name']}\n"
                f"Lunch: Dine at {lunch_place['name']}\n"
                f"Afternoon: Explore {afternoon_attraction['name']}\n"
                f"Evening: Dinner at {dinner_place['name']}"
            )
            
            # Insert with parameterized query
            itinerary_query = """
            INSERT INTO itineraries (trip_id, day, activity, date)
            VALUES (%s, %s, %s, %s)
            """
            params = (trip_id, day, full_day, current_date.strftime('%Y-%m-%d'))
            execute_query(connection, itinerary_query, params)
        
        return True, "Itinerary generated successfully"
        
    except Exception as e:
        return False, f"Error generating itinerary: {str(e)}"
    finally:
        if connection:
            connection.close()

def get_trip_itinerary(trip_id):
    connection = create_connection()
    if not connection:
        return None
    
    query = f"""
    SELECT * FROM itineraries
    WHERE trip_id = {trip_id}
    ORDER BY day
    """
    
    itineraries = execute_read_query(connection, query)
    connection.close()
    
    return itineraries

def get_user_trips(user_id):
    connection = create_connection()
    if not connection:
        return None
    
    query = f"""
    SELECT * FROM trips
    WHERE user_id = {user_id}
    ORDER BY start_date DESC
    """
    
    trips = execute_read_query(connection, query)
    connection.close()
    
    return trips

def add_expense(trip_id, category, amount, date):
    connection = create_connection()
    if not connection:
        return False, "Database connection failed"
    
    query = f"""
    INSERT INTO expenses (trip_id, category, amount, date)
    VALUES ({trip_id}, '{category}', {amount}, '{date}')
    """
    
    success = execute_query(connection, query)
    connection.close()
    
    if success:
        return True, "Expense added successfully"
    else:
        return False, "Failed to add expense"

def get_trip_expenses(trip_id):
    connection = create_connection()
    if not connection:
        return None
    
    query = f"""
    SELECT * FROM expenses
    WHERE trip_id = {trip_id}
    ORDER BY date
    """
    
    expenses = execute_read_query(connection, query)
    connection.close()
    
    return expenses

def get_trip_expense_summary(trip_id):
    connection = create_connection()
    if not connection:
        return None
    
    query = f"""
    SELECT category, SUM(amount) as total
    FROM expenses
    WHERE trip_id = {trip_id}
    GROUP BY category
    """
    
    summary = execute_read_query(connection, query)
    connection.close()
    
    return summary