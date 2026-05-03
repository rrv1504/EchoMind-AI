from textblob import TextBlob


POSITIVE_KEYWORDS = {
    "happy", "great", "good", "nice", "awesome", "amazing", "excited",
    "proud", "relieved", "better", "love", "glad", "yay", "wow", "mza",
    "maja",
    "\u0905\u091a\u094d\u091b\u093e",  # अच्छा
    "\u092e\u091c\u093e",              # मजा
    "\u0916\u0941\u0936",              # खुश
    "\u0a96\u0ac1\u0ab6",              # ખુશ
    "\u0aae\u0a9c\u0abe",              # મજા
}

NEGATIVE_KEYWORDS = {
    "sad", "bad", "upset", "hurt", "lonely", "crying", "depressed",
    "empty", "heavy", "tired", "exhausted", "drained", "stress",
    "stressed", "frustrated", "frustrating", "angry", "mad", "ugh",
    "done", "hate", "worried", "anxious", "overwhelmed", "low",
    "\u0928\u0939\u0940\u0902",        # नहीं
    "\u0916\u0930\u093e\u092c",        # खराब
    "\u0924\u0928\u093e\u0935",        # तनाव
    "\u0a96\u0ab0\u0abe\u0aac",        # ખરાબ
    "\u0aa6\u0ac1\u0a96",              # દુખ
    "\u0a97\u0ac1\u0ab8\u0acd\u0ab8\u0acb",  # ગુસ્સો
    "\u0ab8\u0acd\u0a9f\u0acd\u0ab0\u0ac7\u0ab8",  # સ્ટ્રેસ
}


def _tokenize(text):
    return set((text or "").lower().replace("...", " ").split())


def analyze_sentiment(text):
    text = (text or "").strip()
    if not text:
        return "neutral"

    lowered = text.lower()
    tokens = _tokenize(text)

    positive_hits = sum(1 for word in POSITIVE_KEYWORDS if word in tokens or word in lowered)
    negative_hits = sum(1 for word in NEGATIVE_KEYWORDS if word in tokens or word in lowered)

    if negative_hits > positive_hits:
        return "negative"
    if positive_hits > negative_hits:
        return "positive"

    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0.08:
        return "positive"
    elif polarity < -0.08:
        return "negative"
    else:
        return "neutral"
