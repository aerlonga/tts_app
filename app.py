from flask import Flask, request, jsonify, send_file, render_template_string, Response, stream_with_context
from google import genai
from google.genai import types
import wave, io, os
import base64
import json
import time
import subprocess
import shutil
import tempfile
import uuid

import nltk
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

app = Flask(__name__)

HTML = open(os.path.join(os.path.dirname(__file__), "index.html"), encoding="utf-8").read()

# ─── FFmpeg check ───────────────────────────────────────────────────────────

def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("[WARN] FFmpeg não encontrado. A Fase 3 (montagem de vídeo) não estará disponível.")
        return False
    return True

FFMPEG_AVAILABLE = check_ffmpeg()

# ─── System Prompts ──────────────────────────────────────────────────────────

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

SCRIPTIFY_SYSTEM_PROMPT = """You are a professional scriptwriter for an American YouTube channel focused on military history, dark historical events, and geopolitical conflicts, targeting American veterans and history enthusiasts aged 35-65.

Your task: transform raw input text into a dramatic, engaging video script.

SCRIPT RULES:
1. Write ONLY in English, regardless of input language.
2. Minimum 2000 words. Aim for 2500 words (approximately 15 minutes of narration).
3. Use long, flowing paragraphs — NO bullet points, NO lists, NO headers inside the script body.
4. Open with a powerful hook: a dramatic scene, shocking statistic, or provocative question.
5. Maintain a tone of gravitas, patriotism, and historical curiosity throughout.
6. Use active voice. Avoid passive constructions.
7. Add dramatic pauses naturally by ending paragraphs with short, punchy sentences.
8. DO NOT invent facts. Dramatize what is in the source material, but stay truthful.
9. Use timestamps every ~30 seconds in the format [MM:SS - Section Name] to help with video editing.

IMAGE PROMPTS RULES (append AFTER the script):
- Generate exactly 15 image prompts in English.
- Style: dramatic black and white photorealistic photography, 16:9 aspect ratio, cinematic lighting.
- Each prompt should describe a specific scene from the script.
- Format as a JSON array at the very end, after the marker: ===IMAGE_PROMPTS===

OUTPUT FORMAT:
[Full script text with timestamps]

===IMAGE_PROMPTS===
["prompt 1", "prompt 2", ..., "prompt 15"]
"""

# ─── Chunking ─────────────────────────────────────────────────────────────────

def chunk_text(text: str, max_chars: int = 600) -> list[str]:
    """Divide o texto em chunks adequados para a API TTS."""
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip()]
    chunks = []

    for para in paragraphs:
        if len(para) < 10:
            continue
        if len(para) <= max_chars:
            chunks.append(para)
        else:
            # Subdivide por frases (ponto final seguido de espaço)
            sentences = []
            for part in para.split('. '):
                part = part.strip()
                if part:
                    sentences.append(part if part.endswith('.') else part + '.')

            current = ''
            for sentence in sentences:
                if len(current) + len(sentence) + 1 <= max_chars:
                    current = (current + ' ' + sentence).strip()
                else:
                    if current:
                        chunks.append(current)
                    # Se a frase em si é maior que max_chars, cortamos por palavras
                    if len(sentence) > max_chars:
                        words = sentence.split()
                        sub = ''
                        for word in words:
                            if len(sub) + len(word) + 1 <= max_chars:
                                sub = (sub + ' ' + word).strip()
                            else:
                                if sub:
                                    chunks.append(sub)
                                sub = word
                        if sub:
                            current = sub
                        else:
                            current = ''
                    else:
                        current = sentence
            if current:
                chunks.append(current)

    return [c for c in chunks if c.strip()]

# ─── FFmpeg video assembly ────────────────────────────────────────────────────

