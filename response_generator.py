def generate_response(emotion, sentiment, text):

    text = text.lower()

    # 🔥 Strong keyword detection
    if any(word in text for word in ["good", "great", "happy", "nice", "awesome", "completed", "done"]):
        state = "calm"

    elif any(word in text for word in ["stress", "tired", "pressure", "busy", "overwhelmed"]):
        state = "stress"

    elif any(word in text for word in ["sad", "lonely", "upset", "bad", "depressed"]):
        state = "low mood"

    else:
        # fallback
        if sentiment == "positive":
            state = "calm"
        elif sentiment == "negative":
            state = "low mood"
        else:
            state = "neutral"

    responses = {
    "stress": "You sound a bit stressed. Try slow breathing or take a short break.",
    "calm": "That’s really nice to hear. You’re doing well, keep it up!",
    "low mood": "I’m here for you. Maybe talk to someone or take some rest.",
    "neutral": "Sounds like a normal day. Tell me more about it."
}

    return responses[state] + "\n(Note: Not medical advice)"