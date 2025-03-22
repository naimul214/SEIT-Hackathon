import pandas as pd
import pickle
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.tree import DecisionTreeClassifier
from sklearn.metrics import confusion_matrix, accuracy_score, ConfusionMatrixDisplay
from sklearn.preprocessing import StandardScaler

# Load dataset
df = pd.read_csv('bus_status_dataset_unix.csv')
# Remove unnecessary columns
columns_to_remove = ['bus_id', 'trip_id', 'route_id', 'next_stop_name', 'stop_sequence', 'wheelchair_boarding']
def train_decision_tree(df, columns_to_remove, target='status'):
    df = df.drop(columns=columns_to_remove)

    # Split features and target
    X_train, X_test, y_train, y_test = train_test_split(df.drop(target, axis=1), df[target], test_size=0.2, random_state=42)

    # Standardize features
    scaler = StandardScaler()
    X_train = scaler.fit_transform(X_train)
    X_test = scaler.transform(X_test)

    # Train Decision Tree model
    dt_model = DecisionTreeClassifier(random_state=42)
    dt_model.fit(X_train, y_train)

    # Save the model
    with open("decision_tree_model.pkl", "wb") as file:
        pickle.dump(dt_model, file)

    # Make predictions
    y_pred = dt_model.predict(X_test)

    # Evaluate model
    acc = accuracy_score(y_test, y_pred)
    cm = confusion_matrix(y_test, y_pred)

    print(f"Decision Tree Accuracy: {acc * 100:.2f}%")
    print("Confusion Matrix:")
    print(cm)

    # Display Confusion Matrix
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap=plt.cm.Blues)
    plt.title("Decision Tree Confusion Matrix")
    plt.show()

    # Save the scaler to use during inference
    with open("scaler.pkl", "wb") as file:
        pickle.dump(scaler, file)

train_decision_tree(df, columns_to_remove)