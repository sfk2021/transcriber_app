
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
