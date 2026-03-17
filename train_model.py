# train_model.py

import os
import librosa
import numpy as np
import joblib
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score

DATA_PATH = "data/ravdess/"
MODEL_PATH = "models/emotion_model.pkl"

# Emotion mapping
emotion_dict = {
    "01": "neutral",
    "02": "calm",
    "03": "happy",
    "04": "sad",
    "05": "angry"
}

# 🎧 Extract MFCC features
def extract_features(file_path):
    try:
        y, sr = librosa.load(file_path, duration=3, offset=0.5)
        mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
        return mfcc
    except:
        return None

# 📂 Load dataset
def load_data():
    X = []
    y = []

    for root, dirs, files in os.walk(DATA_PATH):
        for file in files:
            if file.endswith(".wav"):
                file_path = os.path.join(root, file)

                # Extract emotion from filename
                emotion_code = file.split("-")[2]

                if emotion_code in emotion_dict:
                    emotion = emotion_dict[emotion_code]

                    features = extract_features(file_path)

                    if features is not None:
                        X.append(features)
                        y.append(emotion)

    return np.array(X), np.array(y)

# 🚀 Train Model
def train():
    print("Loading dataset...")
    X, y = load_data()

    print("Total samples:", len(X))

    # Split data
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Model
    model = RandomForestClassifier(n_estimators=100)

    print("Training model...")
    model.fit(X_train, y_train)

    # Evaluation
    y_pred = model.predict(X_test)
    accuracy = accuracy_score(y_test, y_pred)

    print("Model Accuracy:", accuracy)

    # Save model
    joblib.dump(model, MODEL_PATH)
    print("Model saved at:", MODEL_PATH)

# ▶️ Run training
if __name__ == "__main__":
    train()