# emotion_smoother.py

from collections import Counter

class EmotionSmoother:
    def __init__(self, window_size=5):
        self.window_size = window_size
        self.emotions = []

    def add_emotion(self, emotion):
        self.emotions.append(emotion)

        if len(self.emotions) > self.window_size:
            self.emotions.pop(0)

        return self.get_smoothed_emotion()

    def get_smoothed_emotion(self):
        if not self.emotions:
            return "neutral"

        return Counter(self.emotions).most_common(1)[0][0]