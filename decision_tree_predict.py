import time
import pickle
import requests
import pandas as pd
import math
import pytz
import tempfile
import os
import json
from datetime import datetime
from protobuf_to_json import protobuf_to_json  # Import the provided function

bus_predictions = {}

# Load the saved scaler and decision tree model
with open("scaler.pkl", "rb") as file:
    scaler = pickle.load(file)

with open("decision_tree_model.pkl", "rb") as file:
    dt_model = pickle.load(file)

# Define Eastern Time Zone
eastern = pytz.timezone('US/Eastern')

# Load stops data
stops_df = pd.read_csv('data/stops.txt')

# --- Utility Functions ---
def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate the Haversine distance between two latitude/longitude points."""
    R = 6371e3  # Earth's radius in meters
    φ1, φ2 = map(math.radians, [lat1, lat2])
    Δφ, Δλ = map(math.radians, [lat2 - lat1, lon2 - lon1])
    a = math.sin(Δφ / 2) ** 2 + math.cos(φ1) * math.cos(φ2) * math.sin(Δλ / 2) ** 2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return R * c  # Distance in meters

def calculate_speed(distance, time_diff):
    """Calculate speed in meters per second."""
    return 0 if time_diff == 0 else distance / time_diff

def fetch_and_convert(url):
    """Fetch GTFS-Realtime data and convert to JSON."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            tmp_file.write(response.content)
            tmp_file.flush()
            tmp_filename = tmp_file.name
        data_json = protobuf_to_json(tmp_filename, save=False)
        os.remove(tmp_filename)
        return data_json
    except Exception as e:
        print(f"Error fetching or converting data from {url}: {e}")
        return None

def get_real_time_data(save=False):
    """Fetch, process, and convert GTFS data to a structured dataset."""
    vehicle_positions_url = "https://drtonline.durhamregiontransit.com/gtfsrealtime/VehiclePositions"
    trip_updates_url = "https://drtonline.durhamregiontransit.com/gtfsrealtime/TripUpdates"
    
    vehicle_positions = fetch_and_convert(vehicle_positions_url)
    trip_updates = fetch_and_convert(trip_updates_url)
    
    if not vehicle_positions or not trip_updates:
        print("Failed to fetch GTFS data.")
        return None
    
    processed_data = []
    
    # Get current time (as Unix timestamp)
    current_time = datetime.fromtimestamp(vehicle_positions['header']['timestamp'], tz=eastern).timestamp()
    
    for vehicle_entity in vehicle_positions.get('entity', []):
        if 'vehicle' not in vehicle_entity:
            continue
        
        vehicle = vehicle_entity['vehicle']
        bus_id = vehicle_entity.get('id')
        trip_id = vehicle['trip'].get('trip_id')
        route_id = vehicle['trip'].get('route_id')
        current_lat = vehicle['position'].get('latitude')
        current_lon = vehicle['position'].get('longitude')
        position_timestamp = datetime.fromtimestamp(vehicle['timestamp'], tz=eastern).timestamp()

        # Find trip update for this vehicle
        trip_update = next((tu['trip_update'] for tu in trip_updates.get('entity', []) 
                            if tu['trip_update']['trip'].get('trip_id') == trip_id), None)
        
        if trip_update and 'stop_time_update' in trip_update:
            next_stop_update = trip_update['stop_time_update'][0]  # Assume first stop is next
            next_stop_id = next_stop_update.get('stop_id')
            
            stop_match = stops_df[stops_df['stop_id'] == next_stop_id]
            if stop_match.empty:
                continue  # Skip if stop not found
            
            next_stop = stop_match.iloc[0]
            next_stop_lat = next_stop['stop_lat']
            next_stop_lon = next_stop['stop_lon']
            next_stop_name = next_stop['stop_name']
            
            # Convert expected arrival to Unix timestamp
            if next_stop_update.get('arrival') and next_stop_update['arrival'].get('time'):
                expected_arrival = datetime.fromtimestamp(next_stop_update['arrival']['time'], tz=eastern).timestamp()
            else:
                continue
            
            time_to_arrival = expected_arrival - current_time
            distance_to_stop = calculate_distance(current_lat, current_lon, next_stop_lat, next_stop_lon)
            speed = calculate_speed(distance_to_stop, max(1, time_to_arrival))
            
            # Determine status (label for training)
            if time_to_arrival < -60:
                status = 'early'
            elif time_to_arrival > 60:
                status = 'late'
            else:
                status = 'on-time'
            
            record = {
                'bus_id': bus_id,
                'trip_id': trip_id,
                'route_id': route_id,
                'current_lat': current_lat,
                'current_lon': current_lon,
                'next_stop_id': next_stop_id,
                'next_stop_lat': next_stop_lat,
                'next_stop_lon': next_stop_lon,
                'next_stop_name': next_stop_name,
                'current_time': current_time,
                'position_timestamp': position_timestamp,
                'expected_arrival_time': expected_arrival,
                'time_to_arrival_seconds': time_to_arrival,
                'distance_to_stop_meters': distance_to_stop,
                'speed_m_s': speed,
                'status': status,
                'stop_sequence': next_stop_update.get('stop_sequence'),
                'wheelchair_boarding': next_stop.get('wheelchair_boarding')
            }
            processed_data.append(record)
    
    df = pd.DataFrame(processed_data)
    if save:
        csv_filename = 'bus_status_dataset.csv'
        df.to_csv(csv_filename, index=False)
        
        print(f"Dataset saved as '{csv_filename}' with {len(df)} records.")
    
    return df

def make_predictions(df):
    """Make predictions using the decision tree model."""
    if df is None or df.empty:
        print("No data available for predictions.")
        return
    
    df_pred = df.copy()

    # Drop non-feature columns
    blacklist = ['bus_id', 'trip_id', 'route_id', 'next_stop_name', 'stop_sequence', 'wheelchair_boarding', 'status']
    X = df_pred.drop(columns=blacklist, errors='ignore')

    # Convert timestamps to Unix timestamps (redundant but ensures correctness)
    time_columns = ['current_time', 'position_timestamp', 'expected_arrival_time']
    for col in time_columns:
        if col in X.columns:
            X[col] = pd.to_numeric(X[col], errors='coerce')

    # Scale features
    X_scaled = scaler.transform(X)

    # Predict
    predictions = dt_model.predict(X_scaled)
    bus_predictions = {}


    for idx, row in df_pred.iterrows():
        bus_predictions[row['bus_id']] = predictions[idx]
        print(f"Bus ID: {row['bus_id']}, Trip ID: {row['trip_id']}, Predicted Status: {predictions[idx]}")
    return bus_predictions

def decision_tree_scan(time_in_seconds=0):
    """
    Fetches real-time data, processes it, and makes predictions.
    If `time_in_seconds` > 0, runs in a loop every `time_in_seconds` seconds.
    """
    if time_in_seconds <= 0:
        df = get_real_time_data()
        if df is not None:
            make_predictions(df)
    else:
        while True:
            df = get_real_time_data()
            if df is not None:
                make_predictions(df)
            time.sleep(time_in_seconds)

if __name__ == "__main__":
    # Set time interval (in seconds) between data pulls. 0 = run once.
    time_in_seconds = 5
    try:
        decision_tree_scan(time_in_seconds)
    except Exception as e:
        print(f"An error occurred: {e}")
