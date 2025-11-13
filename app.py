<<<<<<< HEAD
from flask import Flask, render_template_string, request, jsonify
from openai import AzureOpenAI
import os
import traceback

# Azure OpenAI configuration
AZURE_ENDPOINT = "AZURE_OPENAI_ENDPOINT"
AZURE_KEY = "AZURE_OPENAI_KEY"
DEPLOYMENT = "AZURE_DEPLOYMENT_NAME"  # e.g. "gpt-4o-mini"
API_VERSION = "API_VERSION"   # or "2025-04-01-preview" if your resource supports it

client = AzureOpenAI(
    azure_endpoint=AZURE_ENDPOINT,
    api_key=AZURE_KEY,
    api_version=API_VERSION
)

# ----------------------------
# FLASK APP
# ----------------------------
app = Flask(__name__)

# ----------------------------
# HTML + CSS + JS
# ----------------------------
HTML_PAGE = """ 
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8" />
<meta name="viewport" content="width=device-width,initial-scale=1" />
<title>Azure OpenAI Chatbot</title>
<style>
:root{
  --bg:#eef6ff;
  --card:#ffffff;
  --muted:#6b7280;
  --blue-600:#1e90ff;
  --blue-700:#1662c4;
  --input-bg:#f3f7ff;
  --user-bubble:#dff3ff;
  --bot-bubble:#e9f1ff;
}
html,body{height:100%;margin:0;font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",Roboto,"Helvetica Neue",Arial;color:#0b1a2b;background:linear-gradient(180deg,var(--bg),#f8fbff);}
.wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:28px;}
.container{width:100%;max-width:900px;background:var(--card);border-radius:16px;box-shadow:0 12px 40px rgba(16,24,40,0.08);overflow:hidden;border:1px solid rgba(15,23,42,0.04);}
.header{display:flex;align-items:center;gap:16px;padding:22px 28px;background:linear-gradient(90deg,var(--blue-600),var(--blue-700));color:white;}
.logo{width:52px;height:52px;border-radius:10px;background:rgba(255,255,255,0.12);display:flex;align-items:center;justify-content:center;font-weight:700;box-shadow:0 6px 16px rgba(16,24,40,0.08);}
.title{font-size:20px;font-weight:700;letter-spacing:0.2px;}
.subtitle{font-size:13px;opacity:0.95}
.main{display:flex;gap:24px;padding:20px 28px 28px;flex-direction:column;}
#chat{height:62vh;min-height:360px;border-radius:12px;padding:18px;overflow:auto;background:linear-gradient(180deg,#fcfeff,#f7fbff);border:1px solid rgba(14,45,114,0.04);}
.row{display:flex;align-items:flex-end;margin:10px 0;gap:12px;}
.row.user{justify-content:flex-end;}
.avatar{width:34px;height:34px;border-radius:10px;flex:0 0 34px;display:flex;align-items:center;justify-content:center;font-weight:700;color:white;background:var(--blue-700);box-shadow:0 6px 18px rgba(20,40,80,0.06);}
.bubble{max-width:78%;padding:12px 14px;border-radius:12px;line-height:1.45;box-shadow:0 6px 18px rgba(12,24,48,0.04);}
.bubble.user{background:var(--user-bubble);color:#05203a;border-bottom-right-radius:4px;}
.bubble.bot{background:var(--bot-bubble);color:#02204a;border-bottom-left-radius:4px;}
.metadata{font-size:12px;color:var(--muted);margin-top:6px;text-align:right;}
.controls{display:flex;gap:12px;margin-top:14px;align-items:center;}
#prompt{flex:1;padding:12px 14px;border-radius:12px;border:1px solid rgba(14,45,114,0.06);background:var(--input-bg);outline:none;font-size:15px;}
#send{background:var(--blue-600);border:none;color:white;padding:11px 16px;border-radius:12px;cursor:pointer;font-weight:600;box-shadow:0 8px 18px rgba(30,144,255,0.14);}
#send:disabled{opacity:0.6;cursor:not-allowed}
.footer{display:flex;justify-content:space-between;align-items:center;margin-top:10px;color:var(--muted);font-size:13px;}
.hint{font-size:12px;color:#234a7a}
@media(max-width:720px){
  .container{border-radius:12px;margin:8px;}
  .header{padding:16px}
  #chat{height:56vh}
}
</style>
</head>
<body>
<div class="wrap">
<div class="container" role="main" aria-labelledby="title">
<div class="header">
<div class="logo">AI</div>
<div>
<div id="title" class="title">Azure OpenAI Chatbot</div>
<div class="subtitle">A simple demo powered by your Azure deployment</div>
</div>
</div>

<div class="main">
<div id="chat" aria-live="polite" aria-label="Chat messages"></div>

<div class="controls">
<input id="prompt" placeholder="Say hello... (press Enter to send)" autocomplete="off" />
<button id="send">Send</button>
</div>

<div class="footer">
<div class="hint">Tip: type <code>quit</code> to end the session</div>
<div class="hint">Status: <span id="status">Ready</span></div>
</div>
</div>
</div>
</div>

<script>
const chatEl = document.getElementById('chat');
const promptEl = document.getElementById('prompt');
const sendBtn = document.getElementById('send');
const statusEl = document.getElementById('status');

function appendMessage(text, role){
  const wrapper = document.createElement('div');
  wrapper.className = 'row ' + (role === 'user' ? 'user' : 'bot');

  if(role === 'user'){
    const bubble = document.createElement('div');
    bubble.className = 'bubble user';
    bubble.textContent = text;
    wrapper.appendChild(bubble);
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = 'You';
    wrapper.appendChild(avatar);
  } else {
    const avatar = document.createElement('div');
    avatar.className = 'avatar';
    avatar.textContent = 'AI';
    wrapper.appendChild(avatar);
    const bubble = document.createElement('div');
    bubble.className = 'bubble bot';
    bubble.textContent = text;
    wrapper.appendChild(bubble);
  }
  chatEl.appendChild(wrapper);
  chatEl.scrollTop = chatEl.scrollHeight;
}

function setStatus(s){ statusEl.textContent = s; }

async function sendMessage(){
  const text = promptEl.value.trim();
  if(!text) return;
  appendMessage(text, 'user');
  promptEl.value = '';
  setStatus('Thinking...');
  sendBtn.disabled = true;

  const placeholder = document.createElement('div');
  placeholder.className = 'row bot';
  placeholder.innerHTML = '<div class="avatar">AI</div><div class="bubble bot">…</div>';
  chatEl.appendChild(placeholder);
  chatEl.scrollTop = chatEl.scrollHeight;

  try{
    const res = await fetch('/chat', {
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body: JSON.stringify({message: text})
    });
    const data = await res.json();

    if (placeholder.parentNode) placeholder.remove();

    if(res.ok && data.reply){
      appendMessage(data.reply, 'bot');
      setStatus('Ready');
    } else {
      appendMessage(data.reply || 'Unknown error', 'bot');
      setStatus('Error');
      console.error('Chat error:', data);
    }
  } catch(err){
    if (placeholder.parentNode) placeholder.remove();
    appendMessage('Network error: ' + err.message, 'bot');
    setStatus('Network error');
    console.error(err);
  } finally {
    sendBtn.disabled = false;
    promptEl.focus();
  }
}

sendBtn.addEventListener('click', sendMessage);
promptEl.addEventListener('keydown', (e) => {
  if(e.key === 'Enter' && !e.shiftKey){
    e.preventDefault();
    sendMessage();
  }
});

promptEl.focus();
</script>
</body>
</html>
"""

