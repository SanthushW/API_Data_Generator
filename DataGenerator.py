import requests
import json
from datetime import datetime, timedelta
from geopy.distance import geodesic

def fetch_route(api_key, origin, destination):
    url = "https://maps.googleapis.com/maps/api/directions/json"
    params = {
        "origin": origin,
        "destination": destination,
        "key": api_key,
        "mode": "transit"  # Try using "transit" or remove this parameter
    }
    response = requests.get(url, params=params)
    print(response.json())  # Print the full response for debugging
    if response.status_code != 200:
        raise Exception("API request failed with status code:", response.status_code)
    return response.json()

def extract_coordinates(route_data):
    if 'routes' not in route_data or len(route_data['routes']) == 0:
        raise ValueError("No routes found in the response.")
    if 'legs' not in route_data['routes'][0] or len(route_data['routes'][0]['legs']) == 0:
        raise ValueError("No legs found in the route.")
    
    steps = route_data['routes'][0]['legs'][0]['steps']
    if not steps:
        raise ValueError("No steps found in the leg.")
    
    coordinates = []
    for step in steps:
        start = step['start_location']
        end = step['end_location']
        coordinates.append((start['lat'], start['lng']))
        coordinates.append((end['lat'], end['lng']))
    return coordinates

def simulate_train_movement(coordinates, speed_kmph):
    if not coordinates:
        raise ValueError("No coordinates to simulate movement.")
    
    speed_mps = speed_kmph * 1000 / 3600
    movement_data = []
    current_time = datetime.now()

    for i in range(len(coordinates) - 1):
        start = coordinates[i]
        end = coordinates[i + 1]
        distance = geodesic(start, end).meters
        travel_time_seconds = distance / speed_mps
        current_time += timedelta(seconds=travel_time_seconds)
        movement_data.append({"time": current_time.isoformat(), "location": end})

    return movement_data

def save_as_geojson(movement_data, filename='train_movement.geojson'):
    geojson_data = {
        "type": "FeatureCollection",
        "features": []
    }
    for data in movement_data:
        feature = {
            "type": "Feature",
            "properties": {
                "time": data['time']
            },
            "geometry": {
                "type": "Point",
                "coordinates": [data['location'][1], data['location'][0]]
            }
        }
        geojson_data['features'].append(feature)

    with open(filename, 'w') as f:
        json.dump(geojson_data, f, indent=2)

api_key = "AIzaSyBYlmum_EIYi8B0nax7l-bJDLjJQjlhN-o"
origin = "Colombo Fort, Colombo, Sri Lanka"
destination = "Kandy Railway Station, Kandy, Sri Lanka"
speed_kmph = 60

try:
    route_data = fetch_route(api_key, origin, destination)
    coordinates = extract_coordinates(route_data)
    movement_data = simulate_train_movement(coordinates, speed_kmph)
    save_as_geojson(movement_data)
    print("Train location data generated and saved successfully!")
except Exception as e:
    print("An error occurred:", e)

