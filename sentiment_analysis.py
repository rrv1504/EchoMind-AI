# sentiment_analysis.py

from textblob import TextBlob

def analyze_sentiment(text):
    if text == "":
        return "neutral"

    polarity = TextBlob(text).sentiment.polarity

    if polarity > 0.2:
        return "positive"
    elif polarity < -0.2:
        return "negative"
    else:
        return "neutral"