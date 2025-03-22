# Description: Converts a GTFS-Realtime protobuf file to JSON, preserving Unix timestamps.
# Install required packages: pip install gtfs-realtime-bindings
# Import the bindings and JSON module
from google.transit import gtfs_realtime_pb2
import json

def protobuf_to_json(filename="alerts.pb", save_filename='TripUpdates.json', save=True,verbose=False):
    """
    Converts a GTFS-Realtime protobuf file to JSON, preserving Unix timestamps.
    
    Parameters:
    - filename (str): Path to the input .pb file (default: 'alerts.pb')
    - save_filename (str): Path to save the output JSON file (default: 'TripUpdates.json')
    - save (bool): Whether to save the output to a file (default: True)
    
    Returns:
    - dict: The converted feed data as a Python dictionary
    
    Raises:
    - FileNotFoundError: If the input file doesn't exist
    - Exception: For other parsing or writing errors
    """
    try:
        # Read the GTFS-Realtime data from the file
        with open(filename, 'rb') as f:
            feed = gtfs_realtime_pb2.FeedMessage()
            feed.ParseFromString(f.read())

        # Convert the feed to a dictionary
        feed_dict = {
            "header": {
                "gtfs_realtime_version": feed.header.gtfs_realtime_version,
                "incrementality": str(feed.header.incrementality),  # Enum to string
                "timestamp": feed.header.timestamp  # Unix timestamp (seconds since epoch)
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
                        "start_time": trip_update.trip.start_time,  # Kept as original string (e.g., "HH:MM:SS")
                        "start_date": trip_update.trip.start_date   # Kept as original string (e.g., "YYYYMMDD")
                    },
                    "stop_time_update": [
                        {
                            "stop_sequence": stu.stop_sequence,
                            "stop_id": stu.stop_id,
                            "arrival": {
                                "time": stu.arrival.time if stu.HasField('arrival') else None  # Unix timestamp
                            },
                            "departure": {
                                "time": stu.departure.time if stu.HasField('departure') else None  # Unix timestamp
                            }
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
                    "timestamp": vehicle.timestamp  # Unix timestamp
                }
            elif entity.HasField('alert'):
                alert = entity.alert
                entity_dict["alert"] = {
                    "active_period": [
                        {"start": ap.start, "end": ap.end} for ap in alert.active_period  # Unix timestamps
                    ],
                    "informed_entity": [
                        {"route_id": ie.route_id, "stop_id": ie.stop_id} for ie in alert.informed_entity
                    ],
                    "description_text": [
                        {"text": tt.text, "language": tt.language} for tt in alert.description_text.translation
                    ]
                }

            feed_dict["entity"].append(entity_dict)

        if verbose:
            # Print for verification (optional)
            print("Header:", feed.header)
            for entity in feed.entity:
                if entity.HasField('trip_update'):
                    print("Trip Update:", entity.trip_update)
                elif entity.HasField('vehicle'):
                    print("Vehicle Position:", entity.vehicle)
                elif entity.HasField('alert'):
                    print("Alert:", entity.alert)

        if save:
            # Save to JSON file
            with open(save_filename, 'w') as json_file:
                json.dump(feed_dict, json_file, indent=4)
            print(f"Data saved to '{save_filename}'")

        # Return the dictionary (fixed from original, which tried to return json.dump a second time)
        return feed_dict

    except FileNotFoundError as e:
        print(f"Error: Input file '{filename}' not found - {e}")
        raise
    except Exception as e:
        print(f"An error occurred: {e}")
        raise

# Example usage
if __name__ == "__main__":
    # Convert the file and get the dictionary
    result = protobuf_to_json("alerts.pb", "TripUpdates.json", save=True)
    # Optionally print the result
    print("\nConverted data (first entity):")
    print(json.dumps(result["entity"][0], indent=4) if result["entity"] else "No entities found")