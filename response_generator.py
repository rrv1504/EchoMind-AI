import json
import os
import re
import urllib.error
import urllib.request

from emotion_engine import (
    VALID_EMOTIONS,
    detect_text_emotion,
    emotion_state,
    emotion_value,
    infer_local_semantic_emotion,
    normalize_voice_emotion,
)
from language_utils import from_english


CONTEXT_KEYWORDS = {
    "studies": {"exam", "exams", "assignment", "submission", "study", "college", "project"},
    "work": {"job", "office", "work", "boss", "manager", "client", "meeting"},
    "health": {"sick", "tired", "exhausted", "fever", "headache", "pain", "doctor", "sleep"},
    "interview": {"interview", "resume", "hr", "technical", "answer", "candidate"},
}

FALLBACKS = {
    "enthusiastic": (
        "That energy sounds really good.",
        "Use it well: finish one small task while your momentum is high.",
    ),
    "happy": (
        "That sounds genuinely nice.",
        "Save the good moment with a quick note, song, or small celebration.",
    ),
    "calm": (
        "You sound pretty steady right now.",
        "Keep it simple: do one useful thing and protect that calm pace.",
    ),
    "neutral": (
        "I am with you.",
        "Try writing one clear next action and start with that.",
    ),
    "sad": (
        "That sounds heavy.",
        "Try a warm drink, soft music, and a few quiet minutes away from your phone.",
    ),
    "tired": (
        "That sounds draining.",
        "Try water, a short rest, and one low-effort task only if needed.",
    ),
    "stress": (
        "That sounds like a lot to carry.",
        "Try a 10-minute timer, then handle just the smallest next step.",
    ),
    "frustrated": (
        "Ugh, that sounds really frustrating.",
        "Step away for two minutes, breathe slowly, then choose one practical next move.",
    ),
    "angry": (
        "Yeah, that sounds intense.",
        "Do not reply immediately; cool down with a short walk or slow breathing first.",
    ),
    "sarcastic": (
        "That sounds like the kind of fine that is not fully fine.",
        "Take a reset break, then do one small thing that gives you control back.",
    ),
}


def _get_env(name, default=None):
    value = os.getenv(name)
    if value:
        return value

    env_path = os.path.join(os.getcwd(), ".env")
    if not os.path.exists(env_path):
        return default

    try:
        with open(env_path, "r", encoding="utf-8") as env_file:
            for line in env_file:
                line = line.strip()
                if not line or line.startswith("#") or "=" not in line:
                    continue
                key, raw_value = line.split("=", 1)
                if key.strip() == name:
                    return raw_value.strip().strip("\"'")
    except OSError:
        return default

    return default


def _tokenize(text):
    return set(re.findall(r"[a-z']+", (text or "").lower()))


def detect_intent(text, memory=None):
    tokens = _tokenize(text)
    scores = {
        context: len(tokens.intersection(words))
        for context, words in CONTEXT_KEYWORDS.items()
    }
    context = max(scores, key=scores.get)
    return (context if scores[context] else "general"), scores


def _build_prompt(text, emotion, memory=None):
    return f"""
User is feeling {emotion}.
User said: '{text}'.
Recent chat history:
{json.dumps(_recent_memory_for_emotion(memory), ensure_ascii=False)}

Give:
1. Emotional reaction
2. One helpful activity

Rules:
- DO NOT ask questions
- Keep response in 2 lines
- Match emotion correctly
- Do NOT repeat generic phrases
- Use chat history only when it helps the current response
""".strip()


def _call_gemini(text, emotion, memory=None):
    api_key = _get_env("GEMINI_API_KEY") or _get_env("GOOGLE_API_KEY")
    if not api_key:
        print("No API key found for Gemini. Set GEMINI_API_KEY or GOOGLE_API_KEY in environment or .env file.")
        return None

    model = _get_env("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": _build_prompt(text, emotion, memory)}],
            }
        ],
        "generationConfig": {
            "temperature": 0.75,
            "maxOutputTokens": 90,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=14) as response:
            data = json.loads(response.read().decode("utf-8"))
            print(f"Raw Gemini API response: {data}")
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Gemini error: {exc}")
        return None

    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "\n".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError, TypeError) as exc:
        print(f"Gemini parse error: {exc}; raw={data}")
        return None


