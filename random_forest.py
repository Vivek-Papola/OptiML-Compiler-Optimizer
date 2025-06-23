import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score, classification_report
import joblib # For saving and loading the model

def train_and_save_random_forest_model(csv_file_path, model_save_path='random_forest_optimization_model.joblib'):
    """
    Trains a Random Forest Classifier model using data from a CSV file
    and saves the trained model to a .joblib file.

    Args:
        csv_file_path (str): The path to the CSV file containing features and labels.
        model_save_path (str): The file path where the trained model will be saved.
    """
    try:
        # Load the dataset
        df = pd.read_csv(csv_file_path)

        # Separate features (X) and labels (y)
        # Assuming the last column is 'label' and the rest are features
        X = df.drop('label', axis=1)
        y = df['label']

        # Split data into training and testing sets
        # Using a fixed random_state for reproducibility
        X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

        # Initialize and train the Random Forest Classifier
        # You can tune n_estimators, max_depth, etc., for better performance
        model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
        model.fit(X_train, y_train)

        # Make predictions on the test set
        y_pred = model.predict(X_test)

        # Evaluate the model
        accuracy = accuracy_score(y_test, y_pred)
        report = classification_report(y_test, y_pred)

        print(f"Model Training Complete!")
        print(f"Accuracy: {accuracy:.4f}")
        print("Classification Report:")
        print(report)

        # Save the trained model using joblib
        joblib.dump(model, model_save_path)
        print(f"--- Model Saved Successfully: {model_save_path} ---")

    except FileNotFoundError:
        print(f"Error: CSV file not found at {csv_file_path}")
    except Exception as e:
        print(f"An error occurred during model training: {e}")

if __name__ == "__main__":
    # --- Example Usage ---
    # Make sure you have your dataset ready, e.g., 'code_dataset_combinationflag.csv'
    # This example assumes the file is in the same directory as this script.
    # Replace 'path/to/your/code_dataset_combinationflag.csv' with the actual path if different.
    
    # You mentioned 'code_dataset_combinationflag.csv.xlsx - code_dataset_combinationflag.csv'
    # If your file is a CSV and named 'code_dataset_combinationflag.csv', use that name.
    # If it's an Excel file you've converted, ensure it's saved as .csv
    
    csv_dataset_path = 'code_dataset_combinationflag.csv' # Adjust if your CSV file has a different name

    # Train and save the model
    train_and_save_random_forest_model(csv_dataset_path)

    # You can then load and use this 'random_forest_optimization_model.joblib' in your prediction script.
    # Example of loading the model (for testing purposes, not part of this script's primary function)
    # try:
    #     loaded_model = joblib.load('random_forest_optimization_model.joblib')
    #     print(f"\nModel loaded successfully for verification: {loaded_model}")
    # except FileNotFoundError:
    #     print("Saved model not found after training, check path.")
