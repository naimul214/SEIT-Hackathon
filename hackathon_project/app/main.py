# api.py (with logging and custom HTML frontend)
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
    docs_url="/docs",    # Enable default Swagger UI at /docs
    redoc_url="/redoc",  # Enable default ReDoc at /redoc
)

# Custom HTML for the root page with tabs
ROOT_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bus Prediction API</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .tab-container {
            overflow: hidden;
            border-bottom: 1px solid #ccc;
        }
        .tab-button {
            background-color: #ddd;
            float: left;
            border: none;
            outline: none;
            cursor: pointer;
            padding: 14px 16px;
            transition: 0.3s;
            font-size: 16px;
        }
        .tab-button:hover {
            background-color: #bbb;
        }
        .tab-button.active {
            background-color: #ccc;
        }
        .tab-content {
            display: none;
            padding: 20px;
            border: 1px solid #ccc;
            border-top: none;
            background-color: white;
        }
        .tab-content.active {
            display: block;
        }
    </style>
</head>
<body>
    <h1>Bus Prediction API</h1>
    <div class="tab-container">
        <button class="tab-button active" onclick="openTab(event, 'home')">Home</button>
        <button class="tab-button" onclick="openTab(event, 'docs')">Docs</button>
        <button class="tab-button" onclick="openTab(event, 'map')">Map</button>
        <button class="tab-button" onclick="openTab(event, 'dashboard')">Data Dashboard</button>
    </div>

    <div id="home" class="tab-content active">
        <h2>Home</h2>
        <p>Welcome to the Bus Prediction API. Use the tabs above to explore documentation, view a real-time map, or check the data dashboard.</p>
        <p>Try fetching predictions at <a href="/get_predictions">/get_predictions</a> or vehicle positions at <a href="/fetch_vehicle_positions">/fetch_vehicle_positions</a>.</p>
    </div>

    <div id="docs" class="tab-content">
        <h2>API Documentation</h2>
        <p>Explore the API documentation using the following tools:</p>
        <ul>
            <li><a href="/docs" target="_blank">Swagger UI</a> - Interactive API testing and documentation</li>
            <li><a href="/redoc" target="_blank">ReDoc</a> - Clean, readable API documentation</li>
        </ul>
    </div>

    <div id="map" class="tab-content">
        <h2>Real-Time Map</h2>
        <p>Placeholder for a real-time map displaying bus locations and predictions.</p>
        <p>Coming soon! Fetch data from <a href="/get_predictions">/get_predictions</a> to populate this.</p>
    </div>

    <div id="dashboard" class="tab-content">
        <h2>Data Dashboard</h2>
        <p>Placeholder for a dashboard showing bus prediction statistics and trends.</p>
        <p>Coming soon! Use <a href="/fetch_vehicle_positions">vehicle positions</a> and <a href="/fetch_trip_updates">trip updates</a> for analytics.</p>
    </div>

    <script>
        function openTab(evt, tabName) {
            var i, tabcontent, tabbuttons;
            tabcontent = document.getElementsByClassName("tab-content");
            for (i = 0; i < tabcontent.length; i++) {
                tabcontent[i].classList.remove("active");
            }
            tabbuttons = document.getElementsByClassName("tab-button");
            for (i = 0; i < tabbuttons.length; i++) {
                tabbuttons[i].classList.remove("active");
            }
            document.getElementById(tabName).classList.add("active");
            evt.currentTarget.classList.add("active");
        }
    </script>
</body>
</html>
"""

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
        bus_predictions = decision_tree_predict.make_predictions(df)
        logger.info("Predictions made")
        return {"bus_predictions": bus_predictions}
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