def _call_gemini_prompt(prompt, max_tokens=80, temperature=0.1):
    api_key = _get_env("GEMINI_API_KEY") or _get_env("GOOGLE_API_KEY")
    if not api_key:
        return None

    model = _get_env("GEMINI_MODEL", "gemini-2.5-flash")
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    payload = {
        "contents": [{"role": "user", "parts": [{"text": prompt}]}],
        "generationConfig": {
            "temperature": temperature,
            "maxOutputTokens": max_tokens,
        },
    }
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            data = json.loads(response.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        print(f"Gemini semantic emotion error: {exc}")
        return None

    try:
        parts = data["candidates"][0]["content"]["parts"]
        return "\n".join(part.get("text", "") for part in parts).strip()
    except (KeyError, IndexError, TypeError) as exc:
        print(f"Gemini semantic emotion parse error: {exc}; raw={data}")
        return None


def _recent_memory_for_emotion(memory):
    recent = []
    for item in (memory or [])[-4:]:
        recent.append({
            "user": item.get("user", ""),
            "bot": item.get("bot", ""),
            "emotion": item.get("emotion", ""),
            "sentiment": item.get("sentiment", ""),
        })
    return recent


def _last_memory_emotion(memory):
    for item in reversed(memory or []):
        emotion = item.get("emotion")
        if emotion in VALID_EMOTIONS and emotion != "neutral":
            return emotion
    return None


def _continuity_emotion(text, memory):
    lowered = (text or "").lower().strip()
    if not lowered:
        return None, 0.0

    last_emotion = _last_memory_emotion(memory)
    if not last_emotion:
        return None, 0.0

    continuity_patterns = (
        r"\b(same|same thing|again|still|it happened again|that again|this again)\b",
        r"\b(not better|still not okay|still bad|same as before)\b",
        r"\b(yes|yeah|yep|true|exactly|same here)\b",
    )
    short_reply = len(re.findall(r"[a-z']+", lowered)) <= 4
    if short_reply and any(re.search(pattern, lowered) for pattern in continuity_patterns):
        return last_emotion, 0.72
    if any(re.search(pattern, lowered) for pattern in continuity_patterns):
        return last_emotion, 0.68

    return None, 0.0


def _parse_semantic_emotion(raw):
    if not raw:
        return None, 0.0

    cleaned = raw.strip()
    match = re.search(r"\{.*\}", cleaned, flags=re.S)
    if match:
        cleaned = match.group(0)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        emotion_match = re.search(
            r"\b(happy|calm|neutral|sad|tired|stress|frustrated|angry|enthusiastic|sarcastic)\b",
            cleaned.lower(),
        )
        if not emotion_match:
            return None, 0.0
        return emotion_match.group(1), 0.66

    emotion = str(data.get("emotion", "")).lower().strip()
    try:
        confidence = float(data.get("confidence", 0.0))
    except (TypeError, ValueError):
        confidence = 0.0

    if emotion not in VALID_EMOTIONS:
        return None, 0.0
    return emotion, max(0.0, min(confidence, 1.0))


def _semantic_emotion_with_gemini(text, memory, voice_emotion):
    prompt = f"""
Classify the user's emotional state from meaning and recent chat continuity.

Allowed emotions:
happy, calm, neutral, sad, tired, stress, frustrated, angry, enthusiastic, sarcastic

Recent chat history:
{json.dumps(_recent_memory_for_emotion(memory), ensure_ascii=False)}

Current user message:
{text}

Voice emotion hint:
{voice_emotion or "none"}

Return ONLY valid JSON:
{{"emotion":"one_allowed_emotion","confidence":0.0}}

Rules:
- Use meaning, not only keywords.
- Use recent chat history when the user says things like "same", "again", "still", or "that happened".
- If the text clearly implies an emotion, prefer text meaning over voice.
- If the message is truly unclear, use the voice hint if available.
""".strip()
    raw = _call_gemini_prompt(prompt, max_tokens=60, temperature=0.05)
    emotion, confidence = _parse_semantic_emotion(raw)
    print(f"semantic Gemini emotion response: {raw}")
    return emotion, confidence


def _resolve_emotion_with_context(text, sentiment, voice_emotion, voice_confidence, memory):
    text_emotion, text_confidence = detect_text_emotion(text, sentiment)
    voice_normalized = normalize_voice_emotion(voice_emotion)

    if text_emotion:
        return text_emotion, text_confidence, "text_override", voice_normalized, text_emotion, None

    semantic_emotion, semantic_confidence = _semantic_emotion_with_gemini(text, memory, voice_normalized)
    if semantic_emotion and semantic_emotion != "neutral" and semantic_confidence >= 0.55:
        return semantic_emotion, semantic_confidence, "semantic_gemini", voice_normalized, text_emotion, semantic_emotion

    local_emotion, local_confidence = infer_local_semantic_emotion(text)
    if local_emotion:
        return local_emotion, local_confidence, "local_semantic", voice_normalized, text_emotion, semantic_emotion

    continuity_emotion, continuity_confidence = _continuity_emotion(text, memory)
    if continuity_emotion:
        return continuity_emotion, continuity_confidence, "chat_continuity", voice_normalized, text_emotion, semantic_emotion

    if voice_emotion:
        confidence = voice_confidence if voice_confidence is not None else 0.65
        return voice_normalized, confidence, "voice", voice_normalized, text_emotion, semantic_emotion

    if semantic_emotion:
        return semantic_emotion, max(semantic_confidence, 0.55), "semantic_gemini", voice_normalized, text_emotion, semantic_emotion

    return "neutral", 0.55, "text", voice_normalized, text_emotion, semantic_emotion


def _clean_response(text):
    raw = text or ""
    raw = re.sub(r"(?i)^(assistant|bot|reply)\s*:\s*", "", raw.strip())
    lines = []
    seen = set()

    for line in raw.replace("\r", "\n").split("\n"):
        line = re.sub(r"^[-*\d.]+\s*", "", line).strip().strip('"')
        line = re.sub(r"\s+", " ", line)
        if not line:
            continue
        lowered = line.lower()
        if lowered in seen:
            continue
        seen.add(lowered)
        lines.append(line[:170])
        if len(lines) == 2:
            break

    if not lines:
        return ""
    return "\n".join(lines[:2])


def _fallback_response(emotion):
    first, second = FALLBACKS.get(emotion, FALLBACKS["neutral"])
    return f"{first}\n{second}"


def _activity_line(emotion):
    return FALLBACKS.get(emotion, FALLBACKS["neutral"])[1]


def generate_dynamic_response(text, emotion, context=None, language="en", memory=None):
    api_response = _call_gemini(text, emotion, memory)
    print(f"Gemini response: {api_response}")
    cleaned = _clean_response(api_response)

    if cleaned and len(cleaned.strip()) >= 10:
        lines = [line for line in cleaned.splitlines() if line.strip()]
        if len(lines) == 1:
            message = f"{lines[0]}\n{_activity_line(emotion)}"
        else:
            message = cleaned
    else:
        message = _fallback_response(emotion)

    if language != "en":
        message = from_english(message, language)

    return message


def generate_response(
    emotion,
    sentiment,
    text,
    memory=None,
    return_details=False,
    voice_confidence=None,
    language="en",
):
    memory = memory or []
    (
        final_emotion,
        confidence,
        source,
        normalized_voice,
        text_emotion,
        semantic_emotion,
    ) = _resolve_emotion_with_context(
        text,
        sentiment,
        emotion,
        voice_confidence,
        memory,
    )
    print(f"user_text: {text}")
    print(f"detected text emotion: {text_emotion}")
    print(f"semantic emotion: {semantic_emotion}")
    print(f"voice emotion: {normalized_voice}")
    print(f"final emotion: {final_emotion}")

    context, context_scores = detect_intent(text, memory)
    message = generate_dynamic_response(
        text,
        final_emotion,
        context=context,
        language=language,
        memory=memory,
    )

    result = {
        "state": emotion_state(final_emotion),
        "intent": context,
        "tone": final_emotion,
        "tone_emotion": final_emotion,
        "emotion": final_emotion,
        "emotion_source": source,
        "voice_emotion": normalized_voice,
        "confidence": round(float(confidence), 2),
        "message": message,
        "suggestions": [],
        "note": "",
        "scores": {
            "value": emotion_value(final_emotion),
            "state": emotion_state(final_emotion),
        },
        "intent_scores": context_scores,
        "opener_index": 0,
        "guidance_index": 0,
        "follow_up_index": 0,
    }

    if return_details:
        return result
    return result["message"]
