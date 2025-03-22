# api.py

from fastapi import FastAPI
import decision_tree_predict
import uvicorn
import sys

app = FastAPI(
    title="Bus Prediction API",
    description="API to fetch bus predictions using a Decision Tree model",
    version="1.0.0",
)

@app.get("/get_predictions")
async def get_predictions():
    """API endpoint that returns the bus predictions."""
    df = decision_tree_predict.get_real_time_data()  # Get real-time data
    if df is not None:
        bus_predictions = decision_tree_predict.make_predictions(df)  # Make predictions based on the data
        return {"bus_predictions": bus_predictions}
    return {"error": "Failed to fetch or process real-time data."}

if __name__ == "__main__":
    # Check if the user has provided a port argument
    port = 8000  # Default port
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])  # Port passed as the first argument
        except ValueError:
            print("Invalid port. Using default port 8000.")
    
    # Run the app with uvicorn, specifying host as 0.0.0.0 and dynamic port
    uvicorn.run(app, host="0.0.0.0", port=port)
