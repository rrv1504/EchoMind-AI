import os
from collections import deque

from flask import Flask, jsonify, render_template, request
from pydub import AudioSegment

from emotion_detection import predict_emotion_details
from emotion_engine import EmotionTracker
from emotion_smoother import EmotionSmoother
from interview_analyzer import analyze_interview_tone
from language_utils import detect_language, from_english, normalize_language, to_english
from response_generator import generate_response
from sentiment_analysis import analyze_sentiment


app = Flask(__name__)
smoother = EmotionSmoother()
tracker = EmotionTracker(maxlen=20)
conversation_memory = deque(maxlen=5)
recent_responses = deque(maxlen=6)

UPLOAD_FOLDER = "temp_audio"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def _memory_snapshot():
    return list(conversation_memory)


def _remember_turn(user_text, emotion, sentiment, response):
    conversation_memory.append({
        "user": user_text,
        "bot": response["message"],
        "state": response["state"],
        "intent": response["intent"],
        "emotion": emotion,
        "sentiment": sentiment,
        "opener_index": response["opener_index"],
        "guidance_index": response["guidance_index"],
        "follow_up_index": response["follow_up_index"],
    })
    recent_responses.append(response["message"])


def _dedupe_response(response, language="en"):
    if response["message"] not in recent_responses:
        return response

    emotion = response.get("tone_emotion") or response.get("emotion", "neutral")
    variants = {
        "enthusiastic": "That energy sounds really good.\nUse it well: finish one small task while your momentum is high.",
        "happy": "That sounds genuinely nice.\nSave the good moment with a quick note, song, or small celebration.",
        "calm": "You sound pretty steady right now.\nDo one useful thing and protect that calm pace.",
        "neutral": "I am with you.\nTry writing one clear next action and start with that.",
        "sad": "That sounds heavy.\nTry a warm drink, soft music, and a few quiet minutes.",
        "tired": "That sounds draining.\nTry water, a short rest, and one low-effort task only if needed.",
        "stress": "That sounds like a lot to carry.\nTry a 10-minute timer, then handle just the smallest next step.",
        "frustrated": "Ugh, that sounds really frustrating.\nStep away for two minutes, breathe slowly, then choose one practical next move.",
        "angry": "Yeah, that sounds intense.\nCool down with a short walk or slow breathing before replying.",
        "sarcastic": "That sounds like the kind of fine that is not fully fine.\nTake a reset break, then do one small thing that gives you control back.",
    }
    message = variants.get(emotion, variants["neutral"])
    response["message"] = from_english(message, language) if language != "en" else message
    return response


@app.route("/reset_memory", methods=["POST"])
def reset_memory():
    conversation_memory.clear()
    recent_responses.clear()
    smoother.emotions.clear()
    tracker.clear()
    return jsonify({"ok": True})


def _response_payload(response, raw_emotion, sentiment, language, trend, extra=None):
    payload = {
        "emotion": response.get("emotion", raw_emotion),
        "raw_emotion": raw_emotion,
        "sentiment": sentiment,
        "response": response["message"],
        "suggestions": response["suggestions"],
        "state": response["state"],
        "intent": response["intent"],
        "confidence": response["confidence"],
        "note": response["note"],
        "language": language,
        "voice_emotion": response.get("voice_emotion"),
        "emotion_history": trend["history"],
        "spike": trend["spike"],
        "spike_message": trend["spike_message"],
        "memory_count": len(conversation_memory),
    }
    if extra:
        payload.update(extra)
    return payload


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/process", methods=["POST"])
def process():
    audio_file = request.files.get("audio")
    transcript = request.form.get("text", "").strip()
    interview_mode = request.form.get("interview_mode", "false").lower() == "true"
    language_hint = normalize_language(request.form.get("language"))

    if not audio_file:
        return jsonify({"error": "No audio file received."}), 400

    webm_path = os.path.join(UPLOAD_FOLDER, "input.webm")
    wav_path = os.path.join(UPLOAD_FOLDER, "input.wav")
    audio_file.save(webm_path)

    try:
        audio = AudioSegment.from_file(webm_path, format="webm")
        audio.export(wav_path, format="wav")
        raw_emotion, model_confidence, model_scores = predict_emotion_details(wav_path)
    except Exception as exc:
        return jsonify({"error": f"Could not process audio: {exc}"}), 422

    smooth_emotion = smoother.add_emotion(raw_emotion)
    original_text = transcript or "User spoke without transcript"
    language = language_hint or (detect_language(transcript) if transcript else "en")
    english_text = to_english(original_text, language)
    sentiment = analyze_sentiment(english_text)

    response = generate_response(
        smooth_emotion,
        sentiment,
        english_text,
        memory=_memory_snapshot(),
        return_details=True,
        voice_confidence=model_confidence,
        language=language,
    )
    response = _dedupe_response(response, language)
    trend = tracker.add(response["emotion"])
    _remember_turn(english_text, response["emotion"], sentiment, response)

    interview_feedback = None
    if interview_mode:
        interview_feedback = analyze_interview_tone(
            wav_path,
            emotion=response["emotion"],
            confidence=model_confidence,
        )

    return jsonify(_response_payload(response, smooth_emotion, sentiment, language, trend, {
        "model_confidence": model_confidence,
        "model_scores": model_scores,
        "interview_feedback": interview_feedback,
    }))


@app.route("/process_text", methods=["POST"])
def process_text():
    data = request.get_json(silent=True) or {}
    original_text = data.get("text", "").strip()

    if not original_text:
        return jsonify({"error": "Please enter or say something first."}), 400

    language = detect_language(original_text)
    english_text = to_english(original_text, language)
    sentiment = analyze_sentiment(english_text)

    response = generate_response(
        None,
        sentiment,
        english_text,
        memory=_memory_snapshot(),
        return_details=True,
        language=language,
    )
    response = _dedupe_response(response, language)
    trend = tracker.add(response["emotion"])
    _remember_turn(english_text, response["emotion"], sentiment, response)

    return jsonify(_response_payload(response, response["emotion"], sentiment, language, trend))


if __name__ == "__main__":
    app.run(debug=True)
