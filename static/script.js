let recognition;
let silenceTimer;
let popupTimer;
let isListening = false;
let shouldAutoRestart = false;
let mediaRecorder = null;
let activeStream = null;
let audioChunks = [];
let emotionChart = null;

const languageNames = {
  en: "English",
  hi: "Hindi",
  gu: "Gujarati",
};

function getSelectedVoiceLanguage() {
  const select = document.getElementById("voiceLanguageSelect");
  if (!select) {
    return { code: "en", speechLang: "en-US" };
  }

  const option = select.options[select.selectedIndex];
  return {
    code: select.value || "en",
    speechLang: option && option.dataset.speechLang ? option.dataset.speechLang : "en-US",
  };
}

const state = {
  finalTranscript: "",
  currentChatId: null,
  messages: [],
  histories: [],
  emotionHistory: [],
};

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("textForm");
  const input = document.getElementById("textInput");
  const newChatBtn = document.getElementById("newChatBtn");

  loadHistories();
  initEmotionChart();
  startNewChat(false);
  renderHistoryList();

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const text = input.value.trim();
    if (!text) {
      showPopup("Type a message first.");
      return;
    }

    input.value = "";
    submitUserText(text);
  });

  newChatBtn.addEventListener("click", () => startNewChat(true));
});

function getRecognitionClass() {
  return window.SpeechRecognition || window.webkitSpeechRecognition || null;
}

function releaseMediaStream(stream) {
  if (!stream) return;
  stream.getTracks().forEach((track) => track.stop());
}

function getRecorderOptions() {
  if (!window.MediaRecorder) return {};
  if (MediaRecorder.isTypeSupported("audio/webm;codecs=opus")) {
    return { mimeType: "audio/webm;codecs=opus" };
  }
  if (MediaRecorder.isTypeSupported("audio/webm")) {
    return { mimeType: "audio/webm" };
  }
  return {};
}

function setStatus(label, mode = "") {
  const status = document.getElementById("statusPill");
  status.textContent = label;
  status.className = `status-pill ${mode}`.trim();
}

function updateInsights(data) {
  document.getElementById("moodMetric").textContent = titleCase(data.emotion || data.state || "neutral");
  document.getElementById("sentimentMetric").textContent = titleCase(data.sentiment || "unknown");
  document.getElementById("intentMetric").textContent = titleCase(data.intent || "general");
  document.getElementById("confidenceMetric").textContent = data.confidence
    ? `${Math.round(data.confidence * 100)}%`
    : "--";
  document.getElementById("languageMetric").textContent = languageNames[data.language] || titleCase(data.language || "en");

  document.body.dataset.emotion = data.state || "neutral";
  updateEmotionChart(data.emotion_history || []);
  updateSpikeAlert(data);
  updateInterviewFeedback(data.interview_feedback);
}

function initEmotionChart() {
  const canvas = document.getElementById("emotionChart");
  if (!canvas || !window.Chart) return;

  emotionChart = new Chart(canvas, {
    type: "line",
    data: {
      labels: [],
      datasets: [{
        label: "Mood value",
        data: [],
        borderColor: "#2563eb",
        backgroundColor: "rgba(37, 99, 235, 0.12)",
        pointRadius: 3,
        tension: 0.32,
        fill: true,
      }],
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            label: (context) => {
              const item = state.emotionHistory[context.dataIndex] || {};
              return `${titleCase(item.emotion || "neutral")}: ${item.value}`;
            },
          },
        },
      },
      scales: {
        y: {
          min: -3,
          max: 3,
          ticks: { stepSize: 1 },
        },
        x: {
          ticks: { maxTicksLimit: 6 },
        },
      },
    },
  });
}

function updateEmotionChart(history) {
  if (!emotionChart) return;

  state.emotionHistory = history;
  emotionChart.data.labels = history.map((item) => {
    const date = new Date(item.timestamp);
    return Number.isNaN(date.getTime()) ? "" : date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  });
  emotionChart.data.datasets[0].data = history.map((item) => item.value);
  emotionChart.update();
}

function updateSpikeAlert(data) {
  const alert = document.getElementById("spikeAlert");
  if (!alert) return;
  alert.textContent = data.spike ? data.spike_message || "Your mood changed quickly just now" : "";
}

