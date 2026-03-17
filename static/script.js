let recognition;
let silenceTimer;
let isListening = false;

function startSpeechRecognition() {
  if (isListening) return;
  if (window.speechSynthesis.speaking) return;
  showPopup("🎤 Listening...");

  recognition = new (
    window.SpeechRecognition || window.webkitSpeechRecognition
  )();
  recognition.lang = "en-US";
  recognition.continuous = true;
  recognition.interimResults = true;

  isListening = true;
  window.finalTranscript = "";

  recognition.start();

  recognition.onresult = function (event) {
    let transcript = "";

    for (let i = event.resultIndex; i < event.results.length; i++) {
      transcript += event.results[i][0].transcript;
    }

    document.getElementById("liveText").innerText = transcript;

    window.finalTranscript = transcript;

    // 🔥 RESET SILENCE TIMER
    clearTimeout(silenceTimer);

    silenceTimer = setTimeout(() => {
      stopSpeechRecognition();
    }, 2000); // 2 sec silence
  };

  recognition.onerror = function () {
    isListening = false;
  };
}

// ⏹ STOP (AUTO + MANUAL)
function stopSpeechRecognition() {
  if (!isListening) return;

  recognition.stop();
  isListening = false;

  let text = window.finalTranscript || "";

  if (text.trim() !== "") {
    addMessage(text, "user");
    showTyping();
    sendText(text);
  }
  showPopup("🎤 Stopped listening.");

  document.getElementById("liveText").innerText = "";
}

// 📤 Send to backend
function sendText(text) {
  fetch("/process_text", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ text: text }),
  })
    .then((res) => res.json())
    .then((data) => {
      removeTyping();

      let emojiMap = {
        calm: "😊",
        stress: "😓",
        "low mood": "💙",
        neutral: "🙂",
      };
      let fullResponse = `Emotion: ${data.emotion} ${emojiMap[data.emotion] || ""}
      
      ${data.response}`;

      typingEffect(fullResponse);
      speakText(data.response);
    });
}

// 💬 Add message with timestamp
function addMessage(text, sender) {
  let chatBox = document.getElementById("chatBox");

  let wrapper = document.createElement("div");
  wrapper.classList.add("msg-wrapper", sender);

  let msg = document.createElement("div");
  msg.classList.add("message");

  let time = new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  msg.innerText = text;

  let timeEl = document.createElement("span");
  timeEl.classList.add("time");
  timeEl.innerText = time;

  wrapper.appendChild(msg);
  wrapper.appendChild(timeEl);

  chatBox.appendChild(wrapper);
  chatBox.scrollTop = chatBox.scrollHeight;
}
function typingEffect(text) {
  let chatBox = document.getElementById("chatBox");

  let wrapper = document.createElement("div");
  wrapper.classList.add("msg-wrapper", "bot");

  let msg = document.createElement("div");
  msg.classList.add("message");
  msg.style.whiteSpace = "pre-wrap"; // ✅ add this line
  msg.style.wordSpacing = "normal"; // ✅ add this line
  let time = new Date().toLocaleTimeString([], {
    hour: "2-digit",
    minute: "2-digit",
  });

  let timeEl = document.createElement("span");
  timeEl.classList.add("time");
  timeEl.innerText = time;

  wrapper.appendChild(msg);
  wrapper.appendChild(timeEl);
  chatBox.appendChild(wrapper);

  let words = text.split(" ");
  let i = 0;

  let interval = setInterval(() => {
    msg.innerText += words[i] + " ";
    i++;

    if (i >= words.length) clearInterval(interval);

    chatBox.scrollTop = chatBox.scrollHeight;
  }, 60);
}

// 🔄 Typing dots animation
function showTyping() {
  let chatBox = document.getElementById("chatBox");

  let msg = document.createElement("div");
  msg.classList.add("message", "bot");
  msg.id = "typing";

  msg.innerHTML = `<span class="dots">Typing...</span>`;

  chatBox.appendChild(msg);
  chatBox.scrollTop = chatBox.scrollHeight;
}

function removeTyping() {
  let t = document.getElementById("typing");
  if (t) t.remove();
}

// 🔊 Speak
function speakText(text) {
  const speech = new SpeechSynthesisUtterance(text);
  speech.lang = "en-US";

  // 🔥 When bot finishes speaking → restart listening
  speech.onend = () => {
    startSpeechRecognition();
  };

  window.speechSynthesis.speak(speech);
}
function showPopup(message) {
  let popup = document.getElementById("popup");

  popup.innerText = message;
  popup.classList.remove("hidden");
  popup.classList.add("show");

  setTimeout(() => {
    popup.classList.remove("show");
    setTimeout(() => popup.classList.add("hidden"), 300);
  }, 2000);
}