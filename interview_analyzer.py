import math

import librosa
import numpy as np


def _safe_float(value, default=0.0):
    try:
        if math.isnan(value) or math.isinf(value):
            return default
        return float(value)
    except Exception:
        return default


def analyze_interview_tone(audio_file, emotion="neutral", confidence=None):
    try:
        y, sr = librosa.load(audio_file, duration=8, offset=0)
    except Exception:
        return None

    if y.size == 0:
        return None

    rms = librosa.feature.rms(y=y)[0]
    zcr = librosa.feature.zero_crossing_rate(y)[0]
    intervals = librosa.effects.split(y, top_db=30)
    voiced_duration = sum((end - start) / sr for start, end in intervals)
    total_duration = len(y) / sr if sr else 0
    speech_ratio = voiced_duration / total_duration if total_duration else 0

    pitches = librosa.yin(y, fmin=70, fmax=350, sr=sr)
    pitches = pitches[np.isfinite(pitches)]
    pitch_std = _safe_float(np.std(pitches), 0)
    energy_mean = _safe_float(np.mean(rms), 0)
    energy_std = _safe_float(np.std(rms), 0)
    zcr_mean = _safe_float(np.mean(zcr), 0)

    stress_level = min(1.0, (pitch_std / 90) + (zcr_mean * 2.2))
    clarity = max(0.0, min(1.0, speech_ratio - (energy_std * 5)))
    confidence_level = max(0.0, min(1.0, (energy_mean * 18) + (clarity * 0.55) - (stress_level * 0.25)))

    if emotion in {"stress", "frustrated", "angry"} or stress_level > 0.62:
        tone = "nervous"
        feedback = "You sounded slightly nervous"
        suggestion = "Try slowing down, pausing between points, and speaking clearly"
    elif confidence_level > 0.58 and clarity > 0.45:
        tone = "confident"
        feedback = "You sounded reasonably confident"
        suggestion = "Keep that steady pace and finish answers with a clear final line"
    elif clarity < 0.28:
        tone = "unsure"
        feedback = "Your answer sounded a bit unclear"
        suggestion = "Try shorter sentences and emphasize the main point first"
    else:
        tone = "monotone"
        feedback = "Your tone sounded a little flat"
        suggestion = "Add small pitch changes and stress key words naturally"

    return {
        "tone": tone,
        "confidence_level": round(confidence_level, 2),
        "stress_level": round(stress_level, 2),
        "clarity": round(clarity, 2),
        "feedback": feedback,
        "suggestion": suggestion,
        "model_emotion_confidence": confidence,
    }
