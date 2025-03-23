# api.py 
from fastapi import FastAPI
from fastapi.responses import HTMLResponse
import decision_tree_predict
import uvicorn
import sys
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app with default /docs and /redoc
app = FastAPI(
    title="Bus Prediction API",
    description="API to fetch bus predictions and raw GTFS data using a Decision Tree model",
    version="1.0.0",
    docs_url="/docs",    # Swagger UI at /docs
    redoc_url="/redoc",  # ReDoc at /redoc
)

# Load the HTML file
with open("index.html", "r") as f:
    ROOT_HTML = f.read()

@app.get("/", response_class=HTMLResponse)
async def root():
    logger.info("Root endpoint accessed")
    return HTMLResponse(content=ROOT_HTML)

@app.get("/test")
async def test():
    logger.info("Test endpoint accessed")
    return {"message": "Server is running"}

@app.get("/get_predictions")
async def get_predictions():
    logger.info("Fetching predictions")
    df = await decision_tree_predict.get_real_time_data()
    if df is not None:
        map_data = decision_tree_predict.make_predictions(df)
        if map_data is not None:
            logger.info("Predictions made")
            return {"bus_predictions": map_data}
    logger.error("Failed to fetch real-time data")
    return {"error": "Failed to fetch or process real-time data."}

@app.get("/fetch_vehicle_positions")
async def fetch_vehicle_positions():
    logger.info("Fetching vehicle positions")
    vehicle_positions_url = "https://drtonline.durhamregiontransit.com/gtfsrealtime/VehiclePositions"
    vehicle_positions = await decision_tree_predict.fetch_and_convert(vehicle_positions_url)
    if vehicle_positions is not None:
        logger.info("Vehicle positions fetched")
        return vehicle_positions
    logger.error("Failed to fetch vehicle positions")
    return {"error": "Failed to fetch vehicle positions data."}

@app.get("/fetch_trip_updates")
async def fetch_trip_updates():
    logger.info("Fetching trip updates")
    trip_updates_url = "https://drtonline.durhamregiontransit.com/gtfsrealtime/TripUpdates"
    trip_updates = await decision_tree_predict.fetch_and_convert(trip_updates_url)
    if trip_updates is not None:
        logger.info("Trip updates fetched")
        return trip_updates
    logger.error("Failed to fetch trip updates")
    return {"error": "Failed to fetch trip updates data."}

if __name__ == "__main__":
    port = 8000
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            print("Invalid port. Using default port 8000.")
    uvicorn.run(app, host="0.0.0.0", port=port)
