# 🧠 EchoMind - Real-Time Emotion-Aware Conversational AI

## 📌 Project Overview

**EchoMind** is a real-time voice-based conversational AI system that detects user emotions from speech and text, and responds empathetically using voice and chat.

The system integrates:

- 🎤 Speech Recognition
- 🧠 Machine Learning (Emotion Detection)
- 😊 Sentiment Analysis
- 💬 ChatGPT-style UI
- 🔊 Text-to-Speech

---

## 🎯 Objectives

- Capture live voice input
- Convert speech to text
- Detect emotional state using ML + NLP
- Generate empathetic responses
- Provide voice output
- Maintain continuous conversation

---

## ✨ Key Features

### 🎤 Voice Interaction

- Real-time speech input (Web Speech API)
- Silence detection (auto-stop)
- Manual Start/Stop controls

### 🧠 Emotion Detection

- MFCC feature extraction (Librosa)
- Random Forest model
- Emotion smoothing

### 😊 Sentiment Analysis

- TextBlob-based sentiment detection
- Combined with emotion for accuracy

### 💬 Conversational UI

- ChatGPT-style interface
- Chat bubbles + timestamps
- Typing animation
- Smooth scrolling

### 🔊 Voice Output

- Browser-based Text-to-Speech
- Continuous conversation loop

---

## 🧩 System Architecture

```text
User Voice
⬇
Speech Recognition (Browser)
⬇
Flask Backend
⬇
Emotion + Sentiment Analysis
⬇
Response Generation
⬇
Text-to-Speech (Browser)
⬇
Continuous Conversation
```

---

## 🛠️ Tech Stack

### Frontend

- HTML5
- CSS3
- JavaScript (Vanilla)
- Web Speech API

### Backend

- Python
- Flask

### Machine Learning

- Scikit-learn (Random Forest)
- Librosa (MFCC)
- NumPy
- Pandas

### NLP

- TextBlob

---

## 📁 Project Structure

```text
EchoMind/
│
├── data/
├── models/
│
├── static/
│   ├── style.css
│   └── script.js
│
├── templates/
│   └── index.html
│
├── emotion_detection.py
├── sentiment_analysis.py
├── response_generator.py
├── emotion_smoother.py
├── train_model.py
├── app.py
│
├── requirements.txt
└── README.md
```

---

## ⚙️ Installation & Setup

### 1️⃣ Clone Repository

```bash
git clone https://github.com/rrv1504/EchoMind-AI.git
cd EchoMind-AI
```

### 2️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 3️⃣ Install TextBlob Data

```bash
python -m textblob.download_corpora
```

---

## ⚙️ Additional Setup (IMPORTANT)

### 🎧 FFmpeg Installation (Required for Audio Processing)

EchoMind uses FFmpeg to convert browser-recorded audio (WebM) into WAV format.

#### 🔹 Windows Setup

1. Download FFmpeg:  
   https://www.gyan.dev/ffmpeg/builds/

2. Extract and move to:

```text
C:\ffmpeg
```

3. Add to PATH:

```text
C:\ffmpeg\bin
```

4. Restart terminal

5. Verify:

```bash
ffmpeg -version
```

### 🔹 Install pydub

```bash
pip install pydub
```

### 🔹 Why FFmpeg?

- Browser records audio in WebM format
- ML model requires WAV
- FFmpeg converts audio formats

---

## 🔄 Audio Processing Flow

```text
Browser Audio (WebM)
⬇
FFmpeg Conversion
⬇
WAV File
⬇
MFCC Extraction
⬇
Emotion Detection
```

---

## ▶️ Run Project

```bash
python app.py
```

Open:  
http://127.0.0.1:5000

---

## 🧪 How to Use

1. Click 🎤 Start
2. Speak naturally
3. Stop speaking -> auto-detected
4. System:
   - Shows text
   - Detects emotion
   - Responds
   - Speaks output
5. Conversation continues automatically

---

## 📊 Dataset

- RAVDESS Emotional Speech Dataset
- Emotions:
  - Happy
  - Sad
  - Angry
  - Calm
  - Neutral

---

## 🧠 Model Details

- Algorithm: Random Forest
- Features: MFCC
- Input: Audio
- Output: Emotion label

---

## ⚠️ Limitations

- Basic ML model (not deep learning)
- Accuracy depends on speech clarity
- Works best in Chrome browser
- Simplified emotion detection logic

---

## 🚀 Future Enhancements

- Deep Learning (CNN/LSTM)
- Emotion history tracking
- Mobile app (Flutter)
- Chat memory
- Cloud deployment

---

## 🛡️ Ethical Considerations

- ❌ Does NOT diagnose mental illness
- ✅ Detects emotional cues only
- ⚠️ Provides general well-being suggestions

---

## 🎓 Learning Outcomes

- Speech processing
- Machine Learning integration
- NLP techniques
- Full-stack AI application
- Human-centered design

---

## 👩‍💻 Author

**Roshni Raichandani**  
B.Tech IT - Semester 6

---

## ⭐ Acknowledgements

- RAVDESS Dataset
- Scikit-learn
- Librosa
- Flask
- Web Speech API

---

## 📌 Conclusion

EchoMind demonstrates how AI can create emotionally aware conversational systems that enhance user interaction through voice and empathy.

---
