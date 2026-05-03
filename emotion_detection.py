import librosa
import numpy as np
import joblib

MODEL_PATH = "models/emotion_model.pkl"

model = joblib.load(MODEL_PATH)

def extract_features(audio_file):
    y, sr = librosa.load(audio_file, duration=3, offset=0.5)
    mfcc = np.mean(librosa.feature.mfcc(y=y, sr=sr, n_mfcc=40).T, axis=0)
    return mfcc

def predict_emotion(audio_file):
    features = extract_features(audio_file)
    features = features.reshape(1, -1)
    return model.predict(features)[0]


def predict_emotion_details(audio_file):
    features = extract_features(audio_file).reshape(1, -1)
    emotion = model.predict(features)[0]

    if not hasattr(model, "predict_proba"):
        return emotion, None, {}

    probabilities = model.predict_proba(features)[0]
    scores = {
        label: round(float(score), 3)
        for label, score in zip(model.classes_, probabilities)
    }
    confidence = scores.get(emotion)
    return emotion, confidence, scores
