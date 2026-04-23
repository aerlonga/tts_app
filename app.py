from flask import Flask, request, jsonify, send_file, render_template_string
from google import genai
from google.genai import types
import wave, struct, io, os, tempfile

app = Flask(__name__)

HTML = open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8").read()

@app.route("/")
def index():
    return render_template_string(HTML)

@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    api_key = data.get("api_key", "AIzaSyBO8nxpt9l3fDn0ywblqYQtjyg720IkXrM").strip()
    text = data.get("text", "").strip()
    voice = data.get("voice", "Charon")

    if not api_key:
        return jsonify({"error": "API Key do Gemini é obrigatória."}), 400
    if not text:
        return jsonify({"error": "Texto não pode estar vazio."}), 400

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash-preview-tts",
            contents=text,
            config=types.GenerateContentConfig(
                response_modalities=["AUDIO"],
                speech_config=types.SpeechConfig(
                    voice_config=types.VoiceConfig(
                        prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                    )
                ),
            ),
        )

        audio_data = response.candidates[0].content.parts[0].inline_data.data

        # Convert raw PCM to WAV
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)
        buf.seek(0)

        return send_file(buf, mimetype="audio/wav", as_attachment=False, download_name="audio.wav")

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    print("\n[TTS] GOINFRA TTS rodando em: http://localhost:5000\n")
    app.run(debug=False, port=5000)
