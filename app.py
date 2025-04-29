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
from streamlit.errors import StreamlitAPIException

# Import our modules
from db_utils import create_connection

from user_management import register_user, login_user, get_user_by_id, update_user_profile
from trip_planner import (create_trip, generate_itinerary, get_trip_itinerary, 
                         get_user_trips, add_expense, get_trip_expenses, 
                         get_trip_expense_summary)
from photo_manager import save_travel_photo, get_trip_photos
from api_integration import get_weather_data, get_place_recommendations, get_traffic_updates
# Import additional modules
from packing_list import (generate_packing_list, get_packing_list, 
                         add_custom_item, update_item_status, 
                         delete_item, get_packing_progress)
from travel_notes import (add_travel_note, get_travel_notes, get_travel_note,
                         update_travel_note, delete_travel_note, 
                         get_mood_counts, get_locations)
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
# Initialize session state variables if they don't exist
if 'editing_note' not in st.session_state:
    st.session_state.editing_note = None

if 'show_note_details' not in st.session_state:
    st.session_state.show_note_details = None

if 'note_title' not in st.session_state:
    st.session_state.note_title = ""

if 'note_content' not in st.session_state:
    st.session_state.note_content = ""

if 'note_location' not in st.session_state:
    st.session_state.note_location = ""

if 'note_mood' not in st.session_state:
    st.session_state.note_mood = ""   
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
    st.title("Tripfinity✈️")
    
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
            st.metric("Temperature🌡️", f"{weather['temperature']}°C")
        with col2:
            st.metric("Description📝", weather['description'])
        with col3:
            st.metric("Humidity🌬️", f"{weather['humidity']}%")
        with col4:
            st.metric("Wind Speed🌪️", f"{weather['wind_speed']} m/s")
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

