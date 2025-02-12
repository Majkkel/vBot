document.addEventListener("DOMContentLoaded", () => {
  const chatBox = document.getElementById("chatBox");
  const userInput = document.getElementById("userInput");
  const sendBtn = document.getElementById("sendBtn");
  const recordBtn = document.getElementById("recordBtn");

  // Ikony jako stałe łańcuchy HTML
  const microphoneIcon = `
  <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
    <path fill-rule="evenodd" d="M5 8a1 1 0 0 1 1 1v3a4.006 4.006 0 0 0 4 4h4a4.006 4.006 0 0 0 4-4V9a1 1 0 1 1 2 0v3.001A6.006 6.006 0 0 1 14.001 18H13v2h2a1 1 0 1 1 0 2H9a1 1 0 1 1 0-2h2v-2H9.999A6.006 6.006 0 0 1 4 12.001V9a1 1 0 0 1 1-1Z" clip-rule="evenodd"/>
    <path d="M7 6a4 4 0 0 1 4-4h2a4 4 0 0 1 4 4v5a4 4 0 0 1-4 4h-2a4 4 0 0 1-4-4V6Z"/>
  </svg>

`;

  const stopIcon = `
  <svg class="w-6 h-6 text-gray-800 dark:text-white" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" width="24" height="24" fill="currentColor" viewBox="0 0 24 24">
    <path d="M7 5a2 2 0 0 0-2 2v10a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V7a2 2 0 0 0-2-2H7Z"/>
  </svg>

`;

  sendBtn.addEventListener("click", sendMessage);
  userInput.addEventListener("keyup", function (e) {
    if (e.key === "Enter") sendMessage();
  });

  // Zmienne globalne do nagrywania
  let audioContext;
  let processor; // ScriptProcessorNode
  let input; // MediaStreamAudioSourceNode
  let audioData = []; // Tablica z fragmentami danych audio
  let isRecording = false;

  recordBtn.addEventListener("click", toggleRecording);

  function sendMessage() {
    const message = userInput.value.trim();
    if (!message) return;
    addMessage("user", message);
    userInput.value = "";

    fetch("http://localhost:5000/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: message }),
    })
      .then((response) => response.json())
      .then((data) => {
        const responseText = data.response;
        addMessage("bot", responseText);
        // Opcjonalnie: odtwarzanie dźwiękowej odpowiedzi (endpoint /tts)
        playAudio(responseText);
      })
      .catch((error) => {
        console.error("Błąd:", error);
        addMessage("bot", "Wystąpił błąd podczas wysyłania zapytania.");
      });
  }

  function addMessage(sender, text) {
    const messageElem = document.createElement("div");
    messageElem.classList.add("message", sender);
    messageElem.textContent = (sender === "user" ? "Ty: " : "Bot: ") + text;
    chatBox.appendChild(messageElem);
    chatBox.scrollTop = chatBox.scrollHeight;
  }

  function playAudio(text) {
    fetch("http://localhost:5000/tts", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text: text }),
    })
      .then((response) => response.blob())
      .then((blob) => {
        const audioUrl = URL.createObjectURL(blob);
        const audio = new Audio(audioUrl);
        audio.play();
      })
      .catch((error) => {
        console.error("Błąd TTS:", error);
      });
  }

  function toggleRecording() {
    if (isRecording) {
      stopRecording()
        .then((blob) => {
          sendAudioForRecognition(blob);
        })
        .catch((err) => console.error(err));
      recordBtn.innerHTML = microphoneIcon;
      isRecording = false;
    } else {
      startRecording();
      recordBtn.innerHTML = stopIcon;
      isRecording = true;
    }
  }

  function startRecording() {
    audioData = []; // Resetujemy zebrane dane
    navigator.mediaDevices
      .getUserMedia({ audio: true })
      .then((stream) => {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        input = audioContext.createMediaStreamSource(stream);
        // Używamy ScriptProcessorNode; rozmiar bufora 4096, 1 kanał wejściowy i 1 wyjściowy
        processor = audioContext.createScriptProcessor(4096, 1, 1);
        processor.onaudioprocess = function (e) {
          const channelData = e.inputBuffer.getChannelData(0);
          audioData.push(new Float32Array(channelData));
        };
        input.connect(processor);
        processor.connect(audioContext.destination);
      })
      .catch((error) => {
        console.error("Błąd przy uzyskiwaniu dostępu do mikrofonu:", error);
      });
  }

  function stopRecording() {
    return new Promise((resolve, reject) => {
      if (!isRecording) {
        reject("Nagrywanie nie zostało rozpoczęte.");
        return;
      }
      processor.disconnect();
      input.disconnect();
      audioContext
        .close()
        .then(() => {
          const length = audioData.reduce((acc, cur) => acc + cur.length, 0);
          const samples = new Float32Array(length);
          let offset = 0;
          for (let i = 0; i < audioData.length; i++) {
            samples.set(audioData[i], offset);
            offset += audioData[i].length;
          }
          const wavBuffer = encodeWAV(samples, audioContext.sampleRate);
          const blob = new Blob([wavBuffer], { type: "audio/wav" });
          isRecording = false;
          resolve(blob);
        })
        .catch(reject);
    });
  }

  function sendAudioForRecognition(blob) {
    const formData = new FormData();
    formData.append("audio", blob, "recording.wav");
    fetch("http://localhost:5000/asr", {
      method: "POST",
      body: formData,
    })
      .then((response) => response.json())
      .then((data) => {
        const recognizedText = data.text;
        userInput.value = recognizedText;
      })
      .catch((error) => {
        console.error("Błąd podczas wysyłania nagrania:", error);
      });
  }

  function encodeWAV(samples, sampleRate) {
    const buffer = new ArrayBuffer(44 + samples.length * 2);
    const view = new DataView(buffer);

    writeString(view, 0, "RIFF");
    view.setUint32(4, 36 + samples.length * 2, true);
    writeString(view, 8, "WAVE");
    writeString(view, 12, "fmt ");
    view.setUint32(16, 16, true);
    view.setUint16(20, 1, true);
    view.setUint16(22, 1, true);
    view.setUint32(24, sampleRate, true);
    view.setUint32(28, sampleRate * 2, true);
    view.setUint16(32, 2, true);
    view.setUint16(34, 16, true);
    writeString(view, 36, "data");
    view.setUint32(40, samples.length * 2, true);

    floatTo16BitPCM(view, 44, samples);
    return view;
  }

  function floatTo16BitPCM(output, offset, input) {
    for (let i = 0; i < input.length; i++, offset += 2) {
      let s = Math.max(-1, Math.min(1, input[i]));
      output.setInt16(offset, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
  }

  function writeString(view, offset, string) {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i));
    }
  }
});
