import googlemaps
import geojson
import time
import random
from datetime import datetime, timedelta
import json
import polyline  # Add this import

# Initialize Google Maps client
gmaps = googlemaps.Client(key='AIzaSyBYlmum_EIYi8B0nax7l-bJDLjJQjlhN-o')

# Load the GeoJSON file containing train stations
with open('SLRailwayRoutes.geojson', encoding='utf-8') as f:
    stations = geojson.load(f)

def get_random_station():
    return random.choice(stations['features'])

def get_route(origin, destination):
    """Get the route between two points using Google Maps API."""
    print(f"Requesting route from {origin} to {destination}")
    directions_result = gmaps.directions(
        origin=f"{origin['latitude']},{origin['longitude']}",
        destination=f"{destination['latitude']},{destination['longitude']}",
        mode="transit",
        transit_mode="rail",
        units="metric"
    )
    if not directions_result:
        print("No directions found.")
        return []

    print(f"Directions found: {directions_result}")
    # Extract the polyline from the directions result
    polyline_str = directions_result[0]['overview_polyline']['points']
    return polyline.decode(polyline_str)  # Use the polyline library's decode function

def simulate_train_route(train_id, route, speed_kmph, start_time):
    """Simulate the train moving along the route at a certain speed."""
    if not route:
        print(f"No route data for train {train_id}")
        return None

    geojson_route = {
        "type": "Feature",
        "properties": {
            "train_id": train_id,
            "start_time": start_time.isoformat()
        },
        "geometry": {
            "type": "LineString",
            "coordinates": []
        }
    }
    
    # Convert speed to meters per minute
    speed_mpm = (speed_kmph * 1000) / 60
    
    for i in range(len(route) - 1):
        start_point = route[i]
        end_point = route[i + 1]
        # Calculate the distance between points
        distance = gmaps.distance_matrix(
            origins=[start_point],
            destinations=[end_point],
            mode="walking"
        )['rows'][0]['elements'][0]['distance']['value']
        
        travel_time = distance / speed_mpm
        geojson_route['geometry']['coordinates'].append([start_point[1], start_point[0]])
        
        print(f"Train {train_id} at {start_point} moving to {end_point}.")
        
        time.sleep(travel_time * 5)  # Simulate the time delay
    
    return geojson_route

def generate_train_data(num_trains, speed_kmph, output_file):
    """Generate train tracking data for multiple trains."""
    trains_data = []
    start_time = datetime.now()
    
    for train_id in range(num_trains):
        origin_station = get_random_station()
        destination_station = get_random_station()
        
        origin = origin_station['geometry']['coordinates']
        destination = destination_station['geometry']['coordinates']
        
        route = get_route(
            {'latitude': origin[1], 'longitude': origin[0]},
            {'latitude': destination[1], 'longitude': destination[0]}
        )
        
        train_route_data = simulate_train_route(train_id, route, speed_kmph, start_time)
        if train_route_data:
            trains_data.append(train_route_data)
    
    if trains_data:
        with open(output_file, 'w', encoding='utf-8') as f:
            geojson.dump(geojson.FeatureCollection(trains_data), f)
        print(f"Data written to {output_file}")
    else:
        print("No data to write.")

# Configuration
NUM_TRAINS = 2
TRAIN_SPEED_KMPH = 160  # Adjust speed as needed
OUTPUT_FILE = 'train_tracking_data.geojson'

# Generate the train data
generate_train_data(NUM_TRAINS, TRAIN_SPEED_KMPH, OUTPUT_FILE)
