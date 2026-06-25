import pandas as pd
import pickle
import matplotlib.pyplot as plt
import os
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, ConfusionMatrixDisplay
from sklearn.preprocessing import StandardScaler

# Define absolute directory of the script
BASE_DIR = Path(__file__).resolve().parent

# Ensure the model_weights directory exists
(BASE_DIR / "model_weights").mkdir(parents=True, exist_ok=True)

# Load dataset using absolute path
dataset_path = BASE_DIR / 'bus_status_dataset_unix.csv'
if not dataset_path.exists():
    # Fallback to non-unix dataset if it exists, or output instructions
    alt_dataset_path = BASE_DIR / 'bus_status_dataset.csv'
    if alt_dataset_path.exists():
        dataset_path = alt_dataset_path
    else:
        print(f"Error: Dataset not found at {dataset_path} or {alt_dataset_path}.")
        print("Please run data collection (e.g. data_creation/create_dataset_scan.py) first.")
        exit(1)

df = pd.read_csv(dataset_path)

# Remove unnecessary columns and features that cause Target Leakage
# time_to_arrival_seconds and expected_arrival_time must be removed to prevent leakage
columns_to_remove = [
    'bus_id', 'trip_id', 'route_id', 'next_stop_name', 
    'stop_sequence', 'wheelchair_boarding', 
    'time_to_arrival_seconds', 'expected_arrival_time'
]

def train_decision_tree(df, columns_to_remove, target='status'):
    df = df.drop(columns=columns_to_remove, errors='ignore')

    # Split features and target
    X_train, X_test, y_train, y_test = train_test_split(df.drop(target, axis=1), df[target], test_size=0.2, random_state=42)

    # Standardize features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Train Decision Tree model
    dt_model = DecisionTreeClassifier(random_state=42)
    dt_model.fit(X_train, y_train)

    # Save the model to model_weights/ directory
    model_path = BASE_DIR / "model_weights" / "decision_tree_model.pkl"
    with open(model_path, "wb") as file:
        pickle.dump(dt_model, file)

    # Make predictions
    y_pred = dt_model.predict(X_test)

    # Evaluate model
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    print(f"Decision Tree Accuracy: {acc * 100:.2f}%")
    print("Confusion Matrix:")
    print(cm)

    # Save Confusion Matrix plot instead of showing it (headless friendly)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Decision Tree Confusion Matrix")
    plt.savefig(BASE_DIR / "confusion_matrix.png")
    print(f"Confusion matrix plot saved to {BASE_DIR / 'confusion_matrix.png'}")
    plt.close()

    # Save the scaler to use during inference
    scaler_path = BASE_DIR / "model_weights" / "scaler.pkl"
    with open(scaler_path, "wb") as file:
        pickle.dump(scaler, file)
    print(f"Model and scaler successfully saved to {BASE_DIR / 'model_weights'}")

train_decision_tree(df, columns_to_remove)