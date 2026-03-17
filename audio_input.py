# audio_input.py

import speech_recognition as sr

def record_audio(save_path="temp.wav"):
    recognizer = sr.Recognizer()

    with sr.Microphone() as source:
        recognizer.adjust_for_ambient_noise(source)
        audio = recognizer.listen(source)

    with open(save_path, "wb") as f:
        f.write(audio.get_wav_data())

    return audio, save_path