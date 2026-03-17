# emotion_detection.py

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