function updateInterviewFeedback(feedback) {
  const panel = document.getElementById("interviewFeedback");
  if (!panel) return;

  if (!feedback) {
    panel.classList.add("hidden");
    panel.innerHTML = "";
    return;
  }

  panel.classList.remove("hidden");
  panel.innerHTML = `
    <div class="feedback-item"><span class="metric-label">Interview Tone</span><strong>${escapeHtml(titleCase(feedback.tone))}</strong></div>
    <div class="feedback-item"><span class="metric-label">Confidence</span><strong>${Math.round(feedback.confidence_level * 100)}%</strong></div>
    <div class="feedback-item"><span class="metric-label">Stress</span><strong>${Math.round(feedback.stress_level * 100)}%</strong></div>
    <div class="feedback-item"><span class="metric-label">Feedback</span><strong>${escapeHtml(feedback.feedback)}. ${escapeHtml(feedback.suggestion)}</strong></div>
  `;
}

function escapeHtml(value) {
  return String(value || "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function startSpeechRecognition() {
  if (isListening) return;

  if (window.speechSynthesis.speaking) {
    showPopup("Please wait until the assistant finishes speaking.");
    return;
  }

  const RecognitionClass = getRecognitionClass();
  if (!RecognitionClass) {
    showPopup("Speech recognition is not supported in this browser. Use the text box instead.");
    return;
  }

  if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
    showPopup("Microphone access is not available in this browser.");
    return;
  }

  if (!window.MediaRecorder) {
    showPopup("Audio emotion detection is not supported in this browser. Use Chrome or Edge.");
    return;
  }

  try {
    activeStream = await navigator.mediaDevices.getUserMedia({ audio: true });
  } catch (error) {
    showPopup("Microphone access denied or unavailable.");
    return;
  }

  recognition = new RecognitionClass();
  const voiceLanguage = getSelectedVoiceLanguage();
  recognition.lang = voiceLanguage.speechLang;
  recognition.continuous = true;
  recognition.interimResults = true;

  audioChunks = [];
  mediaRecorder = new MediaRecorder(activeStream, getRecorderOptions());
  mediaRecorder.ondataavailable = (event) => {
    if (event.data && event.data.size > 0) {
      audioChunks.push(event.data);
    }
  };

  isListening = true;
  shouldAutoRestart = true;
  state.finalTranscript = "";
  document.getElementById("liveText").textContent = "";

  recognition.onstart = () => {
    setStatus("Listening", "listening");
    showPopup("Listening...");
  };

  recognition.onresult = (event) => {
    let interim = "";
    let finalText = state.finalTranscript;

    for (let i = event.resultIndex; i < event.results.length; i++) {
      const transcript = event.results[i][0].transcript.trim();
      if (event.results[i].isFinal) {
        finalText = `${finalText} ${transcript}`.trim();
      } else {
        interim = `${interim} ${transcript}`.trim();
      }
    }

    state.finalTranscript = finalText;
    document.getElementById("liveText").textContent = interim || finalText;

    clearTimeout(silenceTimer);
    silenceTimer = setTimeout(() => stopSpeechRecognition(false), 1800);
  };

  recognition.onerror = (event) => {
    isListening = false;
    setStatus("Ready");

    const errorType = event && event.error ? event.error : "unknown";
    if (errorType === "not-allowed" || errorType === "service-not-allowed") {
      shouldAutoRestart = false;
      stopActiveRecording();
      showPopup("Microphone permission blocked. Allow mic and try again.");
      return;
    }

    if (errorType === "no-speech") {
      stopActiveRecording();
      showPopup("No speech detected. Try speaking a little louder.");
      return;
    }

    stopActiveRecording();
    showPopup(`Speech recognition error: ${errorType}`);
  };

  recognition.onend = () => {
    isListening = false;
    setStatus("Ready");
  };

  try {
    mediaRecorder.start();
    recognition.start();
  } catch (error) {
    isListening = false;
    shouldAutoRestart = false;
    stopActiveRecording();
    setStatus("Ready");
    showPopup("Could not start speech recognition.");
  }
}

function stopActiveRecording() {
  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.onstop = null;
    mediaRecorder.stop();
  }
  mediaRecorder = null;
  audioChunks = [];
  releaseMediaStream(activeStream);
  activeStream = null;
}

