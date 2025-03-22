# Description: This script fetches GTFS-Realtime data from Durham Region Transit's API and creates a dataset of bus status information.
import requests
import time
import pandas as pd
import json
from google.transit import gtfs_realtime_pb2
from datetime import datetime
import math
import pytz
from protobuf_to_json import protobuf_to_json

# Define Eastern Time Zone
eastern = pytz.timezone('US/Eastern')

# Function to fetch GTFS-Realtime data from a URL
def fetch_gtfs_data(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        feed = gtfs_realtime_pb2.FeedMessage()
        feed.ParseFromString(response.content)
        return feed
    except requests.RequestException as e:
        print(f"Error fetching data from {url}: {e}")
        return None

# Function to parse protobuf feed into JSON format
def protobuf_to_json(feed):
    feed_dict = {
        "header": {
            "gtfs_realtime_version": feed.header.gtfs_realtime_version,
            "incrementality": str(feed.header.incrementality),
            "timestamp": feed.header.timestamp
        },
        "entity": []
    }
    for entity in feed.entity:
        entity_dict = {"id": entity.id}
        if entity.HasField('trip_update'):
            trip_update = entity.trip_update
            entity_dict["trip_update"] = {
                "trip": {
                    "trip_id": trip_update.trip.trip_id,
                    "route_id": trip_update.trip.route_id,
                    "start_time": trip_update.trip.start_time,
                    "start_date": trip_update.trip.start_date
                },
                "stop_time_update": [
                    {
                        "stop_sequence": stu.stop_sequence,
                        "stop_id": stu.stop_id,
                        "arrival": {"time": stu.arrival.time if stu.HasField('arrival') else None},
                        "departure": {"time": stu.departure.time if stu.HasField('departure') else None}
                    } for stu in trip_update.stop_time_update
                ]
            }
        elif entity.HasField('vehicle'):
            vehicle = entity.vehicle
            entity_dict["vehicle"] = {
                "trip": {
                    "trip_id": vehicle.trip.trip_id,
                    "route_id": vehicle.trip.route_id
                },
                "position": {
                    "latitude": vehicle.position.latitude,
                    "longitude": vehicle.position.longitude
                },
                "timestamp": vehicle.timestamp
            }
        feed_dict["entity"].append(entity_dict)
    return feed_dict

# Function to calculate distance between two coordinates (Haversine formula)
def calculate_distance(lat1, lon1, lat2, lon2):
    R = 6371e3
    φ1, φ2 = map(math.radians, [lat1, lat2])
    Δφ, Δλ = map(math.radians, [lat2 - lat1, lon2 - lon1])
    a = math.sin(Δφ/2)**2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c

# Function to calculate speed
def calculate_speed(distance, time_diff):
    return 0 if time_diff == 0 else distance / time_diff

# Load stops data
stops_df = pd.read_csv('stops.txt')

# Initialize CSV file
csv_filename = 'bus_status_dataset.csv'
if not pd.io.common.file_exists(csv_filename):
    pd.DataFrame(columns=[
        'bus_id', 'trip_id', 'route_id', 'current_lat', 'current_lon', 'next_stop_id', 'next_stop_lat', 'next_stop_lon',
        'next_stop_name', 'current_time', 'position_timestamp', 'expected_arrival_time', 'time_to_arrival_seconds',
        'distance_to_stop_meters', 'speed_m_s', 'status', 'stop_sequence', 'wheelchair_boarding'
    ]).to_csv(csv_filename, index=False)

# Main loop to fetch data every minute
while True:
    vehicle_positions_feed = fetch_gtfs_data("https://drtonline.durhamregiontransit.com/gtfsrealtime/VehiclePositions")
    trip_updates_feed = fetch_gtfs_data("https://drtonline.durhamregiontransit.com/gtfsrealtime/TripUpdates")
    
    if not vehicle_positions_feed or not trip_updates_feed:
        time.sleep(60)
        continue
    
    vehicle_positions = protobuf_to_json(vehicle_positions_feed)
    trip_updates = protobuf_to_json(trip_updates_feed)
    
    processed_data = []
    current_time = datetime.fromtimestamp(vehicle_positions['header']['timestamp'], tz=pytz.utc).astimezone(eastern)
    
    for vehicle_entity in vehicle_positions['entity']:
        vehicle = vehicle_entity['vehicle']
        bus_id = vehicle_entity['id']
        trip_id = vehicle['trip']['trip_id']
        route_id = vehicle['trip']['route_id']
        current_lat = vehicle['position']['latitude']
        current_lon = vehicle['position']['longitude']
        position_timestamp = datetime.fromtimestamp(vehicle['timestamp'], tz=pytz.utc).astimezone(eastern)
        
        trip_update = next((tu['trip_update'] for tu in trip_updates['entity'] if tu['trip_update']['trip']['trip_id'] == trip_id), None)
        if trip_update and 'stop_time_update' in trip_update:
            next_stop_update = trip_update['stop_time_update'][0]
            next_stop_id = next_stop_update['stop_id']
            stop_match = stops_df[stops_df['stop_id'] == next_stop_id]
            if stop_match.empty:
                continue
            next_stop = stop_match.iloc[0]
            next_stop_lat, next_stop_lon, next_stop_name = next_stop['stop_lat'], next_stop['stop_lon'], next_stop['stop_name']
            expected_arrival = datetime.fromtimestamp(next_stop_update['arrival']['time'], tz=pytz.utc).astimezone(eastern)
            time_to_arrival = (expected_arrival - current_time).total_seconds()
            distance_to_stop = calculate_distance(current_lat, current_lon, next_stop_lat, next_stop_lon)
            speed = calculate_speed(distance_to_stop, max(1, time_to_arrival))
            time_diff = time_to_arrival
            status = 'early' if time_diff < -60 else 'late' if time_diff > 60 else 'on-time'
            
            record = {
                'bus_id': bus_id, 'trip_id': trip_id, 'route_id': route_id, 'current_lat': current_lat,
                'current_lon': current_lon, 'next_stop_id': next_stop_id, 'next_stop_lat': next_stop_lat,
                'next_stop_lon': next_stop_lon, 'next_stop_name': next_stop_name, 
                'current_time': int(current_time.timestamp()),  # Converted to Unix time
                'position_timestamp': int(position_timestamp.timestamp()),  # Converted to Unix time
                'expected_arrival_time': int(expected_arrival.timestamp()),  # Converted to Unix time
                'time_to_arrival_seconds': time_to_arrival, 'distance_to_stop_meters': distance_to_stop,
                'speed_m_s': speed, 'status': status, 'stop_sequence': next_stop_update['stop_sequence'],
                'wheelchair_boarding': next_stop['wheelchair_boarding']
            }
            processed_data.append(record)
    
    if processed_data:
        pd.DataFrame(processed_data).to_csv(csv_filename, mode='a', header=False, index=False)
    
    print(f"Updated dataset with {len(processed_data)} new records.")
    time.sleep(60)
