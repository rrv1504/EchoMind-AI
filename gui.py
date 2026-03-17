# gui.py

import tkinter as tk
from tkinter import scrolledtext
from audio_input import record_audio
from speech_to_text import speech_to_text
from sentiment_analysis import analyze_sentiment
from emotion_detection import predict_emotion
from response_generator import generate_response
from text_to_speech import speak
from emotion_smoother import EmotionSmoother

smoother = EmotionSmoother()

def start_listening():
    status_label.config(text="Listening...")

    audio, audio_file = record_audio()

    text = speech_to_text(audio)
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, text)

    sentiment = analyze_sentiment(text)
    emotion = predict_emotion(audio_file)

    smooth_emotion = smoother.add_emotion(emotion)

    emotion_label.config(text=f"Emotion: {smooth_emotion}")

    response = generate_response(smooth_emotion, sentiment)

    response_box.delete(1.0, tk.END)
    response_box.insert(tk.END, response)

    speak(response)

    status_label.config(text="Ready")

# GUI setup
root = tk.Tk()
root.title("EchoMind AI")
root.geometry("600x500")
root.configure(bg="black")

title = tk.Label(root, text="EchoMind", fg="white", bg="black", font=("Arial", 20))
title.pack(pady=10)

status_label = tk.Label(root, text="Ready", fg="green", bg="black")
status_label.pack()

btn = tk.Button(root, text="Start Listening", command=start_listening)
btn.pack(pady=10)

text_box = scrolledtext.ScrolledText(root, height=5)
text_box.pack(pady=10)

emotion_label = tk.Label(root, text="Emotion: -", fg="yellow", bg="black")
emotion_label.pack()

response_box = scrolledtext.ScrolledText(root, height=5)
response_box.pack(pady=10)

root.mainloop()