function stopSpeechRecognition(manual = false) {
  if (recognition && isListening) {
    recognition.stop();
  }

  shouldAutoRestart = !manual;
  isListening = false;
  clearTimeout(silenceTimer);
  setStatus("Ready");

  const text = state.finalTranscript.trim() || document.getElementById("liveText").textContent.trim();
  document.getElementById("liveText").textContent = "";

  if (mediaRecorder && mediaRecorder.state !== "inactive") {
    mediaRecorder.onstop = () => {
      const audioBlob = new Blob(audioChunks, { type: mediaRecorder.mimeType || "audio/webm" });
      releaseMediaStream(activeStream);
      activeStream = null;
      mediaRecorder = null;
      audioChunks = [];

      if (audioBlob.size > 0) {
        submitUserVoice(text || "Voice message", audioBlob);
      } else if (text) {
        submitUserText(text);
      } else {
        showPopup("Stopped. No speech captured.");
      }
    };
    mediaRecorder.stop();
    return;
  }

  releaseMediaStream(activeStream);
  activeStream = null;

  if (!text) {
    showPopup("Stopped. No speech captured.");
    return;
  }

  submitUserText(text);
}

function submitUserText(text) {
  addMessage(text, "user");
  rememberMessage("user", text);
  showTyping();
  setStatus("Thinking", "thinking");
  sendText(text);
}

function submitUserVoice(text, audioBlob) {
  addMessage(text, "user");
  rememberMessage("user", text);
  showTyping();
  const voiceLanguage = getSelectedVoiceLanguage();
  setStatus(`Voice: ${languageNames[voiceLanguage.code] || "English"}`, "thinking");
  sendVoice(text, audioBlob);
}

async function sendText(text) {
  try {
    const response = await fetch("/process_text", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ text }),
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not process that message.");
    }

    removeTyping();
    updateInsights(data);
    addBotResponse(data);
    rememberMessage("bot", data.response, data);
    speakText(data.response);
  } catch (error) {
    removeTyping();
    addMessage(error.message, "bot");
    showPopup(error.message);
  } finally {
    setStatus("Ready");
  }
}

async function sendVoice(text, audioBlob) {
  const voiceLanguage = getSelectedVoiceLanguage();
  const formData = new FormData();
  formData.append("text", text);
  formData.append("audio", audioBlob, "voice.webm");
  formData.append("language", voiceLanguage.code);
  formData.append("interview_mode", document.getElementById("interviewModeToggle").checked ? "true" : "false");

  try {
    const response = await fetch("/process", {
      method: "POST",
      body: formData,
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "Could not process that voice message.");
    }

    removeTyping();
    updateInsights(data);
    addBotResponse(data);
    rememberMessage("bot", data.response, data);
    speakText(data.response);
  } catch (error) {
    removeTyping();
    addMessage(error.message, "bot");
    showPopup(error.message);
  } finally {
    setStatus("Ready");
  }
}

function addMessage(text, sender) {
  const chatBox = document.getElementById("chatBox");
  const wrapper = document.createElement("div");
  wrapper.classList.add("msg-wrapper", sender);

  const msg = document.createElement("div");
  msg.classList.add("message");
  msg.textContent = text;

  const timeEl = document.createElement("span");
  timeEl.classList.add("time");
  timeEl.textContent = getTime();

  wrapper.appendChild(msg);
  wrapper.appendChild(timeEl);
  chatBox.appendChild(wrapper);
  scrollChat();
}

function addBotResponse(data) {
  const chatBox = document.getElementById("chatBox");
  const wrapper = document.createElement("div");
  wrapper.classList.add("msg-wrapper", "bot");
  wrapper.dataset.emotion = data.state || "neutral";

  const msg = document.createElement("div");
  msg.classList.add("message");

  const body = document.createElement("p");
  body.textContent = data.response;

  msg.appendChild(body);

  const timeEl = document.createElement("span");
  timeEl.classList.add("time");
  timeEl.textContent = getTime();

  wrapper.appendChild(msg);
  wrapper.appendChild(timeEl);
  chatBox.appendChild(wrapper);
  scrollChat();
}

function showTyping() {
  const chatBox = document.getElementById("chatBox");
  const wrapper = document.createElement("div");
  wrapper.classList.add("msg-wrapper", "bot");
  wrapper.id = "typing";

  const msg = document.createElement("div");
  msg.classList.add("message", "typing");
  msg.innerHTML = '<span></span><span></span><span></span>';

  wrapper.appendChild(msg);
  chatBox.appendChild(wrapper);
  scrollChat();
}

