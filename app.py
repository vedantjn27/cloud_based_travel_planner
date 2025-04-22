# app.py
import streamlit as st
import os
import pandas as pd
from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import seaborn as sns
from db_utils import execute_read_query
from PIL import Image
import io

# Import our modules
from db_utils import create_connection
from user_management import register_user, login_user, get_user_by_id, update_user_profile
from trip_planner import (create_trip, generate_itinerary, get_trip_itinerary, 
                         get_user_trips, add_expense, get_trip_expenses, 
                         get_trip_expense_summary)
from photo_manager import save_travel_photo, get_trip_photos
from api_integration import get_weather_data, get_place_recommendations, get_traffic_updates

# Set page configuration
st.set_page_config(
    page_title="AI Travel Planner",
    page_icon="✈️",
    layout="wide"
)

# Initialize session state
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user_id' not in st.session_state:
    st.session_state.user_id = None
if 'user_name' not in st.session_state:
    st.session_state.user_name = None
if 'current_trip_id' not in st.session_state:
    st.session_state.current_trip_id = None

# Authentication Functions
def login_callback():
    email = st.session_state.login_email
    password = st.session_state.login_password
    
    success, user, message = login_user(email, password)
    
    if success:
        st.session_state.logged_in = True
        st.session_state.user_id = user['user_id']
        st.session_state.user_name = user['name']
        st.success(message)
    else:
        st.error(message)

def register_callback():
    name = st.session_state.reg_name
    email = st.session_state.reg_email
    password = st.session_state.reg_password
    
    success, message = register_user(name, email, password)
    
    if success:
        st.success(message)
        st.session_state.show_login = True
    else:
        st.error(message)

def logout():
    st.session_state.logged_in = False
    st.session_state.user_id = None
    st.session_state.user_name = None
    st.session_state.current_trip_id = None

# Login/Register Page
def show_auth_page():
    st.title("AI Travel Planner")
    
    # Toggle between login and register
    if 'show_login' not in st.session_state:
        st.session_state.show_login = True
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("Login", key="toggle_login"):
            st.session_state.show_login = True
    
    with col2:
        if st.button("Register", key="toggle_register"):
            st.session_state.show_login = False
    
    if st.session_state.show_login:
        st.subheader("Login")
        st.text_input("Email", key="login_email")
        st.text_input("Password", type="password", key="login_password")
        st.button("Login", on_click=login_callback, key="login_submit")
    else:
        st.subheader("Register")
        st.text_input("Name", key="reg_name")
        st.text_input("Email", key="reg_email")
        st.text_input("Password", type="password", key="reg_password")
        st.button("Register", on_click=register_callback, key="register_submit")

# Dashboard Page Components
def show_weather_widget(city):
    weather = get_weather_data(city)
    
    if weather:
        st.subheader(f"Weather in {city}")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Temperature", f"{weather['temperature']}°C")
        with col2:
            st.metric("Description", weather['description'])
        with col3:
            st.metric("Humidity", f"{weather['humidity']}%")
        with col4:
            st.metric("Wind Speed", f"{weather['wind_speed']} m/s")
    else:
        st.warning(f"Could not fetch weather data for {city}")

def show_trip_list():
    trips = get_user_trips(st.session_state.user_id)
    
    if not trips:
        st.info("You haven't created any trips yet.")
        return
    
    for trip in trips:
        col1, col2, col3 = st.columns([3, 1, 1])
        
        with col1:
            st.write(f"**{trip['destination']}**")
            st.write(f"{trip['start_date']} to {trip['end_date']}")
        
        with col2:
            st.write(f"Budget: ${trip['budget']}")
        
        with col3:
            if st.button("View", key=f"view_trip_{trip['trip_id']}"):
                st.session_state.current_trip_id = trip['trip_id']
                st.rerun()

def add_trip_form():
    st.subheader("Create New Trip")
    
    col1, col2 = st.columns(2)
    
    with col1:
        destination = st.text_input("Destination", key="new_trip_destination")
        budget = st.number_input("Budget ($)", min_value=0.0, key="new_trip_budget")
    
    with col2:
        start_date = st.date_input("Start Date", key="new_trip_start_date")
        end_date = st.date_input("End Date", key="new_trip_end_date")
    
    if st.button("Create Trip"):
        if destination and budget > 0 and start_date <= end_date:
            success, trip_id, message = create_trip(
                st.session_state.user_id,
                destination,
                start_date.strftime("%Y-%m-%d"),
                end_date.strftime("%Y-%m-%d"),
                budget
            )
            
            if success:
                st.success(message)
                # Generate itinerary for the new trip
                success, itinerary_message = generate_itinerary(trip_id)
                
                if success:
                    st.success(itinerary_message)
                    st.session_state.current_trip_id = trip_id
                    st.rerun()
                else:
                    st.error(itinerary_message)
            else:
                st.error(message)
        else:
            st.error("Please fill in all fields correctly.")
