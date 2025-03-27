# SEIT-Hackathon
# Live Bus Arrival Time Prediction with Decision Tree ML Model

This project provides a real-time visualization of Durham Regional Transit buses and predicts whether each bus will arrive at its next stop **Late**, **Early**, or **On-Time** using a Decision Tree Machine Learning model. It was developed during a hackathon and submitted to [Devpost](https://devpost.com/software/live-bus-arrival-time-prediction-with-decision-tree-ml-model). A live demo is available at [https://nallace.tech/](https://nallace.tech/).

---

## Features

- **Real-Time Bus Tracking**: Displays all Durham Regional Transit buses on a visual live map.
- **Arrival Time Prediction**: Uses a Decision Tree model to predict bus arrival status (Late, Early, On-Time).
- **Simple Frontend**: Built with HTML, CSS, and JavaScript, featuring tabs for Home, Docs, Map, and Data Dashboard.
- **API Access**: Provides endpoints to fetch predictions and raw GTFS data via FastAPI.

---

## How It Works

1. **Data Fetching**: Real-time GTFS data (vehicle positions and trip updates) is fetched from the Durham Regional Transit API.
2. **Data Processing**: Features like distance to the next stop, time to arrival, and speed are calculated.
3. **Prediction**: A pre-trained Decision Tree model predicts the bus arrival status.
4. **Visualization**: The frontend shows bus locations and their predicted statuses on a map.

---

## Technologies Used

- **Backend**: Python, FastAPI
- **Frontend**: HTML, CSS, JavaScript
- **Machine Learning**: scikit-learn (Decision Tree Classifier)
- **Deployment**: Docker, Google Cloud Run
- **Data Format**: GTFS Realtime (Protocol Buffers)

---

## Setup and Installation

To run this project locally, follow these steps:

1. pip install -r requirements.txt
2. uvicorn main:app --reload --port=
