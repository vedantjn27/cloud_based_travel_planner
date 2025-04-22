import streamlit as st
from db_utils import execute_query, execute_read_query, create_connection
from api_integration import get_weather_data

def generate_packing_list(trip_id, destination, start_date, end_date):
    """
    Generate a recommended packing list based on trip details.
    """
    # Get weather data to determine clothing needs
    weather = get_weather_data(destination)
    temperature = weather.get('temperature', 20) if weather else 20
    
    # Basic items everyone needs
    essentials = [
        ("Passport/ID", "Documents"),
        ("Credit/Debit Cards", "Documents"),
        ("Travel Insurance Info", "Documents"),
        ("Phone Charger", "Electronics"),
        ("Power Adapter", "Electronics"),
        ("Medications", "Health"),
        ("Toothbrush", "Toiletries"),
        ("Toothpaste", "Toiletries"),
        ("Deodorant", "Toiletries"),
        ("Shampoo/Conditioner", "Toiletries"),
        ("Soap/Body Wash", "Toiletries")
    ]
    
    # Clothing based on temperature and trip duration
    clothing = []
    trip_days = (end_date - start_date).days + 1
    
    # Adjust clothing based on temperature
    if temperature < 10:  # Cold
        clothing.extend([
            ("Winter Coat", "Clothing"),
            ("Sweaters/Fleece", "Clothing"),
            ("Thermal Underwear", "Clothing"),
            ("Gloves", "Clothing"),
            ("Scarf", "Clothing"),
            ("Winter Hat", "Clothing"),
            ("Warm Socks", "Clothing")
        ])
    elif temperature < 20:  # Cool
        clothing.extend([
            ("Light Jacket", "Clothing"),
            ("Long Sleeve Shirts", "Clothing"),
            ("Sweater", "Clothing"),
            ("Jeans/Pants", "Clothing")
        ])
    else:  # Warm
        clothing.extend([
            ("T-shirts", "Clothing"),
            ("Shorts", "Clothing"),
            ("Sunglasses", "Accessories"),
            ("Sunscreen", "Toiletries"),
            ("Hat", "Clothing"),
            ("Sandals", "Clothing")
        ])
    
    # Add basic clothing items regardless of temperature
    clothing.extend([
        ("Underwear", "Clothing"),
        ("Socks", "Clothing"),
        ("Comfortable Walking Shoes", "Clothing"),
        ("Pajamas", "Clothing")
    ])
    
    # Special items based on destination keywords
    special_items = []
    destination_lower = destination.lower()
    
    if any(word in destination_lower for word in ["beach", "ocean", "sea", "island"]):
        special_items.extend([
            ("Swimsuit", "Clothing"),
            ("Beach Towel", "Accessories"),
            ("Flip Flops", "Clothing"),
            ("Beach Bag", "Accessories")
        ])
    
    if any(word in destination_lower for word in ["mountain", "hiking", "trek", "national park"]):
        special_items.extend([
            ("Hiking Shoes", "Clothing"),
            ("Hiking Socks", "Clothing"),
            ("Water Bottle", "Accessories"),
            ("Backpack", "Accessories"),
            ("First Aid Kit", "Health")
        ])
    
    if any(word in destination_lower for word in ["rain", "tropical", "jungle"]):
        special_items.extend([
            ("Rain Jacket", "Clothing"),
            ("Umbrella", "Accessories"),
            ("Waterproof Bag", "Accessories")
        ])
    
    # Electronics and entertainment
    electronics = [
        ("Camera", "Electronics"),
        ("Headphones", "Electronics"),
        ("E-reader/Books", "Entertainment")
    ]
    
    # Combine all items
    all_items = essentials + clothing + special_items + electronics
    
    # Save items to database
    conn = create_connection()
    
    # First, delete any existing auto-generated items for this trip
    delete_query = """
    DELETE FROM packing_items 
    WHERE trip_id = %s AND custom = FALSE
    """
    execute_query(conn, delete_query, (trip_id,))
    
    # Insert new items
    insert_query = """
    INSERT INTO packing_items (trip_id, item_name, category, packed, custom)
    VALUES (%s, %s, %s, %s, %s)
    """
    
    for item_name, category in all_items:
        execute_query(conn, insert_query, (trip_id, item_name, category, False, False))
    
    return True, f"Generated {len(all_items)} packing items for your trip to {destination}."

def get_packing_list(trip_id):
    """
    Get the packing list for a specific trip.
    """
    conn = create_connection()
    query = """
    SELECT item_id, item_name, category, packed, custom
    FROM packing_items
    WHERE trip_id = %s
    ORDER BY category, item_name
    """
    
    items = execute_read_query(conn, query, (trip_id,))
    return items

def add_custom_item(trip_id, item_name, category):
    """
    Add a custom item to the packing list.
    """
    if not item_name or not category:
        return False, "Item name and category are required."
    
    conn = create_connection()
    query = """
    INSERT INTO packing_items (trip_id, item_name, category, packed, custom)
    VALUES (%s, %s, %s, %s, %s)
    """
    
    result = execute_query(conn, query, (trip_id, item_name, category, False, True))
    
    if result:
        return True, f"Added '{item_name}' to your packing list."
    else:
        return False, "Failed to add item. Please try again."

def update_item_status(item_id, packed):
    """
    Update the packed status of an item.
    """
    conn = create_connection()
    query = """
    UPDATE packing_items
    SET packed = %s
    WHERE item_id = %s
    """
    
    result = execute_query(conn, query, (packed, item_id))
    
    if result:
        return True
    else:
        return False

def delete_item(item_id):
    """
    Delete an item from the packing list.
    """
    conn = create_connection()
    query = """
    DELETE FROM packing_items
    WHERE item_id = %s
    """
    
    result = execute_query(conn, query, (item_id,))
    
    if result:
        return True, "Item removed from your packing list."
    else:
        return False, "Failed to remove item. Please try again."

def get_packing_progress(trip_id):
    """
    Get the packing progress for a trip.
    """
    conn = create_connection()
    query = """
    SELECT 
        COUNT(*) as total_items,
        SUM(CASE WHEN packed = TRUE THEN 1 ELSE 0 END) as packed_items
    FROM packing_items
    WHERE trip_id = %s
    """
    
    result = execute_read_query(conn, query, (trip_id,))
    
    if result and result[0]:
        total = result[0]['total_items']
        packed = result[0]['packed_items'] or 0
        
        if total > 0:
            progress = (packed / total) * 100
        else:
            progress = 0
            
        return {
            'total': total,
            'packed': packed,
            'progress': progress
        }
    else:
        return {
            'total': 0,
            'packed': 0,
            'progress': 0
        }