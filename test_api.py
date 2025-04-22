# test_apis.py
from api_integration import get_weather_data, get_place_recommendations, get_traffic_updates

def test_weather_api():
    city = "London"
    weather = get_weather_data(city)
    
    if weather:
        print(f"Weather in {city}:")
        print(f"Temperature: {weather['temperature']}°C")
        print(f"Description: {weather['description']}")
        print(f"Humidity: {weather['humidity']}%")
        print(f"Wind Speed: {weather['wind_speed']} m/s")
    else:
        print("Failed to get weather data")

def test_places_api():
    city = "Paris"
    places = get_place_recommendations(city)
    
    if places:
        print(f"Top attractions in {city}:")
        for i, place in enumerate(places, 1):
            print(f"{i}. {place['name']} - Rating: {place['rating']}")
    else:
        print("Failed to get place recommendations")

def test_traffic_api():
    origin = "Times Square, New York"
    destination = "Central Park, New York"
    traffic = get_traffic_updates(origin, destination)
    
    if traffic:
        print(f"Traffic information from {origin} to {destination}:")
        print(f"Distance: {traffic['distance']}")
        print(f"Normal Duration: {traffic['duration']}")
        print(f"Current Duration with Traffic: {traffic['traffic_duration']}")
    else:
        print("Failed to get traffic updates")

if __name__ == "__main__":
    test_weather_api()
    print("\n")
    test_places_api()
    print("\n")
    test_traffic_api()