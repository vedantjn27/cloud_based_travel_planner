# test_integration.py
import unittest
import os
import shutil
from datetime import datetime, timedelta

# Import our modules
from db_utils import create_connection, execute_query, execute_read_query
from user_management import register_user, login_user, get_user_by_id
from trip_planner import (create_trip, generate_itinerary, get_trip_itinerary, 
                         get_user_trips, add_expense, get_trip_expenses)
from api_integration import get_weather_data, get_place_recommendations, get_traffic_updates

class IntegrationTests(unittest.TestCase):
    
    def setUp(self):
        # Create a test user
        self.test_email = f"test_{datetime.now().strftime('%Y%m%d%H%M%S')}@example.com"
        self.test_name = "Test User"
        self.test_password = "test123456"
        
        # Register the test user
        success, message = register_user(self.test_name, self.test_email, self.test_password)
        
        if not success:
            self.fail(f"Failed to register test user: {message}")
        
        # Login the test user to get user ID
        success, user, message = login_user(self.test_email, self.test_password)
        
        if not success:
            self.fail(f"Failed to login test user: {message}")
        
        self.user_id = user['user_id']
        
        # Create temp directory for file uploads
        os.makedirs("temp", exist_ok=True)
    
    def tearDown(self):
        # Clean up any test data from database
        connection = create_connection()
        
        if connection:
            # Delete test user's data
            query = f"""
            DELETE FROM users WHERE email = '{self.test_email}'
            """
            execute_query(connection, query)
            connection.close()
        
        # Remove temp directory
        if os.path.exists("temp"):
            shutil.rmtree("temp")
    
    def test_database_connection(self):
        connection = create_connection()
        self.assertIsNotNone(connection, "Database connection failed")
        connection.close()
    
    def test_user_authentication(self):
        # Test login
        success, user, message = login_user(self.test_email, self.test_password)
        self.assertTrue(success, f"Login failed: {message}")
        self.assertEqual(user['name'], self.test_name, "User name mismatch")
        
        # Test get user by ID
        user = get_user_by_id(self.user_id)
        self.assertIsNotNone(user, "Failed to get user by ID")
        self.assertEqual(user['email'], self.test_email, "User email mismatch")
    
    def test_trip_creation_and_itinerary(self):
        # Create a test trip
        destination = "London"
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=3)).strftime("%Y-%m-%d")
        budget = 1000.0
        
        success, trip_id, message = create_trip(
            self.user_id, destination, start_date, end_date, budget
        )
        
        self.assertTrue(success, f"Trip creation failed: {message}")
        self.assertIsNotNone(trip_id, "Trip ID is None")
        
        # Generate itinerary
        success, message = generate_itinerary(trip_id)
        self.assertTrue(success, f"Itinerary generation failed: {message}")
        
        # Get itinerary
        itineraries = get_trip_itinerary(trip_id)
        self.assertIsNotNone(itineraries, "Failed to get itinerary")
        self.assertTrue(len(itineraries) > 0, "Itinerary is empty")
        
        # Get user trips
        trips = get_user_trips(self.user_id)
        self.assertIsNotNone(trips, "Failed to get user trips")
        self.assertTrue(len(trips) > 0, "User trips list is empty")
        self.assertEqual(trips[0]['destination'], destination, "Trip destination mismatch")
    
    def test_expense_tracking(self):
        # Create a test trip first
        destination = "Paris"
        start_date = datetime.now().strftime("%Y-%m-%d")
        end_date = (datetime.now() + timedelta(days=5)).strftime("%Y-%m-%d")
        budget = 2000.0
        
        success, trip_id, message = create_trip(
            self.user_id, destination, start_date, end_date, budget
        )
        
        self.assertTrue(success, f"Trip creation failed: {message}")
        
        # Add expenses
        categories = ["Accommodation", "Food", "Transportation"]
        amounts = [500.0, 200.0, 150.0]
        dates = [
            datetime.now().strftime("%Y-%m-%d"),
            (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d"),
            (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d")
        ]
        
        for i in range(3):
            success, message = add_expense(
                trip_id, categories[i], amounts[i], dates[i]
            )
            self.assertTrue(success, f"Failed to add expense: {message}")
        
        # Get expenses
        expenses = get_trip_expenses(trip_id)
        self.assertIsNotNone(expenses, "Failed to get expenses")
        self.assertEqual(len(expenses), 3, "Expense count mismatch")
        
        # Check total
        total = sum(amounts)
        expense_total = sum(float(expense['amount']) for expense in expenses)
        self.assertEqual(expense_total, total, "Expense total mismatch")
    
    def test_api_integrations(self):
        # Test weather API
        city = "London"
        weather = get_weather_data(city)
        self.assertIsNotNone(weather, "Failed to get weather data")
        self.assertIn('temperature', weather, "Weather data missing temperature")
        
        # Test places API
        places = get_place_recommendations(city)
        self.assertIsNotNone(places, "Failed to get place recommendations")
        
        # Test traffic API
        origin = "London Eye"
        destination = "Tower of London"
        traffic = get_traffic_updates(origin, destination)
        self.assertIsNotNone(traffic, "Failed to get traffic updates")

if __name__ == "__main__":
    unittest.main()