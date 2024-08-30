import geojson
import time
from datetime import datetime, timedelta
import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from pymongo import MongoClient

# Load the GeoJSON files
with open('SLRailwayRoutes.geojson', encoding='utf-8') as f:
    routes = geojson.load(f)

with open('hotosm_lka_railways_lines.geojson', encoding='utf-8') as f:
    railway_lines = geojson.load(f)

def find_nearest_line(origin, destination):
    """Find the nearest railway line to the train's route."""
    closest_line = None
    closest_distance = float('inf')
    
    for feature in railway_lines['features']:
        line_coords = feature['geometry']['coordinates']
        
        # Simplified method to find the closest line segment
        for i in range(len(line_coords) - 1):
            line_start = line_coords[i]
            line_end = line_coords[i + 1]
            
            # Check if this segment is closer to the origin and destination
            distance_to_start = haversine(origin, line_start)
            distance_to_end = haversine(destination, line_end)
            
            if distance_to_start + distance_to_end < closest_distance:
                closest_distance = distance_to_start + distance_to_end
                closest_line = line_coords
    
    return closest_line

def haversine(coord1, coord2):
    """Calculate the great-circle distance between two points on the Earth."""
    from math import radians, cos, sin, sqrt, atan2
    
    lat1, lon1 = coord1
    lat2, lon2 = coord2
    
    R = 6371000  # Radius of the Earth in meters
    phi1, phi2 = radians(lat1), radians(lat2)
    delta_phi = radians(lat2 - lat1)
    delta_lambda = radians(lon2 - lon1)
    
    a = sin(delta_phi / 2.0) ** 2 + cos(phi1) * cos(phi2) * sin(delta_lambda / 2.0) ** 2
    c = 2 * atan2(sqrt(a), sqrt(1 - a))
    
    return R * c

def simulate_train_route(train_data, speed_kmph, start_time):
    """Simulate the train moving along the route at a certain speed."""
    train_id = train_data['properties']['train_id']
    origin_coords = train_data['geometry']['coordinates'][0]
    destination_coords = train_data['geometry']['coordinates'][-1]

    origin = {'latitude': origin_coords[1], 'longitude': origin_coords[0]}
    destination = {'latitude': destination_coords[1], 'longitude': destination_coords[0]}
    
    print(f"Simulating route: {train_id}")
    
    # Find the nearest railway line
    route = find_nearest_line(origin_coords, destination_coords)

    if not route:
        print(f"No suitable railway line found for train {train_id}.")
        return None

    geojson_route = {
        "type": "Feature",
        "properties": {
            "train_id": train_id,
            "route": train_data['properties'].get('route'),  # Ensure 'route' is included
            "timestamps": [],
            "start_time": start_time.isoformat(),
            "origin": origin,  # Ensure origin is included
            "destination": destination,  # Ensure destination is included
        },
        "geometry": {
            "type": "LineString",
            "coordinates": []
        }
    }
    
    # Convert speed to meters per minute
    speed_mpm = (speed_kmph * 1000) / 60
    
    current_time = start_time
    
    for i in range(len(route) - 1):
        start_point = route[i]
        end_point = route[i + 1]
        
        # Calculate the distance between points
        distance = haversine(start_point, end_point)
        travel_time = distance / speed_mpm
        
        geojson_route['geometry']['coordinates'].append(start_point)
        geojson_route['properties']['timestamps'].append(current_time.isoformat())

        print(f"Train {train_id} moving from {train_data['properties'].get('route')} cordinates: {start_point} to {end_point} at {current_time}.")
        
        time.sleep(0.1)  # Simulate the passage of one minute
        current_time += timedelta(minutes=1)

    # Add the final point and timestamp to the route
    geojson_route['geometry']['coordinates'].append(route[-1])
    geojson_route['properties']['timestamps'].append(current_time.isoformat())
    
    return geojson_route


def generate_train_data(output_file, num_simultaneous_trains=5):
    """Generate train tracking data for multiple trains concurrently."""
    trains_data = []
    start_time = datetime.now()
    
    with ThreadPoolExecutor(max_workers=num_simultaneous_trains) as executor:
        futures = [
            executor.submit(simulate_train_route, train, TRAIN_SPEED_KMPH, start_time)
            for train in routes['features']
        ]
        
        for future in as_completed(futures):
            result = future.result()
            if result:
                trains_data.append(result)
    
    if trains_data:
        with open(output_file, 'w', encoding='utf-8') as f:
            geojson.dump(geojson.FeatureCollection(trains_data), f)
        print(f"Data written to {output_file}")
    else:
        print("No data to write.")

# Function to insert to MongoDB
def insert_to_mongodb(file_path, db_name, collection_name):
    """Insert the GeoJSON data from a file into a MongoDB collection."""
    # Load the GeoJSON data from the file
    with open(file_path, 'r', encoding='utf-8') as f:
        data = geojson.load(f)
    
    # Connect to MongoDB
    client = MongoClient('mongodb+srv://your_connection_string_here')  # Adjust the connection string as needed
    db = client[db_name]
    collection = db[collection_name]
    
    # Insert the data into the collection
    result = collection.insert_many(data['features'])
    print(f"Inserted {len(result.inserted_ids)} documents into the collection '{collection_name}' in database '{db_name}'.")

# Configuration
TRAIN_SPEED_KMPH = 160  # Adjust speed as needed
OUTPUT_FILE = 'train_tracking_data.geojson'

# MongoDB Configuration
FILE_PATH = 'train_tracking_data.geojson'
DB_NAME = 'train_database'
COLLECTION_NAME = 'train_tracking_data'

# Generate the train data with up to 5 trains running simultaneously
generate_train_data(OUTPUT_FILE, num_simultaneous_trains=10)
# Insert the GeoJSON data into MongoDB
insert_to_mongodb(FILE_PATH, DB_NAME, COLLECTION_NAME)