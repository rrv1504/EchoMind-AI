# EchoMind - Emotion-Aware Conversational AI

EchoMind is a Flask-based emotional chatbot for daily conversation and supportive activity suggestions. It supports text chat, voice input, semantic emotion detection, multilingual interaction, emotion trend tracking, and an optional Mock Interview Mode for voice tone feedback.

## Features

- Text chat with emotion-aware responses
- Voice input using browser speech recognition and recorded audio
- Voice emotion detection using MFCC features and a trained Random Forest model
- Semantic text emotion detection using keywords, sentiment, Gemini meaning analysis, and chat continuity
- Gemini-powered dynamic responses with strict two-line output
- Local fallback responses when Gemini is unavailable
- Sentiment analysis with TextBlob plus English, Hindi, and Gujarati keyword cues
- Multilingual support for English, Hindi, and Gujarati
- Voice language selector for better speech recognition
- Emotion history tracking for the last 20 turns
- Chart.js emotion trend graph
- Spike/drop alert when mood changes quickly
- Optional Mock Interview Mode with confidence, stress, clarity, and tone feedback
- Chat history sidebar stored in browser localStorage
- Text-to-speech output
- Emotion-colored UI states

## Emotion Classes

EchoMind currently works with:

- enthusiastic
- happy
- calm
- neutral
- sad
- tired
- stress
- frustrated
- angry
- sarcastic

Voice model outputs are normalized before use. For example, angry/frustrated audio is treated as frustrated, fearful audio as stress, and calm/neutral audio as calm.

## How It Works

```text
User text or voice
  -> Speech recognition transcript and/or audio emotion model
  -> Language detection or selected voice language
  -> Translation to English for processing
  -> Sentiment + keyword + semantic emotion detection
  -> Chat-continuity emotion resolution
  -> Gemini response generation
  -> Translation back to original language when needed
  -> Emotion history + spike detection
  -> Chat UI, graph, and optional speech output
```

Final emotion priority:

1. Clear text emotion signal
2. Gemini semantic emotion from meaning and recent chat
3. Local semantic phrase fallback
4. Chat continuity from recent turns
5. Voice emotion
6. Neutral fallback

## Tech Stack

- Python
- Flask
- JavaScript, HTML, CSS
- Chart.js
- Web Speech API
- MediaRecorder API
- Gemini API
- TextBlob
- Langdetect
- Deep Translator
- Librosa
- Scikit-learn
- Pydub
- RAVDESS speech emotion dataset

## Project Structure

```text
EchoMind/
|-- app.py
|-- emotion_detection.py
|-- emotion_engine.py
|-- emotion_smoother.py
|-- interview_analyzer.py
|-- language_utils.py
|-- response_generator.py
|-- sentiment_analysis.py
|-- train_model.py
|-- requirements.txt
|-- models/
|   `-- emotion_model.pkl
|-- static/
|   |-- script.js
|   `-- style.css
|-- templates/
|   `-- index.html
|-- data/
`-- README.md
```

## Setup

Install dependencies:

```bash
pip install -r requirements.txt
```

Install TextBlob data:

```bash
python -m textblob.download_corpora
```

## Gemini API Setup

EchoMind uses Gemini for semantic emotion classification and dynamic replies. Create a `.env` file in the project root:

```env
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
```

`GEMINI_API_KEY` is also supported if you prefer that variable name.

If no Gemini key is available, EchoMind still runs with local emotion rules and fallback responses, but semantic understanding and response variety will be weaker.

Important: do not commit `.env` to GitHub.

## FFmpeg Setup

FFmpeg is required for converting browser voice recordings into WAV format.

Windows:

1. Download FFmpeg from https://www.gyan.dev/ffmpeg/builds/
2. Extract it to:

```text
C:\ffmpeg
```

3. Add this folder to PATH:

```text
C:\ffmpeg\bin
```

4. Verify:

```bash
ffmpeg -version
```

## Run

```bash
python app.py
```

Open:

```text
http://127.0.0.1:5000/
```

## Usage

You can interact with EchoMind in two ways:

- Type a message in the input box
- Select a voice language, click `Start voice`, and speak naturally

Supported voice language choices:

- English
- Hindi
- Gujarati

The chatbot responds with:

- one short emotional reaction
- one helpful activity suggestion
- tone matched to the detected emotion

New chats can be started from the sidebar. Chat history is saved locally in the browser.

## Emotion Trend Graph

EchoMind stores the last 20 emotion entries in memory and maps them to graph values:

- enthusiastic: +3
- happy: +2
- calm: +1
- neutral: 0
- tired: -1
- sad: -2
- stress: -2
- frustrated: -3
- angry: -3

If the value changes by 2 or more between two turns, EchoMind shows:

```text
Your mood changed quickly just now
```

## Mock Interview Mode

Mock Interview Mode is optional and does not replace the normal chatbot.

When enabled for voice input, EchoMind analyzes:

- confidence level
- stress level
- clarity
- tone label such as confident, nervous, unsure, or monotone

It then shows short interview feedback such as:

```text
You sounded slightly nervous.
Try slowing down, pausing between points, and speaking clearly.
```

## Response Rules

Gemini is prompted to return:

```text
1. Emotional reaction
2. One helpful activity
```

Rules:

- no questions
- two lines maximum
- no repeated generic phrases
- emotion must match the final detected emotion
- fallback is used only when Gemini returns an empty or very short response

## Model Details

- Dataset: RAVDESS Emotional Speech Dataset
- Audio features: MFCC
- Model: Random Forest Classifier
- Base voice model outputs include happy, sad, angry, calm, neutral, and related classes depending on training data
- Voice outputs are normalized into EchoMind's expanded emotion classes

## Limitations

- Emotion detection is approximate and depends on audio quality and transcript accuracy
- Browser speech recognition works best in Chrome or Edge
- Hindi/Gujarati voice recognition depends on selecting the correct voice language
- Translation requires network access when using `deep-translator`
- Gemini-based replies require an API key and internet access
- The system does not diagnose mental health conditions

## Ethical Note

EchoMind is for supportive conversation and educational demonstration only. It does not provide medical advice, diagnosis, crisis support, or professional interview coaching.

## Author

Roshni Raichandani  
B.Tech IT - Semester 6
