// static/app.js
const btnTTS = document.getElementById('btnTTS');
const ttsText = document.getElementById('ttsText');
const ttsAudio = document.getElementById('ttsAudio');

btnTTS.onclick = async () => {
  const text = ttsText.value;
  btnTTS.disabled = true;
  btnTTS.innerText = "Thinking...";
  try {
    const res = await fetch('/tts', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({text})
    });
    if (!res.ok) {
      const err = await res.json();
      alert("TTS error: " + (err.error || res.statusText));
      return;
    }
    const blob = await res.blob();
    const url = URL.createObjectURL(blob);
    ttsAudio.style.display = 'block';
    ttsAudio.src = url;
    ttsAudio.play();
  } catch (e) {
    alert("Request failed: " + e);
  } finally {
    btnTTS.disabled = false;
    btnTTS.innerText = "Speak";
  }
};

// Upload file for STT
const fileInput = document.getElementById('fileInput');
const btnUpload = document.getElementById('btnUpload');
const resultText = document.getElementById('resultText');

btnUpload.onclick = async () => {
  if (!fileInput.files.length) { alert("Choose a file first"); return; }
  const fd = new FormData();
  fd.append('file', fileInput.files[0]);
  btnUpload.disabled = true;
  btnUpload.innerText = "Transcribing...";
  try {
    const r = await fetch('/stt', {method:'POST', body: fd});
    const j = await r.json();
    if (r.ok) {
      resultText.innerText = j.text;
    } else {
      resultText.innerText = "Error: " + (j.error || JSON.stringify(j));
    }
  } catch (e) {
    resultText.innerText = "Request failed: " + e;
  } finally {
    btnUpload.disabled = false;
    btnUpload.innerText = "Transcribe Upload";
  }
};

// Simple browser recording (WebM). The backend will convert to WAV with ffmpeg/pydub.
let mediaRecorder = null;
let chunks = [];
const recordBtn = document.getElementById('recordBtn');
const recStatus = document.getElementById('recStatus');

recordBtn.onclick = async () => {
  if (!mediaRecorder || mediaRecorder.state === 'inactive') {
    // start
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);
    chunks = [];
    mediaRecorder.ondataavailable = e => chunks.push(e.data);
    mediaRecorder.onstop = async () => {
      recStatus.innerText = 'Uploading...';
      const blob = new Blob(chunks, { type: 'audio/webm' });
      const fd = new FormData();
      fd.append('file', blob, 'recording.webm');
      try {
        const r = await fetch('/stt', {method:'POST', body: fd});
        const j = await r.json();
        if (r.ok) resultText.innerText = j.text;
        else resultText.innerText = "Error: " + (j.error || JSON.stringify(j));
      } catch (e) {
        resultText.innerText = "Upload failed: " + e;
      } finally {
        recStatus.innerText = '';
        recordBtn.innerText = 'Record';
      }
    };
    mediaRecorder.start();
    recordBtn.innerText = 'Stop';
    recStatus.innerText = 'Recording...';
  } else {
    // stop
    mediaRecorder.stop();
    recStatus.innerText = 'Stopping...';
  }
};