def assemble_video(audio_path: str, image_paths: list[str], output_path: str) -> bool:
    """
    Monta um vídeo MP4 a partir de um WAV e uma lista de imagens.

    Estratégia:
    1. Pegar a duração total do áudio com ffprobe
    2. Dividir a duração igualmente entre as imagens
    3. Montar slideshow com crossfade entre imagens
    4. Combinar com áudio
    5. Output: MP4 H.264, AAC audio, 1920x1080, CRF 23
    """
    try:
        # 1. Obter duração do áudio
        probe_result = subprocess.run(
            ['ffprobe', '-v', 'quiet', '-print_format', 'json', '-show_format', audio_path],
            capture_output=True, text=True, timeout=30
        )
        probe_data = json.loads(probe_result.stdout)
        total_duration = float(probe_data['format']['duration'])

        n = len(image_paths)
        duration_per_image = total_duration / n
        fade_duration = min(0.5, duration_per_image * 0.2)  # máx 20% da duração por imagem

        if n == 1:
            # Caso simples: uma imagem estática
            cmd = [
                'ffmpeg', '-y',
                '-loop', '1', '-i', image_paths[0],
                '-i', audio_path,
                '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
                '-vf', 'scale=1920:1080:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:(oh-ih)/2',
                '-c:a', 'aac', '-b:a', '192k',
                '-shortest', '-pix_fmt', 'yuv420p',
                output_path
            ]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if result.returncode != 0:
                print(f"[ERROR] FFmpeg single image: {result.stderr}")
                return False
            return True

        # Caso múltiplas imagens: slideshow com xfade
        # Construir filter_complex
        inputs = []
        for img in image_paths:
            inputs.extend(['-loop', '1', '-t', str(duration_per_image + fade_duration), '-i', img])

        # Scale cada input para 1920x1080
        filter_parts = []
        for i in range(n):
            filter_parts.append(
                f'[{i}:v]scale=1920:1080:force_original_aspect_ratio=decrease,'
                f'pad=1920:1080:(ow-iw)/2:(oh-ih)/2,setsar=1[v{i}]'
            )

        # Encadear xfade
        xfade_chain = '[v0]'
        for i in range(1, n):
            offset = duration_per_image * i - fade_duration * (i - 1) - fade_duration
            offset = max(0.1, offset)
            xfade_chain += f'[v{i}]xfade=transition=fade:duration={fade_duration:.2f}:offset={offset:.2f}'
            if i < n - 1:
                xfade_chain += f'[xf{i}];[xf{i}]'
        xfade_chain += '[vout]'

        filter_complex = ';'.join(filter_parts) + ';' + xfade_chain

        cmd = (
            ['ffmpeg', '-y'] +
            inputs +
            ['-i', audio_path,
             '-filter_complex', filter_complex,
             '-map', '[vout]',
             '-map', f'{n}:a',
             '-c:v', 'libx264', '-crf', '23', '-preset', 'fast',
             '-c:a', 'aac', '-b:a', '192k',
             '-pix_fmt', 'yuv420p',
             '-shortest',
             output_path]
        )

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"[ERROR] FFmpeg slideshow: {result.stderr}")
            return False
        return True

    except Exception as e:
        print(f"[ERROR] assemble_video: {e}")
        return False

# ─── Routes ───────────────────────────────────────────────────────────────────

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
            contents=text,
            config=types.GenerateContentConfig(
                system_instruction=ENHANCE_SYSTEM_PROMPT,
                temperature=0.4,
            ),
        )
        enhanced = response.text.strip()
        return jsonify({"enhanced_text": enhanced})
    except Exception as e:
        print(f"[ERROR] /enhance: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/generate", methods=["POST"])
def generate():
    """Fallback para textos curtos — retorna WAV direto."""
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

        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(audio_data)
        buf.seek(0)

        return send_file(buf, mimetype="audio/wav", as_attachment=False, download_name="audio.wav")

    except Exception as e:
        print(f"[ERROR] /generate: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/generate-stream", methods=["POST"])
def generate_stream():
    """TTS com chunking e progresso via SSE."""
    data = request.json
    api_key = data.get("api_key", "").strip()
    text = data.get("text", "").strip()
    voice = data.get("voice", "Charon")

    if not api_key:
        return jsonify({"error": "API Key do Gemini e obrigatoria."}), 400
    if not text:
        return jsonify({"error": "Texto nao pode estar vazio."}), 400

    def event_stream():
        chunks = chunk_text(text)
        n = len(chunks)
        all_pcm = []
        client = genai.Client(api_key=api_key)

        for i, chunk in enumerate(chunks):
            # Envia progresso
            progress_event = json.dumps({
                "type": "progress",
                "current": i + 1,
                "total": n,
                "preview": chunk[:80]
            })
            yield f"data: {progress_event}\n\n"

            try:
                response = client.models.generate_content(
                    model="gemini-2.5-flash-preview-tts",
                    contents=chunk,
                    config=types.GenerateContentConfig(
                        response_modalities=["AUDIO"],
                        speech_config=types.SpeechConfig(
                            voice_config=types.VoiceConfig(
                                prebuilt_voice_config=types.PrebuiltVoiceConfig(voice_name=voice)
                            )
                        ),
                    ),
                )
                pcm_data = response.candidates[0].content.parts[0].inline_data.data
                all_pcm.append(pcm_data)
            except Exception as e:
                error_event = json.dumps({
                    "type": "error",
                    "chunk": i + 1,
                    "message": str(e)
                })
                yield f"data: {error_event}\n\n"
                print(f"[WARN] Chunk {i+1} falhou: {e}")
                continue

        if not all_pcm:
            error_event = json.dumps({"type": "error", "chunk": 0, "message": "Nenhum chunk processado com sucesso."})
            yield f"data: {error_event}\n\n"
            return

        # Concatena PCM e converte para WAV
        combined_pcm = b"".join(all_pcm)
        buf = io.BytesIO()
        with wave.open(buf, "wb") as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(24000)
            wf.writeframes(combined_pcm)
        buf.seek(0)
        wav_bytes = buf.read()
        audio_b64 = base64.b64encode(wav_bytes).decode("utf-8")

        done_event = json.dumps({
            "type": "done",
            "audio_b64": audio_b64,
            "chunks_processed": len(all_pcm)
        })
        yield f"data: {done_event}\n\n"

    return Response(
        stream_with_context(event_stream()),
        mimetype="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )


@app.route("/scriptify", methods=["POST"])
def scriptify():
    """Roteiriza um artigo a partir de uma URL usando newspaper3k + Gemini."""
    data = request.json
    api_key = data.get("api_key", "").strip()
    url = data.get("url", "").strip()

    if not api_key:
        return jsonify({"error": "API Key do Gemini é obrigatória."}), 400
    if not url or not url.startswith("http"):
        return jsonify({"error": "URL inválida. Deve começar com http(s)://"}), 400

    try:
        from newspaper import Article
        article = Article(url)
        article.download()
        article.parse()
        raw_text = article.text

        if len(raw_text) < 200:
            return jsonify({"error": "Não foi possível extrair conteúdo da URL. Tente outra URL."}), 400

        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=raw_text,
            config=types.GenerateContentConfig(
                system_instruction=SCRIPTIFY_SYSTEM_PROMPT,
                temperature=0.7,
            ),
        )

        full_response = response.text.strip()

        # Separar script dos image prompts
        if "===IMAGE_PROMPTS===" in full_response:
            parts = full_response.split("===IMAGE_PROMPTS===", 1)
            script_part = parts[0].strip()
            image_raw = parts[1].strip()
            try:
                # Tenta extrair o array JSON
                start = image_raw.find('[')
                end = image_raw.rfind(']') + 1
                if start != -1 and end > start:
                    image_prompts = json.loads(image_raw[start:end])
                else:
                    image_prompts = []
            except Exception:
                image_prompts = []
        else:
            script_part = full_response
            image_prompts = []

        return jsonify({
            "script": script_part,
            "image_prompts": image_prompts,
            "source_chars": len(raw_text)
        })

    except Exception as e:
        print(f"[ERROR] /scriptify: {e}")
        return jsonify({"error": str(e)}), 500