function removeTyping() {
  const typing = document.getElementById("typing");
  if (typing) typing.remove();
}

function speakText(text) {
  if (!("speechSynthesis" in window)) return;

  window.speechSynthesis.cancel();
  const speech = new SpeechSynthesisUtterance(text);
  speech.lang = "en-US";
  speech.rate = 0.96;

  speech.onend = () => {
    const autoListen = document.getElementById("autoListenToggle").checked;
    if (autoListen && shouldAutoRestart) {
      setTimeout(() => startSpeechRecognition(), 350);
    }
  };

  window.speechSynthesis.speak(speech);
}

function showPopup(message) {
  const popup = document.getElementById("popup");
  clearTimeout(popupTimer);

  popup.textContent = message;
  popup.classList.remove("hidden");
  requestAnimationFrame(() => popup.classList.add("show"));

  popupTimer = setTimeout(() => {
    popup.classList.remove("show");
    setTimeout(() => popup.classList.add("hidden"), 250);
  }, 2600);
}

function getTime() {
  return new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });
}

function titleCase(value) {
  return String(value || "")
    .split(" ")
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(" ");
}

function scrollChat() {
  const chatBox = document.getElementById("chatBox");
  chatBox.scrollTop = chatBox.scrollHeight;
}

function loadHistories() {
  try {
    state.histories = JSON.parse(localStorage.getItem("echomindChats")) || [];
  } catch (error) {
    state.histories = [];
  }
}

function saveHistories() {
  localStorage.setItem("echomindChats", JSON.stringify(state.histories.slice(0, 12)));
}

function startNewChat(resetServer = true) {
  state.currentChatId = window.crypto && crypto.randomUUID ? crypto.randomUUID() : String(Date.now());
  state.messages = [];
  resetChatBox();
  updateInsights({
    emotion: "neutral",
    state: "neutral",
    sentiment: "waiting",
    intent: "general",
    language: "en",
    emotion_history: [],
  });

  if (resetServer) {
    fetch("/reset_memory", { method: "POST" }).catch(() => {});
  }
}

function resetChatBox() {
  const chatBox = document.getElementById("chatBox");
  chatBox.innerHTML = "";
  addMessage("Hey, I am here. Send text or use voice and I will read the mood.", "bot");
}

function rememberMessage(sender, text, meta = {}) {
  const message = {
    sender,
    text,
    meta,
    time: getTime(),
  };
  state.messages.push(message);

  const titleSource = state.messages.find((item) => item.sender === "user");
  const title = titleSource ? titleSource.text.slice(0, 42) : "New chat";
  const existingIndex = state.histories.findIndex((item) => item.id === state.currentChatId);
  const chat = {
    id: state.currentChatId,
    title,
    updatedAt: Date.now(),
    messages: state.messages,
  };

  if (existingIndex >= 0) {
    state.histories.splice(existingIndex, 1);
  }
  state.histories.unshift(chat);
  saveHistories();
  renderHistoryList();
}

function renderHistoryList() {
  const list = document.getElementById("historyList");
  list.innerHTML = "";

  if (state.histories.length === 0) {
    const empty = document.createElement("p");
    empty.classList.add("history-empty");
    empty.textContent = "No chats yet";
    list.appendChild(empty);
    return;
  }

  state.histories.forEach((chat) => {
    const button = document.createElement("button");
    button.type = "button";
    button.classList.add("history-item");
    if (chat.id === state.currentChatId) {
      button.classList.add("active");
    }
    button.textContent = chat.title;
    button.addEventListener("click", () => loadChat(chat.id));
    list.appendChild(button);
  });
}

function loadChat(chatId) {
  const chat = state.histories.find((item) => item.id === chatId);
  if (!chat) return;

  state.currentChatId = chat.id;
  state.messages = [...chat.messages];

  const chatBox = document.getElementById("chatBox");
  chatBox.innerHTML = "";

  state.messages.forEach((item) => {
    if (item.sender === "bot" && item.meta) {
      addBotResponse({
        response: item.text,
        state: item.meta.state || "neutral",
        intent: item.meta.intent || "general",
      });
    } else {
      addMessage(item.text, item.sender);
    }
  });

  renderHistoryList();
}
