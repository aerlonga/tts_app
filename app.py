from flask import Flask, request, jsonify, send_file, render_template_string
from google import genai
from google.genai import types
import wave, io, os

app = Flask(__name__)

HTML = open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8").read()

ENHANCE_SYSTEM_PROMPT = """Voce e um diretor de locucao profissional.
Sua tarefa e receber um roteiro em texto puro e reescrevê-lo com marcacoes de entonacao naturais em linguagem natural,
inseridas INLINE dentro do texto, entre parenteses.

Regras:
- Use marcacoes como: (com entusiasmo), (pausa curta), (pausa longa), (enfatizando), (tom calmo), (tom serio),
  (com curiosidade), (acelerando levemente), (desacelerando), (com energia), (suavemente), etc.
- Coloque a marcacao imediatamente ANTES da frase ou palavra que deve receber aquela entonacao.
- Nao invente conteudo, nao altere o texto original alem das marcacoes.
- Nao adicione comentarios, explicacoes ou blocos de codigo. Retorne apenas o roteiro anotado.
- Mantenha timestamps e estrutura do roteiro intactos.
"""

@app.route("/")
def index():
    return render_template_string(HTML)


@app.route("/enhance", methods=["POST"])
def enhance():
    """Step 1: use a text model to annotate the script with intonation cues."""
    data = request.json
    api_key = data.get("api_key", "").strip()
    text = data.get("text", "").strip()

    if not api_key:
        return jsonify({"error": "API Key do Gemini e obrigatoria."}), 400
    if not text:
        return jsonify({"error": "Texto nao pode estar vazio."}), 400

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            # model="gemini-3-flash-preview",
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=ENHANCE_SYSTEM_PROMPT,
                temperature=0.4,
            ),
        )
        enhanced = response.text.strip()
        return jsonify({"enhanced_text": enhanced})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate():
    data = request.json
    api_key = data.get("api_key", "").strip()
    text = data.get("text", "").strip()
    voice = data.get("voice", "Charon")

    if not api_key:
        return jsonify({"error": "API Key do Gemini e obrigatoria."}), 400
    if not text:
        return jsonify({"error": "Texto nao pode estar vazio."}), 400

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            # model="gemini-2.5-flash-preview-tts",
            # model="gemini-3.1-flash-tts-preview",
            model="gemini-2.5-pro-preview-tts",
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
    print("\n[TTS] TTS rodando em: http://localhost:5000\n")
    app.run(debug=False, port=5000)
