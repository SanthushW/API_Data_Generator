import googlemaps
import geojson
import time
from datetime import datetime, timedelta
import json
import polyline
from concurrent.futures import ThreadPoolExecutor, as_completed
from shapely.geometry import Point

# Initialize Google Maps client
gmaps = googlemaps.Client(key='AIzaSyBYlmum_EIYi8B0nax7l-bJDLjJQjlhN-o')

# Load the GeoJSON file containing train routes
with open('SLRailwayRoutes.geojson', encoding='utf-8') as f:
    routes = geojson.load(f)

# Load the GeoJSON file containing railway stations
with open('hotosm_lka_railways_points_geojson.geojson', encoding='utf-8') as f:
    stations = geojson.load(f)

# Create a dictionary of station points for easy lookup
station_points = {feature['properties']['name']: feature['geometry']['coordinates'] for feature in stations['features']}

def get_nearest_station(coord):
    """Find the nearest railway station to a given coordinate."""
    min_distance = float('inf')
    nearest_station = None
    for station_name, station_coord in station_points.items():
        distance = Point(coord).distance(Point(station_coord))
        if distance < min_distance:
            min_distance = distance
            nearest_station = station_coord
    return nearest_station

def get_route(origin, destination):
    """Get the route between two points using Google Maps API."""
    # Snap the origin and destination to the nearest railway station
    origin_coord = [origin['longitude'], origin['latitude']]
    destination_coord = [destination['longitude'], destination['latitude']]
    
    snapped_origin = get_nearest_station(origin_coord)
    snapped_destination = get_nearest_station(destination_coord)
    
    if snapped_origin is None or snapped_destination is None:
        print(f"No nearby station found for origin: {origin_coord} or destination: {destination_coord}")
        return []

    # Use snapped stations as origin and destination
    origin = {'latitude': snapped_origin[1], 'longitude': snapped_origin[0]}
    destination = {'latitude': snapped_destination[1], 'longitude': snapped_destination[0]}
    
    print(f"Requesting route from snapped {origin} to snapped {destination}")
    
    try:
        directions_result = gmaps.directions(
            origin=f"{origin['latitude']},{origin['longitude']}",
            destination=f"{destination['latitude']},{destination['longitude']}",
            mode="transit",
            transit_mode="rail",
            units="metric"
        )
        if not directions_result:
            print("No directions found using rail. Trying without transit mode...")
            directions_result = gmaps.directions(
                origin=f"{origin['latitude']},{origin['longitude']}",
                destination=f"{destination['latitude']},{destination['longitude']}",
                mode="driving",
                units="metric"
            )
            if not directions_result:
                print("No directions found even with driving mode.")
                return []

        print(f"Directions found: {directions_result}")
        polyline_str = directions_result[0]['overview_polyline']['points']
        return polyline.decode(polyline_str)
    
    except googlemaps.exceptions.ApiError as e:
        print(f"Google Maps API error: {e}")
        return []

def simulate_train_route(train_data, speed_kmph, start_time):
    """Simulate the train moving along the route at a certain speed."""
    train_id = train_data['properties']['route']
    origin_coords = train_data['geometry']['coordinates'][0]
    destination_coords = train_data['geometry']['coordinates'][-1]

    origin = {'latitude': origin_coords[1], 'longitude': origin_coords[0]}
    destination = {'latitude': destination_coords[1], 'longitude': destination_coords[0]}
    
    print(f"Simulating route: {train_id}")
    
    route = get_route(origin, destination)

    if not route:
        return None

    # Snap route points to the nearest railway stations
    route = [get_nearest_station([coord[1], coord[0]]) for coord in route]

    geojson_route = {
        "type": "Feature",
        "properties": {
            "train_id": train_id,
            "timestamps": [],
            "start_time": start_time.isoformat()
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
        
        if not start_point or not end_point:
            continue
        
        # Calculate the distance between points
        distance = gmaps.distance_matrix(
            origins=[{'lat': start_point[1], 'lng': start_point[0]}],
            destinations=[{'lat': end_point[1], 'lng': end_point[0]}],
            mode="walking"
        )['rows'][0]['elements'][0]['distance']['value']
        
        travel_time = distance / speed_mpm
        geojson_route['geometry']['coordinates'].append([start_point[0], start_point[1]])
        geojson_route['properties']['timestamps'].append(current_time.isoformat())
        
        print(f"Train {train_id} moving from {start_point} to {end_point} at {current_time}.")
        
        time.sleep(1)  # Simulate the passage of one minute
        current_time += timedelta(minutes=1)
    
    # Add the final point and timestamp to the route
    geojson_route['geometry']['coordinates'].append([route[-1][0], route[-1][1]])
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

# Configuration
TRAIN_SPEED_KMPH = 960  # Adjust speed as needed
OUTPUT_FILE = 'train_tracking_data.geojson'

# Generate the train data with up to 5 trains running simultaneously
generate_train_data(OUTPUT_FILE, num_simultaneous_trains=10)
