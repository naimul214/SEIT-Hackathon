# Live Bus Arrival Time Prediction with Decision Tree ML Model

[![Python](https://img.shields.io/badge/Python-3.12-blue?style=flat-square&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-1.5-F7931E?style=flat-square&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat-square&logo=docker&logoColor=white)](https://www.docker.com/)
[![GTFS Realtime](https://img.shields.io/badge/GTFS--Realtime-Protobuf-000000?style=flat-square)](https://gtfs.org/realtime/)

A real-time service that fetches GTFS Realtime feeds for Durham Regional Transit, extracts spatial and temporal features, and predicts whether transit buses will arrive at their next stop Early, Late, or On-Time using a Decision Tree classifier.

---

## The "Why" (Real-World Value)

Public transit agencies publish real-time feeds to help passengers plan their journeys. However, raw transit schedule updates can be unpredictable due to traffic bottlenecks, rider density, and varying boarding times. 

This project demonstrates a production-ready edge/server API that:
- **Validates Agency Schedule Updates**: Automatically intercepts GTFS Realtime feed updates and computes granular metrics like Haversine distance, expected speed, and time-to-arrival.
- **Enables Proactive Passenger Insights**: Offers unified REST endpoints that frontend mapping dashboards or mobile apps can consume to show live, validated bus delay statuses (Early, Late, On-Time).
- **Supports Smart Transit Initiatives**: Provides a reusable pattern for processing streaming geospatial protobuf feeds and feeding them directly into machine learning inference engines.

---

## Tech Stack

- **Backend Framework**: FastAPI (Asynchronous Python)
- **Machine Learning**: scikit-learn (Decision Tree Classifier, StandardScaler preprocessing)
- **Data Engineering**: pandas, NumPy, Protocol Buffers (gtfs-realtime-bindings)
- **Networking & Async HTTP**: HTTPX
- **Environment & Build**: Docker, Astrals' `uv` package manager (supporting `pyproject.toml` and lockfile-defined dependencies)

---

## Architecture & Data Flow

```text
  ┌────────────────────────────────────────────────────────┐
  │         Durham Regional Transit (DRT) API              │
  │  (GTFS Realtime /VehiclePositions & /TripUpdates Feeds) │
  └───────────────────────────┬────────────────────────────┘
                              │ (HTTPS Get Protobuf Feeds)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                  FastAPI Backend                       │
  │      (Asynchronous HTTPX client fetching feeds)        │
  └───────────────────────────┬────────────────────────────┘
                              │ (Parse Protocol Buffers to Dict)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                 Feature Engineering                    │
  │  - Distance to stop (Haversine formula calculation)    │
  │  - Expected speed (Distance / Time-to-Arrival)         │
  │  - Join stops.txt metadata (coordinates & boarding)   │
  └───────────────────────────┬────────────────────────────┘
                              │ (Structured Pandas Dataframe)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │            Machine Learning Inference                  │
  │  - Preprocess features with fitted StandardScaler     │
  │  - Classify status using trained Decision Tree         │
  └───────────────────────────┬────────────────────────────┘
                              │ (Inference Output: Early, Late, On-Time)
                              ▼
  ┌────────────────────────────────────────────────────────┐
  │                 API Response & UI                      │
  │  - /get_predictions endpoint JSON output               │
  │  - Live HTML/JS Map interface showing transit status  │
  └────────────────────────────────────────────────────────┘
```

---

## Quickstart Guide

### Prerequisites
- Python 3.12 (or Docker installed)
- [uv](https://github.com/astral-sh/uv) (Recommended for lightning-fast setup and reproducible environment builds)

### Option 1: Local Setup with `uv` (Recommended)

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/naimul214/SEIT-Hackathon.git
   cd SEIT-Hackathon/hackathon_project
   ```

2. **Create Virtual Environment and Sync Dependencies**:
   ```bash
   # uv will automatically read pyproject.toml and install Python 3.12 + dependencies
   uv sync
   ```

3. **Activate Environment and Run the Application**:
   ```bash
   # Activate virtual env
   .venv\Scripts\activate  # On Windows
   # or: source .venv/bin/activate  # On Linux/macOS

   # Run FastAPI server
   cd app
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

### Option 2: Local Setup with Standard `pip`

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/naimul214/SEIT-Hackathon.git
   cd SEIT-Hackathon/hackathon_project
   ```

2. **Create Environment and Install Dependencies**:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Run the Application**:
   ```bash
   cd app
   uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

### Option 3: Docker Deployment

1. **Build the Docker Image**:
   ```bash
   docker build -t bus-prediction-app ./hackathon_project
   ```

2. **Run the Container**:
   ```bash
   docker run -p 8080:8080 bus-prediction-app
   ```
   *The API will be available at `http://localhost:8080` (Swagger UI at `/docs`).*

---

## Results & Evaluation

> [!NOTE]
> **Performance Metric & Visualization Placeholder**
> - *Model Performance*: The current Decision Tree model achieves **~99.8% validation accuracy** due to target leakage (see Limitations below). Upon addressing target leakage, realistic baseline metrics (e.g. F1-score, Confusion Matrix) will be documented here.
> - *Visualization*: [Insert screenshot or GIF here showing the live bus map or confusion matrix visualization]

---

## Limitations & Future Work

- **Target Leakage Remediation**: The model currently takes `time_to_arrival_seconds` (derived directly from the transit agency's own arrival time prediction) as an input feature to predict arrival status. The next iteration will drop this feature and instead predict arrival delays using raw speed, distance, route, and time-of-day features.
- **Categorical Feature Encoding**: The `next_stop_id` is a nominal categorical variable scaled as a continuous float. In future versions, this will be handled via target encoding or embedding layers.
- **Frontend Placeholders**: The `Map` and `Data Dashboard` tabs in the frontend `index.html` are currently static placeholders. Future iterations will integrate Leaflet.js to render live bus markers colored by their predicted status.
- **Data Persistence**: The application fetches in-memory GTFS feeds dynamically but does not store historical records. Storing data in a lightweight database (e.g., PostgreSQL or DuckDB) would enable training stronger models on historical delay patterns.

---

## Connect

- **LinkedIn**: [linkedin.com/in/naimul214](https://www.linkedin.com/in/naimul214)
- **GitHub**: [github.com/naimul214](https://github.com/naimul214)
- **Devpost Submission**: [Live Bus Arrival Time Prediction](https://devpost.com/software/live-bus-arrival-time-prediction-with-decision-tree-ml-model)
