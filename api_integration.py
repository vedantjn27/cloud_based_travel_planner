# api_integrations.py
import requests
import json
from datetime import datetime

# Replace with your actual API keys
OPENWEATHER_API_KEY = "d3780264cfb1c21801fae3474a316f46"
PLACES_API_KEY = "AIzaSyCrutOe9XsRKqI0MxhhpTpezXT7UDqmAcI"  # Google Places API or similar

def get_weather_data(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OPENWEATHER_API_KEY}&units=metric"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200:
            weather_info = {
                "temperature": data["main"]["temp"],
                "description": data["weather"][0]["description"],
                "humidity": data["main"]["humidity"],
                "wind_speed": data["wind"]["speed"]
            }
            return weather_info
        else:
            print(f"Error: {data['message']}")
            return None
    except Exception as e:
        print(f"Error fetching weather data: {e}")
        return None

def get_place_recommendations(city, type_of_place="tourist_attraction", radius=5000):
    url = f"https://maps.googleapis.com/maps/api/place/textsearch/json?query={type_of_place}+in+{city}&radius={radius}&key={PLACES_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200 and data["status"] == "OK":
            places = []
            for place in data["results"][:10]:  # Limit to top 10 places
                places.append({
                    "name": place["name"],
                    "address": place.get("formatted_address", ""),
                    "rating": place.get("rating", 0)
                })
            return places
        else:
            print(f"Error: {data.get('status', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error fetching place recommendations: {e}")
        return None

def get_traffic_updates(origin, destination):
    # This would typically use a directions or traffic API
    # Simplified example using Google Directions API
    url = f"https://maps.googleapis.com/maps/api/directions/json?origin={origin}&destination={destination}&departure_time=now&key={PLACES_API_KEY}"
    
    try:
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200 and data["status"] == "OK":
            route = data["routes"][0]
            leg = route["legs"][0]
            
            traffic_info = {
                "distance": leg["distance"]["text"],
                "duration": leg["duration"]["text"],
                "traffic_duration": leg.get("duration_in_traffic", {}).get("text", "Unknown")
            }
            return traffic_info
        else:
            print(f"Error: {data.get('status', 'Unknown error')}")
            return None
    except Exception as e:
        print(f"Error fetching traffic updates: {e}")
        return None