def show_trip_details(trip_id):
    # Get trip details using parameterized query
    connection = create_connection()
    trip_query = "SELECT * FROM trips WHERE trip_id = %s"
    trips = execute_read_query(connection, trip_query, (trip_id,))
    
    if not trips:
        st.error("Trip not found.")
        return
    
    trip = trips[0]
    
    # Trip Header
    st.title(f"Trip to {trip['destination']}")
    st.write(f"**Date:** {trip['start_date']} to {trip['end_date']}")
    st.write(f"**Budget:** ${trip['budget']}")
    
    # Weather Widget
    show_weather_widget(trip['destination'])
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4 = st.tabs(["Itinerary", "Expenses", "Photos", "Recommendations"])
    
    # Tab 1: Itinerary
    with tab1:
        itineraries = get_trip_itinerary(trip_id)
        
        if not itineraries:
            st.info("No itinerary found for this trip.")
            
            if st.button("Generate Itinerary"):
                success, message = generate_itinerary(trip_id)
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
        else:
            for itinerary in itineraries:
                st.subheader(f"Day {itinerary['day']}")
                st.write(itinerary['activity'])
    
    # Tab 2: Expenses
    with tab2:
        st.subheader("Add Expense")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            category = st.selectbox("Category", [
                "Accommodation", "Food", "Transportation", 
                "Activities", "Shopping", "Other"
            ])
        
        with col2:
            amount = st.number_input("Amount ($)", min_value=0.0)
        
        with col3:
            date = st.date_input("Date")
        
        if st.button("Add Expense"):
            if category and amount > 0:
                success, message = add_expense(
                    trip_id,
                    category,
                    amount,
                    date.strftime("%Y-%m-%d")
                )
                
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please fill in all fields correctly.")
        
        st.subheader("Expense Summary")
        
        expenses = get_trip_expenses(trip_id)
        summary = get_trip_expense_summary(trip_id)
        
        if expenses:
            expense_df = pd.DataFrame(expenses)
            st.dataframe(expense_df[["category", "amount", "date"]])
            
            if summary:
                fig, ax = plt.subplots()
                categories = [row['category'] for row in summary]
                amounts = [float(row['total']) for row in summary]
                
                ax.pie(amounts, labels=categories, autopct='%1.1f%%')
                ax.set_title('Expense Breakdown')
                st.pyplot(fig)
                
                total_spent = sum(amounts)
                remaining = float(trip['budget']) - total_spent
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric("Total Spent", f"${total_spent:.2f}")
                
                with col2:
                    st.metric("Remaining Budget", f"${remaining:.2f}")
        else:
            st.info("No expenses recorded for this trip yet.")
    
    with tab3:
        st.subheader("Upload Travel Photo")
    
        photo_file = st.file_uploader("Choose a photo", type=["jpg", "jpeg", "png"])
        description = st.text_input("Description")
    
        if st.button("Upload") and photo_file is not None:
            success, photo_id, message = save_travel_photo(
            st.session_state.user_id,
                trip_id,
                photo_file,
                description
            )
        
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
        st.subheader("Travel Photos")
    
        photos = get_trip_photos(trip_id)
    
        if photos:
            cols = st.columns(3)
            for i, photo in enumerate(photos):
                with cols[i % 3]:
                    try:
                        if photo.get('file_data'):
                            img = Image.open(io.BytesIO(photo['file_data']))
                            st.image(
                                img,
                                caption=photo.get('description', 'No description'),
                                use_container_width=True
                            )
                        else:
                            st.warning("No image data available")
                            st.write(f"Filename: {photo.get('filename', 'Unknown')}")
                    except Exception as e:
                        st.error(f"Error displaying image: {str(e)}")
                        st.write(f"Filename: {photo.get('filename', 'Unknown')}")
        else:
            st.info("No photos uploaded for this trip yet.")
            
    # Tab 4: Recommendations
    with tab4:
        st.subheader(f"Recommendations for {trip['destination']}")
        
        # Get place recommendations
        attractions = get_place_recommendations(trip['destination'], "tourist_attraction")
        restaurants = get_place_recommendations(trip['destination'], "restaurant")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Top Attractions")
            
            if attractions:
                for i, place in enumerate(attractions[:5], 1):
                    st.write(f"**{i}. {place['name']}**")
                    st.write(f"Rating: {place.get('rating', 'N/A')}/5")
                    st.write(f"Address: {place.get('address', 'N/A')}")
                    st.write("---")
            else:
                st.info("Could not fetch attraction recommendations.")
        
        with col2:
            st.write("### Top Restaurants")
            
            if restaurants:
                for i, place in enumerate(restaurants[:5], 1):
                    st.write(f"**{i}. {place['name']}**")
                    st.write(f"Rating: {place.get('rating', 'N/A')}/5")
                    st.write(f"Address: {place.get('address', 'N/A')}")
                    st.write("---")
            else:
                st.info("Could not fetch restaurant recommendations.")
        
        # Traffic updates between key locations
        st.subheader("Traffic Updates")
        
        origin = st.text_input("Origin", value=f"Airport, {trip['destination']}")
        destination = st.text_input("Destination", value=f"City Center, {trip['destination']}")
        
        if st.button("Get Traffic Updates"):
            traffic = get_traffic_updates(origin, destination)
            
            if traffic:
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Distance", traffic['distance'])
                
                with col2:
                    st.metric("Normal Duration", traffic['duration'])
                
                with col3:
                    st.metric("Current Duration", traffic['traffic_duration'])
            else:
                st.error("Could not fetch traffic updates.")

# Main app flow
def main():
    # Add sidebar
    with st.sidebar:
        if st.session_state.logged_in:
            st.write(f"Welcome, {st.session_state.user_name}!")
            
            if st.button("Dashboard"):
                st.session_state.current_trip_id = None
            
            if st.button("Logout"):
                logout()
                st.rerun()
        else:
            st.write("Please login or register")
    
    # Main content
    if not st.session_state.logged_in:
        show_auth_page()
    else:
        if st.session_state.current_trip_id:
            show_trip_details(st.session_state.current_trip_id)
        else:
            st.title(f"Welcome, {st.session_state.user_name}!")
            
            tab1, tab2 = st.tabs(["My Trips", "Create New Trip"])
            
            with tab1:
                show_trip_list()
            
            with tab2:
                add_trip_form()

if __name__ == "__main__":
    main()