# ----------------------------
# ROUTES
# ----------------------------
@app.route("/")
def index():
    return render_template_string(HTML_PAGE)

@app.route("/ping", methods=["GET"])
def ping():
    try:
        resp = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[{"role":"user","content":"ping"}],
            max_completion_tokens=5
        )
        reply = resp.choices[0].message.content if resp.choices else "No response"
        return jsonify({"ok": True, "reply": reply})
    except Exception as e:
        tb = traceback.format_exc()
        return jsonify({"ok": False, "error_type": type(e).__name__, "error_str": str(e), "trace": tb}), 500

@app.route("/chat", methods=["POST"])
def chat():
    data = request.get_json()
    user_message = data.get("message", "")
    if not user_message:
        return jsonify({"reply": "Please send a message."}), 400

    try:
        response = client.chat.completions.create(
            model=DEPLOYMENT,
            messages=[{"role": "user", "content": user_message}],
            max_completion_tokens=500
        )
        reply = response.choices[0].message.content if response.choices else "No response from AI."
    except Exception as e:
        reply = f"Error: {str(e)}"
    return jsonify({"reply": reply})

# ----------------------------
# MAIN
# ----------------------------
if __name__ == "__main__":
    app.run(debug=True)
=======
# app.py
import os
import uuid
import tempfile
from flask import Flask, render_template, request, jsonify, send_file
from dotenv import load_dotenv
from pydub import AudioSegment

