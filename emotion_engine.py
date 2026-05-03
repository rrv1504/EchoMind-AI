import re
from collections import deque
from datetime import datetime, timezone

from textblob import TextBlob


VALID_EMOTIONS = {
    "happy",
    "calm",
    "neutral",
    "sad",
    "tired",
    "stress",
    "frustrated",
    "angry",
    "enthusiastic",
    "sarcastic",
}

EMOTION_VALUES = {
    "enthusiastic": 3,
    "happy": 2,
    "calm": 1,
    "neutral": 0,
    "tired": -1,
    "sad": -2,
    "stress": -2,
    "frustrated": -3,
    "angry": -3,
    "sarcastic": -1,
}

STATE_BY_EMOTION = {
    "enthusiastic": "calm",
    "happy": "calm",
    "calm": "calm",
    "neutral": "neutral",
    "sarcastic": "neutral",
    "tired": "low mood",
    "sad": "low mood",
    "stress": "stress",
    "frustrated": "stress",
    "angry": "stress",
}

TEXT_PATTERNS = (
    ("happy", re.compile(r"(\u0905\u091a\u094d\u091b\u093e|\u092e\u091c\u093e|\u0a96\u0ac1\u0ab6|\u0aae\u0a9c\u0abe)|\b(happy|great)\b", re.I)),
    ("sad", re.compile(r"(\u0928\u0939\u0940\u0902|\u0916\u0930\u093e\u092c|\u0a96\u0ab0\u0abe\u0aac|\u0aa6\u0ac1\u0a96)|\b(sad|bad)\b", re.I)),
    ("stress", re.compile(r"(\u0924\u0928\u093e\u0935|\u0a97\u0ac1\u0ab8\u0acd\u0ab8\u0acb|\u0ab8\u0acd\u0a9f\u0acd\u0ab0\u0ac7\u0ab8)|\b(stress|frustrated)\b", re.I)),
    ("sarcastic", re.compile(r"\b(fine\.\.\.|great\.\.\.|wow\.\.\.|sure\.\.\.|nice\.\.\.)", re.I)),
    ("enthusiastic", re.compile(r"\b(wow|excited|amazing|awesome|fantastic|yay|super|thrilled)\b|!{2,}", re.I)),
    ("frustrated", re.compile(r"\b(ugh|done|frustrating|annoyed|irritated|fed up|sick of)\b", re.I)),
    ("angry", re.compile(r"\b(angry|mad|furious|rage|hate)\b", re.I)),
    ("stress", re.compile(r"\b(stressed|stressful|overwhelmed|pressure|panic|anxious|worried|deadline|too much|a lot)\b", re.I)),
    ("tired", re.compile(r"\b(tired|exhausted|drained|sleepy|burnt out|burned out|low energy)\b", re.I)),
    ("sad", re.compile(r"\b(low|upset|hurt|lonely|crying|depressed|empty|heavy)\b", re.I)),
    ("happy", re.compile(r"\b(good|nice|proud|relieved|better|love|glad)\b", re.I)),
    ("calm", re.compile(r"\b(calm|okay|ok|peaceful|relaxed|fine)\b", re.I)),
)

VOICE_MAP = {
    "angry": "frustrated",
    "frustrated": "frustrated",
    "disgust": "frustrated",
    "fearful": "stress",
    "fear": "stress",
    "sad": "sad",
    "tired": "tired",
    "calm": "calm",
    "neutral": "calm",
    "happy": "happy",
    "surprised": "enthusiastic",
}


def normalize_voice_emotion(emotion):
    return VOICE_MAP.get((emotion or "neutral").lower(), "neutral")


def detect_text_emotion(text, sentiment="neutral"):
    text = text or ""
    for emotion, pattern in TEXT_PATTERNS:
        if pattern.search(text):
            return emotion, 0.94

    polarity = TextBlob(text).sentiment.polarity if text.strip() else 0
    if sentiment == "negative" or polarity < -0.3:
        return "sad", 0.7
    if sentiment == "positive" or polarity > 0.3:
        return "happy", 0.7
    return None, 0.0


def infer_local_semantic_emotion(text):
    lowered = (text or "").lower().strip()
    if not lowered:
        return None, 0.0

    semantic_patterns = (
        ("frustrated", (
            r"\b(can't deal|cannot deal|can't handle|cannot handle|done with this|fed up|keeps happening)\b",
            r"\b(nothing is working|this is not working|same problem again)\b",
        )),
        ("stress", (
            r"\b(too much to do|so much to do|no time|running out of time|deadline is close)\b",
            r"\b(i have to manage|everything is piling up|can't keep up)\b",
        )),
        ("sad", (
            r"\b(i don't feel like|nothing feels good|lost interest|feel empty|feel alone)\b",
            r"\b(not okay|not fine|not feeling myself|feel like crying)\b",
        )),
        ("tired", (
            r"\b(no energy|need rest|can't stay awake|barely slept|long day)\b",
        )),
        ("happy", (
            r"\b(went well|worked out|better than expected|made my day|felt good)\b",
        )),
        ("enthusiastic", (
            r"\b(can't wait|looking forward|really excited|finally did it|nailed it)\b",
        )),
        ("calm", (
            r"\b(feel settled|under control|peaceful now|handled it)\b",
        )),
    )

    for emotion, patterns in semantic_patterns:
        if any(re.search(pattern, lowered) for pattern in patterns):
            return emotion, 0.78

    return None, 0.0


def resolve_emotion(text, sentiment="neutral", voice_emotion=None, voice_confidence=None):
    text_emotion, text_confidence = detect_text_emotion(text, sentiment)
    voice_normalized = normalize_voice_emotion(voice_emotion)

    if text_emotion:
        return text_emotion, text_confidence, "text_override", voice_normalized

    local_emotion, local_confidence = infer_local_semantic_emotion(text)
    if local_emotion:
        return local_emotion, local_confidence, "local_semantic", voice_normalized

    if voice_emotion:
        confidence = voice_confidence if voice_confidence is not None else 0.65
        return voice_normalized, confidence, "voice", voice_normalized

    return "neutral", 0.55, "text", voice_normalized


def emotion_state(emotion):
    return STATE_BY_EMOTION.get(emotion, "neutral")


def emotion_value(emotion):
    return EMOTION_VALUES.get(emotion, 0)


class EmotionTracker:
    def __init__(self, maxlen=20):
        self.history = deque(maxlen=maxlen)

    def clear(self):
        self.history.clear()

    def add(self, emotion):
        value = emotion_value(emotion)
        entry = {
            "emotion": emotion,
            "value": value,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        previous = self.history[-1] if self.history else None
        self.history.append(entry)

        spike = False
        spike_message = ""
        if previous and abs(value - previous.get("value", 0)) >= 2:
            spike = True
            spike_message = "Your mood changed quickly just now"

        return {
            "history": list(self.history),
            "spike": spike,
            "spike_message": spike_message,
        }
