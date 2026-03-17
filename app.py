from flask import Flask, render_template, request, jsonify
import os
from emotion_detection import predict_emotion
from sentiment_analysis import analyze_sentiment
from response_generator import generate_response
from emotion_smoother import EmotionSmoother

app = Flask(__name__)
smoother = EmotionSmoother()

UPLOAD_FOLDER = "temp_audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

@app.route("/")
def index():
    return render_template("index.html")

from pydub import AudioSegment

@app.route("/process", methods=["POST"])
def process():
    audio_file = request.files["audio"]

    webm_path = os.path.join(UPLOAD_FOLDER, "input.webm")
    wav_path = os.path.join(UPLOAD_FOLDER, "input.wav")

    # Save original
    audio_file.save(webm_path)

    # Convert to WAV
    audio = AudioSegment.from_file(webm_path, format="webm")
    audio.export(wav_path, format="wav")

    # Now use WAV
    emotion = predict_emotion(wav_path)
    smooth_emotion = smoother.add_emotion(emotion)
    text = "User spoke"
    sentiment = analyze_sentiment(text)
    response = generate_response(smooth_emotion, sentiment, text)


    return jsonify({
        "emotion": smooth_emotion,
        "response": response
    })

@app.route("/process_text", methods=["POST"])
def process_text():
    data = request.get_json()
    text = data["text"]

    sentiment = analyze_sentiment(text)

    if sentiment == "positive":
        emotion = "happy"
    elif sentiment == "negative":
        emotion = "sad"
    else:
        emotion = "neutral"

    smooth_emotion = smoother.add_emotion(emotion)

    # ✅ FIXED LINE
    response = generate_response(smooth_emotion, sentiment, text)

    return jsonify({
        "emotion": smooth_emotion,
        "response": response
    })

if __name__ == "__main__":
    app.run(debug=True)