@app.route("/assemble", methods=["POST"])
def assemble():
    """Monta um MP4 a partir de WAV + imagens via FFmpeg."""
    if not FFMPEG_AVAILABLE:
        return jsonify({"error": "FFmpeg não está instalado no servidor. Instale FFmpeg para usar esta funcionalidade."}), 503

    audio_file = request.files.get("audio")
    image_files = request.files.getlist("images")

    if not audio_file:
        return jsonify({"error": "Arquivo de áudio (WAV) é obrigatório."}), 400
    if not image_files:
        return jsonify({"error": "Pelo menos 1 imagem é obrigatória."}), 400
    if len(image_files) > 20:
        return jsonify({"error": "Máximo de 20 imagens permitidas."}), 400

    # Validar mimetype do áudio
    audio_mime = audio_file.mimetype or ""
    audio_name = audio_file.filename or ""
    if not (audio_mime.startswith("audio/") or audio_name.lower().endswith(".wav")):
        return jsonify({"error": "O arquivo de áudio deve ser um WAV."}), 400

    # Validar imagens
    for img in image_files:
        if img.mimetype not in ("image/jpeg", "image/png"):
            return jsonify({"error": f"Imagem inválida: {img.filename}. Apenas JPG e PNG são aceitos."}), 400

    tmp_dir = tempfile.mkdtemp()
    try:
        # Salvar áudio
        audio_id = uuid.uuid4().hex
        audio_path = os.path.join(tmp_dir, f"audio_{audio_id}.wav")
        audio_file.save(audio_path)

        # Salvar imagens em ordem
        image_paths = []
        for i, img in enumerate(image_files):
            ext = ".jpg" if img.mimetype == "image/jpeg" else ".png"
            img_path = os.path.join(tmp_dir, f"img_{i:04d}_{uuid.uuid4().hex}{ext}")
            img.save(img_path)
            image_paths.append(img_path)

        # Output
        output_path = os.path.join(tmp_dir, f"video_{uuid.uuid4().hex}.mp4")

        success = assemble_video(audio_path, image_paths, output_path)

        if not success or not os.path.exists(output_path):
            return jsonify({"error": "Falha ao montar o vídeo. Verifique os arquivos enviados."}), 500

        return send_file(
            output_path,
            mimetype="video/mp4",
            as_attachment=True,
            download_name="video.mp4"
        )

    except Exception as e:
        print(f"[ERROR] /assemble: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        try:
            shutil.rmtree(tmp_dir)
        except Exception:
            pass


if __name__ == "__main__":
    print("\n[TTS Studio] Rotas disponíveis:")
    print("  GET  /               → Interface principal")
    print("  POST /enhance        → Entonação inteligente (existente)")
    print("  POST /generate       → TTS curto, retorna WAV (existente)")
    print("  POST /generate-stream → TTS longo com chunking + SSE de progresso (NOVO)")
    print("  POST /scriptify      → Roteirizar URL → Script + Image Prompts (NOVO)")
    print("  POST /assemble       → Montar MP4 com imagens + áudio via FFmpeg (NOVO)")
    print()
    app.run(debug=False, port=5000)
