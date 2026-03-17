# speech_to_text.py

import speech_recognition as sr

def speech_to_text(audio):
    recognizer = sr.Recognizer()

    try:
        text = recognizer.recognize_google(audio)
        print("You said:", text)
        return text.lower()

    except sr.UnknownValueError:
        print("Could not understand audio")
        return ""

    except sr.RequestError:
        print("API error")
        return ""