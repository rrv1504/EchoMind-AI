from emotion_detection import predict_emotion
# main.py

from gui import *
# main.py

from audio_input import record_audio
from speech_to_text import speech_to_text
from sentiment_analysis import analyze_sentiment
from response_generator import generate_response
from text_to_speech import speak

def main():

    print("=== EchoMind AI Started ===")

    while True:
        audio = record_audio()
        text = speech_to_text(audio)

        if text == "":
            continue

        if "exit" in text:
            print("Exiting...")
            break

        sentiment = analyze_sentiment(text)

        # For demo: using text-based emotion fallback
        emotion = "neutral"

        response = generate_response(emotion, sentiment)
        speak(response)

if __name__ == "__main__":
    main()