SUPPORTED_LANGUAGES = {"en", "hi", "gu"}


def normalize_language(language):
    if not language:
        return None

    language = str(language).strip().lower()
    if "-" in language:
        language = language.split("-", 1)[0]
    return language if language in SUPPORTED_LANGUAGES else None


def detect_language(text):
    if not text or not text.strip():
        return "en"

    if any("\u0a80" <= char <= "\u0aff" for char in text):
        return "gu"
    if any("\u0900" <= char <= "\u097f" for char in text):
        return "hi"

    try:
        from langdetect import detect

        detected = detect(text)
    except Exception:
        return "en"

    return normalize_language(detected) or "en"


def translate_text(text, source_language, target_language):
    if not text or source_language == target_language:
        return text

    try:
        from deep_translator import GoogleTranslator

        return GoogleTranslator(source=source_language, target=target_language).translate(text)
    except Exception:
        return text


def to_english(text, language):
    return translate_text(text, language, "en")


def from_english(text, language):
    return translate_text(text, "en", language)