# Azure Speech SDK
import azure.cognitiveservices.speech as speechsdk

load_dotenv()  # load AZURE_KEY / AZURE_REGION from .env if present

AZURE_KEY = os.getenv("AZURE_KEY") or "<PUT_YOUR_KEY_HERE>"
AZURE_REGION = os.getenv("AZURE_REGION") or os.getenv("AZURE_LOCATION") or "<PUT_YOUR_REGION_HERE>"
# Example region: "eastus"

app = Flask(__name__, static_folder="static", template_folder="templates")


def make_speech_config():
    """Return an Azure SpeechConfig configured with subscription and region."""
    if not (AZURE_KEY and AZURE_REGION):
        raise RuntimeError("Azure key/region not configured. Set AZURE_KEY and AZURE_REGION env vars.")
    speech_config = speechsdk.SpeechConfig(subscription=AZURE_KEY, region=AZURE_REGION)
    # optional: set voice and output format
    speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"  # changeable
    return speech_config


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/tts", methods=["POST"])
def tts():
    """
    Text -> Speech.
    Expects JSON: {"text": "hello world"}
    Returns: audio/wav stream (played on client).
    """
    data = request.get_json(force=True)
    text = data.get("text", "")
    if not text:
        return jsonify({"error": "No text provided"}), 400

    speech_config = make_speech_config()

    # produce audio into temp file
    temp_wav = os.path.join(tempfile.gettempdir(), f"tts_{uuid.uuid4().hex}.wav")
    audio_config = speechsdk.audio.AudioOutputConfig(filename=temp_wav)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = synthesizer.speak_text_async(text).get()
    if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
        return send_file(temp_wav, mimetype="audio/wav", as_attachment=False)
    else:
        # get failure reason
        cancel_details = speechsdk.CancellationDetails(result)
        return jsonify({"error": "Synthesis failed", "details": str(cancel_details)}), 500


@app.route("/stt", methods=["POST"])
def stt():
    """
    Speech -> Text.
    Accepts form-data with 'file' field (audio file) OR JSON with 'language' (optional).
    Supports uploaded wav/webm/mp3 — backend converts to WAV using pydub.
    Returns recognized text.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    f = request.files["file"]
    if f.filename == "":
        return jsonify({"error": "Empty filename uploaded"}), 400

    # Save uploaded file to temp
    upload_path = os.path.join(tempfile.gettempdir(), f"upload_{uuid.uuid4().hex}_{f.filename}")
    f.save(upload_path)

    # Convert to WAV (16-bit PCM) using pydub (ffmpeg required)
    wav_path = os.path.join(tempfile.gettempdir(), f"conv_{uuid.uuid4().hex}.wav")
    try:
        audio = AudioSegment.from_file(upload_path)
        audio = audio.set_frame_rate(16000).set_channels(1).set_sample_width(2)
        audio.export(wav_path, format="wav")
    except Exception as e:
        return jsonify({"error": "Failed to convert audio", "details": str(e)}), 500

    # Use Azure Speech SDK to transcribe from WAV file
    speech_config = make_speech_config()
    audio_input = speechsdk.audio.AudioConfig(filename=wav_path)
    recognizer = speechsdk.SpeechRecognizer(speech_config=speech_config, audio_config=audio_input)

    result = recognizer.recognize_once_async().get()

    # cleanup files
    try:
        os.remove(upload_path)
    except OSError:
        pass

    try:
        os.remove(wav_path)
    except OSError:
        pass

    if result.reason == speechsdk.ResultReason.RecognizedSpeech:
        return jsonify({"text": result.text})
    elif result.reason == speechsdk.ResultReason.NoMatch:
        return jsonify({"error": "No speech could be recognized"}), 400
    else:
        cancel = speechsdk.CancellationDetails(result)
        return jsonify({"error": "Recognition failed", "details": str(cancel)}), 500


if __name__ == "__main__":
    app.run(debug=True, port=5000)
>>>>>>> 58f0309 (Initial commit - Azure Speech App)