def create_timeline_view(trip_id, itineraries):
    """
    Create a comprehensive visual timeline of the trip itinerary with enhanced styling
    and automatic activity categorization.
    """
    if not itineraries:
        st.info("No itinerary data available to display in timeline.")
        return
    
    # Get trip date information
    connection = create_connection()
    trip_query = "SELECT start_date, end_date, destination FROM trips WHERE trip_id = %s"
    trips = execute_read_query(connection, trip_query, (trip_id,))
    
    if not trips:
        st.error("Trip information not found.")
        return
    
    start_date = trips[0]['start_date']
    end_date = trips[0]['end_date']

    destination = trips[0]['destination']
    
    # Create a DataFrame for the timeline
    timeline_data = []
    
    # Icons for different types of activities (using emoji as placeholder)
    activity_icons = {
        "breakfast": "🍳",
        "lunch": "🍽️",
        "dinner": "🍷",
        "food": "🍲",
        "restaurant": "🍴",
        "cafe": "☕",
        "visit": "🏛️",
        "tour": "🚶",
        "museum": "🖼️",
        "gallery": "🎨",
        "beach": "🏖️",
        "hike": "🥾",
        "trek": "🏔️",
        "shopping": "🛍️",
        "market": "🛒",
        "show": "🎭",
        "concert": "🎵",
        "music": "🎶",
        "theater": "🎬",
        "movie": "🎦",
        "travel": "✈️",
        "flight": "🛫",
        "airport": "🛬",
        "check-in": "🏨",
        "check-out": "🧳",
        "hotel": "🛌",
        "relax": "🧘",
        "spa": "💆",
        "massage": "💆‍♂️",
        "explore": "🔍",
        "discover": "🧭",
        "swim": "🏊",
        "pool": "🏊‍♀️",
        "park": "🌳",
        "garden": "🌷",
        "nature": "🌿",
        "drive": "🚗",
        "rental": "🚙",
        "train": "🚆",
        "railway": "🚉",
        "bus": "🚌",
        "taxi": "🚕",
        "uber": "🚖",
        "boat": "⛵",
        "cruise": "🚢",
        "ferry": "⛴️",
        "temple": "🛕",
        "church": "⛪",
        "mosque": "🕌",
        "monument": "🗿",
        "landmark": "🏛️",
        "castle": "🏰",
        "palace": "👑",
        "photo": "📸",
        "photography": "📷",
        "default": "📍"
    }
    
    # Activity categories for filtering
    activity_categories = {
        "Meals": ["breakfast", "lunch", "dinner", "food", "restaurant", "cafe"],
        "Sightseeing": ["visit", "tour", "museum", "gallery", "monument", "landmark", "castle", "palace", "temple", "church", "mosque"],
        "Transportation": ["travel", "flight", "airport", "drive", "rental", "train", "bus", "taxi", "uber", "boat", "cruise", "ferry"],
        "Accommodation": ["hotel", "check-in", "check-out", "resort", "airbnb"],
        "Activities": ["hike", "trek", "swim", "show", "concert", "music", "theater", "movie", "relax", "spa", "massage", "explore", "discover", "shopping", "market"]
    }
    
    # Process itinerary data
    for item in itineraries:
        day_num = item['day']
        current_date = start_date + timedelta(days=day_num-1)
        date_str = current_date.strftime('%Y-%m-%d')
        weekday = current_date.strftime('%A')
        
        # Split activities into separate items
        activities = item['activity'].split('\n')
        for activity in activities:
            activity = activity.strip()
            if not activity:
                continue
                
            # Extract time if present (assuming format like "9:00 AM - Visit...")
            time_prefix = ""
            activity_text = activity
            
            if " - " in activity:
                parts = activity.split(" - ", 1)
                if any(time_indicator in parts[0].lower() for time_indicator in ["am", "pm", ":"]) and len(parts) > 1:
                    time_prefix = parts[0].strip()
                    activity_text = parts[1].strip()
            
            # Determine icon based on keywords in the activity
            icon = activity_icons["default"]
            activity_lower = activity_text.lower()
            
            for key, emoji in activity_icons.items():
                if key in activity_lower:
                    icon = emoji
                    break
                    
            # Determine category
            category = "Other"
            for cat_name, keywords in activity_categories.items():
                if any(keyword in activity_lower for keyword in keywords):
                    category = cat_name
                    break
            
            timeline_data.append({
                'date': date_str,
                'day': f"Day {day_num}",
                'weekday': weekday,
                'time': time_prefix,
                'activity': activity_text,
                'icon': icon,
                'category': category
            })
    
    if not timeline_data:
        st.info("No activities to display in timeline.")
        return
    
    # Create DataFrame
    df = pd.DataFrame(timeline_data)
    
    # Add filtering options
    st.subheader("Timeline Filters")
    col1, col2 = st.columns(2)
    
    with col1:
        # Day filter
        unique_days = sorted(df['day'].unique())
        selected_days = st.multiselect("Filter by Day", unique_days, default=unique_days)
        
    with col2:
        # Category filter
        unique_categories = sorted(df['category'].unique())
        selected_categories = st.multiselect("Filter by Activity Type", unique_categories, default=unique_categories)
    
    # Apply filters
    if selected_days or selected_categories:
        if selected_days:
            df = df[df['day'].isin(selected_days)]
        if selected_categories:
            df = df[df['category'].isin(selected_categories)]
    
    if df.empty:
        st.warning("No activities match your filter criteria.")
        return
        
    # Plot the timeline
    fig, ax = plt.subplots(figsize=(12, max(6, len(df) * 0.4)))
    
    # Set style
    plt.style.use('ggplot')
    
    # Create a colormap for different days
    unique_days = df['day'].unique()
    colors = sns.color_palette("husl", len(unique_days))
    day_colors = dict(zip(unique_days, colors))
    
    # Create a colormap for different categories
    unique_categories = df['category'].unique()
    category_colors = sns.color_palette("Dark2", len(unique_categories))
    cat_colors = dict(zip(unique_categories, category_colors))
    
    # Draw vertical line for the timeline
    ax.axvline(x=0, ymin=0, ymax=1, color='gray', alpha=0.5, linestyle='-', linewidth=2)
    
    # Plot each activity as a point with connecting lines
    current_day = None
    
    for i, (_, row) in enumerate(df.iterrows()):
        # Use day color or category color based on preference (uncomment one approach)
        # color = day_colors[row['day']]  # Color by day
        color = cat_colors[row['category']]  # Color by category
        
        # Draw day separator and header
        if current_day != row['day']:
            if current_day is not None:  # Not the first day
                ax.axhline(y=i-0.5, color='lightgray', linestyle='--', alpha=0.7)
            
            current_day = row['day']
            day_date = datetime.strptime(row['date'], '%Y-%m-%d').strftime('%b %d')
            day_header = f"{row['day']} ({row['weekday']}, {day_date})"
            ax.text(-5.5, i, day_header, fontsize=11, fontweight='bold', ha='left', va='center')
        
        # Activity point
        ax.scatter(0, i, s=120, color=color, edgecolor='white', zorder=2)
        
        # Time
        if row['time']:
            ax.text(-1, i, row['time'], fontsize=9, ha='right', va='center')
        
        # Icon and activity text
        icon_text = row['icon'] + " " if row['icon'] else ""
        activity_text = f"{icon_text}{row['activity']}"
        
        # Add category label as small text
        activity_with_category = f"{activity_text} [{row['category']}]"
        ax.text(0.5, i, activity_with_category, va='center', fontsize=10)
    
    # Add title
    trip_duration = (end_date - start_date).days + 1
    plt.suptitle(f"Trip to {destination} - {trip_duration} Days Itinerary", 
                fontsize=14, fontweight='bold', y=0.98)
    
    # Add legend for categories
    legend_elements = [plt.Line2D([0], [0], marker='o', color='w', 
                      label=category, markerfacecolor=cat_colors[category], markersize=10)
                      for category in unique_categories]
    ax.legend(handles=legend_elements, loc='upper right', title="Categories")
    
    # Set up the plot
    ax.set_ylim(-1, len(df))
    ax.set_xlim(-6, 12)  # Adjust based on text length
    ax.axis('off')
    ax.invert_yaxis()  # To have the first day at the top
    
    # Add a border
    plt.box(on=None)
    fig.tight_layout()
    
    # Show the plot
    st.pyplot(fig)
    
    # Add downloadable image option
    buf = io.BytesIO()
    fig.savefig(buf, format="png", dpi=300, bbox_inches="tight")
    buf.seek(0)
    
    st.download_button(
        label="Download Timeline Image",
        data=buf,
        file_name=f"trip_timeline_{destination}.png",
        mime="image/png"
    )
    
    # Add text version of timeline for accessibility
    if st.checkbox("Show text version of timeline"):
        st.subheader("Text Timeline")
        for day in sorted(df['day'].unique()):
            st.write(f"### {day}")
            day_df = df[df['day'] == day]
            for _, row in day_df.iterrows():
                time_str = f"{row['time']} - " if row['time'] else ""
                st.write(f"- {time_str}{row['icon']} {row['activity']} ({row['category']})")

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
    st.title(f"Trip to {trip['destination']}✈️")
    st.write(f"**Date:** {trip['start_date']} to {trip['end_date']}")
    st.write(f"**Budget:** ${trip['budget']}")
    
    # Weather Widget
    show_weather_widget(trip['destination'])
    
    # Tabs for different sections
    tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["Itinerary", "Expenses", "Photos", "Recommendations", "Packing List", "Travel Journal"])
    
    # Inside the tab1 (Itinerary) section of show_trip_details function:

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
            # Add Timeline View toggle
            show_timeline = st.checkbox("Show Timeline View", value=True)
        
            if show_timeline:
                st.subheader("Trip Timeline🗓️")
                # Create the timeline visualization
                create_timeline_view(trip_id, itineraries)
        
            # Keep the existing day-by-day view
            st.subheader("Day-by-Day Itinerary")
            for itinerary in itineraries:
                st.subheader(f"Day {itinerary['day']}")
                st.write(itinerary['activity'])
    
    # Tab 2: Expenses
    with tab2:
        st.subheader("Add Expense💰")
        
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
        
        st.subheader("Expense Summary📋")
        
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
        st.subheader("Upload Travel Photo📸")
    
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
    
        st.subheader("Trip Memories🖼️")
    
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
        st.subheader(f"Recommendations for {trip['destination']}💡")
        
        # Get place recommendations
        attractions = get_place_recommendations(trip['destination'], "tourist_attraction")
        restaurants = get_place_recommendations(trip['destination'], "restaurant")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("### Top Attractions🌍")
            
            if attractions:
                for i, place in enumerate(attractions[:5], 1):
                    st.write(f"**{i}. {place['name']}**")
                    st.write(f"Rating: {place.get('rating', 'N/A')}/5")
                    st.write(f"Address: {place.get('address', 'N/A')}")
                    st.write("---")
            else:
                st.info("Could not fetch attraction recommendations.")
        
        with col2:
            st.write("### Top Restaurants🍽️")
            
            if restaurants:
                for i, place in enumerate(restaurants[:5], 1):
                    st.write(f"**{i}. {place['name']}**")
                    st.write(f"Rating: {place.get('rating', 'N/A')}/5")
                    st.write(f"Address: {place.get('address', 'N/A')}")
                    st.write("---")
            else:
                st.info("Could not fetch restaurant recommendations.")
        
        # Traffic updates between key locations
        st.subheader("Traffic Updates🚗")
        
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

    with tab5:
        st.subheader("Packing List🧳 ")
    
        # Import packing list functions at the top of your file
        from packing_list import (generate_packing_list, get_packing_list, 
                                add_custom_item, update_item_status, 
                                delete_item, get_packing_progress)
    
        # Get trip details
        start_date = trips[0]['start_date']
        end_date = trips[0]['end_date']

    
        # Show packing progress
        progress = get_packing_progress(trip_id)
    
        col1, col2, col3 = st.columns(3)
    
        with col1:
            st.metric("Total Items", float(progress['total']))

        with col2:
            st.metric("Packed Items", float(progress['packed']))

    
        with col3:
            st.progress(float(progress['progress']) / 100)

            st.write(f"Packing Progress: {progress['progress']:.1f}%")
    
        # Generate/regenerate packing list button
        if st.button("Generate Packing List", key="generate_packing"):
            success, message = generate_packing_list(
                trip_id, 
                trip['destination'], 
                start_date, 
                end_date
            )
        
            if success:
                st.success(message)
                st.rerun()
            else:
                st.error(message)
    
        # Add custom item form
        st.subheader("Add Custom Item")
    
        col1, col2, col3 = st.columns([3, 2, 1])
    
        with col1:
            custom_item = st.text_input("Item Name", key="custom_item_name")
    
        with col2:
            custom_category = st.selectbox("Category", [
                "Clothing", "Electronics", "Toiletries", 
                "Documents", "Health", "Accessories", "Entertainment", "Other"
            ], key="custom_item_category")
    
        with col3:
            if st.button("Add Item") and custom_item:
                success, message = add_custom_item(trip_id, custom_item, custom_category)
            
                if success:
                    st.success(message)
                    st.rerun()
                else:
                    st.error(message)
    
        # Display packing list
        items = get_packing_list(trip_id)
    
        if items:
            # Group items by category
            categories = {}
            for item in items:
                category = item['category']
                if category not in categories:
                    categories[category] = []
                categories[category].append(item)
        
            # Display items by category
            for category, cat_items in categories.items():
                with st.expander(f"{category} ({len(cat_items)})", expanded=True):
                    for item in cat_items:
                        col1, col2 = st.columns([6, 1])
                    
                        with col1:
                            # Checkbox for packed status
                            packed = st.checkbox(
                                item['item_name'],
                                value=item['packed'],
                                key=f"item_{item['item_id']}"
                            )
                        
                            if packed != item['packed']:
                                update_item_status(item['item_id'], packed)
                                st.rerun()
                    
                        with col2:
                            # Delete button (only for custom items or if needed for all)
                            if item['custom'] and st.button("🗑️", key=f"delete_{item['item_id']}"):
                                success, message = delete_item(item['item_id'])
                            
                                if success:
                                    st.success(message)
                                    st.rerun()
                                else:
                                    st.error(message)
        else:
            st.info("No items in your packing list yet. Click 'Generate Packing List' to get started.")

    with tab6:
        # Add note form
        st.subheader("Add New Journal Entry📖")

        # Date and Mood
        col1, col2 = st.columns(2)

        with col1:
            note_date = st.date_input("Date", value=datetime.now().date(), key="note_date")

        with col2:
            mood_options = ["Happy", "Excited", "Relaxed", "Tired", "Overwhelmed", "Inspired", "Grateful", "Adventurous"]
            note_mood = st.selectbox("Mood", ["", *mood_options], key="note_mood")

        # Title and Location
        note_title = st.text_input("Title", value=st.session_state.get('note_title', ''), key="note_title")
        note_location = st.text_input("Location", value=st.session_state.get('note_location', ''), key="note_location")

        # Content
        note_content = st.text_area("Journal Entry", value=st.session_state.get('note_content', ''), height=150, key="note_content")

        # Submit button
        if st.button("Save Journal Entry"):
        # Check if title and content are not empty
            if st.session_state.note_title and st.session_state.note_content:
                success, message, _ = add_travel_note(
                    trip_id,
                    st.session_state.note_title,  # Use session state values here
                    st.session_state.note_content,
                    note_date,
                    st.session_state.note_location,
                    st.session_state.note_mood
                )
        
                if success:
                    st.success(message)
                    # Clear form fields in session state
                    try:
                        if "note_title" not in st.session_state:
                            st.session_state.note_title = ""
                    except Exception as e:
                        st.error(f"skipping reset {e}")


                    if "note_content" not in st.session_state:
                        st.session_state["note_content"] = ""
                    if "note_location" not in st.session_state:
                        st.session_state["note_location"] = ""
                    if "note_mood" not in st.session_state:
                        st.session_state["note_mood"] = ""
                        st.rerun()

                else:
                    st.error(message)
            else:
                st.error("Title and content are required.")

        # Edit note form
        if st.session_state.editing_note:
            note_id = st.session_state.editing_note
            st.subheader("Edit Journal Entry")

            # Date and Mood
            col1, col2 = st.columns(2)

            with col1:
                edit_date = st.date_input("Date", value=st.session_state.note_date, key="edit_date")

            with col2:
                mood_options = ["Happy", "Excited", "Relaxed", "Tired", "Overwhelmed", "Inspired", "Grateful", "Adventurous"]
                edit_mood = st.selectbox("Mood", ["", *mood_options], index=mood_options.index(st.session_state.note_mood)+1 if st.session_state.note_mood in mood_options else 0, key="edit_mood")

            # Title and Location
            edit_title = st.text_input("Title", value=st.session_state.note_title, key="edit_title")
            edit_location = st.text_input("Location", value=st.session_state.note_location, key="edit_location")

            # Content
            edit_content = st.text_area("Journal Entry", value=st.session_state.note_content, height=150, key="edit_content")

            # Submit and Cancel buttons
            col1, col2 = st.columns(2)

            with col1:
                if st.button("Update Journal Entry"):
                    if edit_title and edit_content:
                        success, message = update_travel_note(
                            note_id,
                            edit_title,
                            edit_content,
                            edit_date,
                            edit_location,
                            edit_mood
                        )

                        if success:
                            st.success(message)
                            st.session_state.editing_note = None
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Title and content are required.")

            with col2:
                if st.button("Cancel"):
                    st.session_state.editing_note = None
                    st.rerun()


    
        # Get travel notes
        notes = get_travel_notes(trip_id)
    
        # Display notes
        if notes:
            st.subheader("Your Journal Entries")
        
            # Filters
            col1, col2 = st.columns(2)
        
            with col1:
                # Get all unique locations
                locations = get_locations(trip_id)
                filter_location = st.selectbox("Filter by Location", ["All Locations", *locations], key="filter_location")
        
            with col2:
                # Get all unique moods
                moods = [note['mood'] for note in notes if note['mood']]
                unique_moods = list(set(moods))
                filter_mood = st.selectbox("Filter by Mood", ["All Moods", *unique_moods], key="filter_mood")
        
            # Filter notes
            filtered_notes = notes
            if filter_location != "All Locations":
                filtered_notes = [note for note in filtered_notes if note['location'] == filter_location]
        
            if filter_mood != "All Moods":
                filtered_notes = [note for note in filtered_notes if note['mood'] == filter_mood]
        
            # Note cards
            for note in filtered_notes:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                
                    with col1:
                        # Format date
                        # If note['date'] is already a datetime object, no need to parse it again
                        date_str = note['date'].strftime('%b %d, %Y')

                    
                        # Title with date and mood
                        header = f"### {note['title']}"
                        st.markdown(header)
                    
                        # Metadata
                        meta = f"📅 {date_str}"
                        if note['location']:
                            meta += f" | 📍 {note['location']}"
                        if note['mood']:
                            meta += f" | 🧠 {note['mood']}"
                        st.markdown(meta)
                
                    with col2:
                        # Action buttons
                        if st.button("View", key=f"view_{note['note_id']}"):
                            st.session_state.show_note_details = note['note_id']
                            st.rerun()
                
                    # Preview of content (first 100 chars)
                    preview = note['content'][:100] + "..." if len(note['content']) > 100 else note['content']
                    st.markdown(preview)
                    st.markdown("---")
        
            # Display mood stats
            mood_counts = get_mood_counts(trip_id)
            if mood_counts:
                st.subheader("Mood Summary😊")
            
                # Create data for pie chart
                moods = [mc['mood'] for mc in mood_counts]
                counts = [mc['count'] for mc in mood_counts]
            
                # Create pie chart
                fig, ax = plt.subplots()
                ax.pie(counts, labels=moods, autopct='%1.1f%%')
                ax.set_title('Journal Entries by Mood')
                st.pyplot(fig)
        else:
            st.info("No journal entries yet. Add your first entry above!")
    
        # Note detail view
        if st.session_state.show_note_details:
            note_id = st.session_state.show_note_details
            note = get_travel_note(note_id)
        
            if note:
                st.sidebar.subheader("Journal Entry Details")
            
                # Format date
                # If note['date'] is already a datetime object, no need to parse it again
                date_str = note['date'].strftime('%b %d, %Y')

            
                st.sidebar.markdown(f"### {note['title']}")
                st.sidebar.markdown(f"**Date:** {date_str}")
            
                if note['location']:
                    st.sidebar.markdown(f"**Location:** {note['location']}")
            
                if note['mood']:
                    st.sidebar.markdown(f"**Mood:** {note['mood']}")
            
                st.sidebar.markdown("### Entry")
                st.sidebar.markdown(note['content'])
            
                # Edit and Delete buttons
                col1, col2 = st.sidebar.columns(2)
            
                with col1:
                    if st.button("Edit", key=f"edit_{note_id}"):
                        st.session_state.editing_note = note_id
                        # Pre-fill form
                        st.session_state.note_title = note['title']
                        st.session_state.note_content = note['content']
                        st.session_state.note_location = note['location'] or ""
                        st.session_state.note_mood = note['mood'] or ""
                        st.session_state.note_date = datetime.strptime(note['date'], '%Y-%m-%d').date()
                        st.session_state.show_note_details = None
                        st.rerun()
            
                with col2:
                    if st.button("Delete", key=f"delete_{note_id}"):
                        success, message = delete_travel_note(note_id)
                    
                        if success:
                            st.sidebar.success(message)
                            st.session_state.show_note_details = None
                            st.rerun()
                        else:
                            st.sidebar.error(message)
            
                if st.sidebar.button("Close", key="close_note"):
                    st.session_state.show_note_details = None
                    st.rerun()
    
        # Edit note form
        if st.session_state.editing_note:
            note_id = st.session_state.editing_note
            st.subheader("Edit Journal Entry")
        
            # Date and Mood
            col1, col2 = st.columns(2)
        
            with col1:
                edit_date = st.date_input("Date", value=st.session_state.note_date, key="edit_date")
        
            with col2:
                mood_options = ["Happy", "Excited", "Relaxed", "Tired", "Overwhelmed", "Inspired", "Grateful", "Adventurous"]
                edit_mood = st.selectbox("Mood", ["", *mood_options], index=mood_options.index(st.session_state.note_mood)+1 if st.session_state.note_mood in mood_options else 0, key="edit_mood")
        
            # Title and Location
            edit_title = st.text_input("Title", value=st.session_state.note_title, key="edit_title")
            edit_location = st.text_input("Location", value=st.session_state.note_location, key="edit_location")
        
            # Content
            edit_content = st.text_area("Journal Entry", value=st.session_state.note_content, height=150, key="edit_content")
        
            # Submit and Cancel buttons
            col1, col2 = st.columns(2)
        
            with col1:
                if st.button("Update Journal Entry"):
                    if edit_title and edit_content:
                        success, message = update_travel_note(
                            note_id,
                            edit_title,
                            edit_content,
                            edit_date,
                            edit_location,
                            edit_mood
                        )
                    
                        if success:
                            st.success(message)
                            st.session_state.editing_note = None
                            st.rerun()
                        else:
                            st.error(message)
                    else:
                        st.error("Title and content are required.")
        
            with col2:
                if st.button("Cancel"):
                    st.session_state.editing_note = None
                    st.rerun()                    

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