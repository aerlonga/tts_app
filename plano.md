# TTS Studio — Roteiro de Implementação para Claude Code

> **Contexto:** Existe um projeto Flask chamado `tts-studio` com dois arquivos: `app.py` e `index.html`.
> Este roteiro instrui o Claude Code a evoluir esse projeto em **3 fases sequenciais**.
> Execute fase por fase. Não pule etapas.
> Os modelos a serem usados serão do gemini, como já esta no app.py.

---

## Visão Geral do Projeto

**Stack atual:** Flask (Python), HTML/CSS/JS puro, SDK `google-genai`  
**Objetivo:** Transformar o studio local em uma pipeline semi-automatizada de produção de conteúdo para canal Dark do YouTube (mercado americano).  
**Princípio:** Sem over-engineering. Sem trocar a stack. Cada fase deve funcionar e ser testável antes de avançar.

**Estrutura de arquivos alvo ao final das 3 fases:**
```
tts-studio/
├── app.py              # Backend Flask (evoluído)
├── index.html          # Frontend (evoluído)
├── requirements.txt    # Dependências atualizadas
├── .env.example        # Exemplo de variáveis de ambiente
└── output/             # Pasta criada em runtime para salvar arquivos
```

---

## FASE 1 — Chunking de Áudio e Progresso em Tempo Real

**Problema a resolver:** Textos longos (2000+ palavras / ~15 min de áudio) causam timeout no Flask e no navegador. A chamada TTS é síncrona e bloqueia.

**Solução:** Dividir o roteiro em chunks por parágrafo duplo (`\n\n`), processar cada chunk individualmente na API TTS, concatenar os dados PCM brutos em memória e montar um único WAV no final. Usar Server-Sent Events (SSE) para enviar progresso ao frontend em tempo real.

---

### 1.1 — Backend: Chunking + SSE (`app.py`)

**Instrução:** Modifique a rota `/generate` existente e adicione uma nova rota `/generate-stream`.

**Regras de chunking:**
- Dividir o texto por `\n\n` (parágrafo duplo)
- Filtrar chunks vazios ou com menos de 10 caracteres
- Se um chunk tiver mais de 800 caracteres, subdividi-lo por `.` (ponto final seguido de espaço), agrupando frases até atingir ~600 caracteres por sub-chunk
- Nunca cortar no meio de uma palavra

**Implementação da rota `/generate-stream`:**

```python
# Pseudocódigo — o Claude Code deve implementar isso completamente

@app.route("/generate-stream", methods=["POST"])
def generate_stream():
    # 1. Recebe: api_key, text, voice (JSON no body)
    # 2. Chama chunk_text(text) para dividir
    # 3. Retorna uma Response com mimetype "text/event-stream"
    # 4. Para cada chunk (enumerate):
    #    a. Envia SSE: {"type": "progress", "current": i+1, "total": n, "preview": chunk[:50]}
    #    b. Chama a API TTS do Gemini para o chunk
    #    c. Acumula os bytes PCM brutos em uma lista
    #    d. Em caso de erro num chunk: envia SSE {"type": "error", "chunk": i+1, "message": str(e)}
    #       e tenta continuar com o próximo chunk (não abortar tudo)
    # 5. Concatena todos os PCM: b"".join(all_pcm_chunks)
    # 6. Converte para WAV usando wave + io.BytesIO (mesmo código do /generate atual)
    # 7. Converte o WAV para base64
    # 8. Envia SSE final: {"type": "done", "audio_b64": "...", "chunks_processed": n}
    # 9. Fecha o stream
```

**Função de chunking a implementar:**
```python
def chunk_text(text: str, max_chars: int = 600) -> list[str]:
    # Divide por \n\n, depois por frases se necessário
    # Retorna lista de strings, cada uma com no máximo max_chars
    # Nenhum chunk pode ser vazio
```

**Rota `/generate` original:** Manter funcionando como fallback para textos curtos (< 500 chars). Não apagar.

**Imports necessários a adicionar:**
```python
import base64
import json
import time
```

---

### 1.2 — Frontend: Barra de Progresso e Consumo de SSE (`index.html`)

**Instrução:** Adicionar os seguintes elementos visuais e a lógica JS para consumir o stream SSE.

**Novo elemento HTML** — inserir entre o botão `#generateBtn` e o `div.status`:
```html
<!-- Progress bar — hidden by default -->
<div id="progressWrap" style="display:none; margin-top: 16px;">
  <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
    <span id="progressLabel" style="font-size:12px; font-family:var(--mono); color:var(--muted);">
      Processando chunk 0/0...
    </span>
    <span id="progressPct" style="font-size:12px; font-family:var(--mono); color:var(--accent);">0%</span>
  </div>
  <div style="background:var(--surface2); border-radius:4px; height:6px; overflow:hidden;">
    <div id="progressBar" style="height:100%; width:0%; background:var(--accent); 
         border-radius:4px; transition:width 0.3s ease;"></div>
  </div>
  <div id="progressPreview" style="margin-top:8px; font-size:11px; font-family:var(--mono); 
       color:var(--muted); white-space:nowrap; overflow:hidden; text-overflow:ellipsis;"></div>
</div>
```

**Lógica JS a implementar** — substituir a lógica do `Step 2 - generate TTS` dentro da função `generate()`:

```javascript
// Pseudocódigo — implementar completamente

async function generateWithStream(apiKey, text, voice) {
  // 1. Mostrar progressWrap, resetar barra para 0%
  // 2. Fazer POST para /generate-stream com fetch + ReadableStream
  // 3. Ler o stream linha a linha (TextDecoder + getReader())
  // 4. Parsear cada linha como JSON (ignorar linhas vazias e que começam com "data: " prefix se houver)
  // 5. Para evento "progress":
  //    - Atualizar progressLabel: "Processando chunk {current}/{total}..."
  //    - Atualizar progressBar width: (current/total * 100) + "%"
  //    - Atualizar progressPct: Math.round(current/total*100) + "%"
  //    - Atualizar progressPreview: event.preview
  // 6. Para evento "error":
  //    - Mostrar aviso não-bloqueante (amarelo/warning) mas continuar
  // 7. Para evento "done":
  //    - Converter audio_b64 de volta para Blob (audio/wav)
  //    - Criar object URL e setar no audioPlayer
  //    - Esconder progressWrap
  //    - Mostrar audioCard
}
```

**Observação:** O SSE aqui é implementado via fetch + ReadableStream (não via `EventSource`), porque o payload inicial é POST com JSON. O formato de cada mensagem SSE deve ser `data: {json}\n\n`.

---

### 1.3 — Teste da Fase 1

Após implementar, verificar manualmente:
- [ ] Texto curto (< 500 chars): rota `/generate` original ainda funciona
- [ ] Texto longo (o exemplo do roteiro GOINFRA no HTML): barra de progresso aparece e avança
- [ ] Ao final, áudio é gerado e player aparece
- [ ] Sem crash/timeout

---

## FASE 2 — Módulo de Roteirização a partir de URL

**Problema a resolver:** O usuário precisa copiar texto manualmente para o textarea. Queremos aceitar uma URL e gerar um roteiro dramatizado automaticamente.

**Solução:** Nova rota `/scriptify` que recebe uma URL, extrai o texto limpo com `newspaper3k`, envia para Gemini com um system prompt de roteirização, e retorna o roteiro + array de prompts de imagem.

---

### 2.1 — Dependências

Adicionar ao `requirements.txt`:
```
newspaper3k==0.2.8
lxml[html_clean]
```

**Nota:** `newspaper3k` depende de `lxml` e `nltk`. O Claude Code deve adicionar no topo do `app.py`, logo após os imports existentes:
```python
import nltk
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)
```

---

### 2.2 — System Prompt de Roteirização

Adicionar esta constante no `app.py` junto com o `ENHANCE_SYSTEM_PROMPT` existente:

```python
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
```

---

### 2.3 — Rota `/scriptify` (`app.py`)

```python
@app.route("/scriptify", methods=["POST"])
def scriptify():
    # 1. Recebe: api_key (str), url (str)
    # 2. Valida que url começa com http
    # 3. Usa newspaper3k para baixar e parsear o artigo:
    #    from newspaper import Article
    #    article = Article(url)
    #    article.download()
    #    article.parse()
    #    raw_text = article.text
    # 4. Se raw_text tiver menos de 200 chars, retorna erro 400: "Não foi possível extrair conteúdo da URL."
    # 5. Chama Gemini (gemini-2.5-flash, temperature=0.7) com SCRIPTIFY_SYSTEM_PROMPT + raw_text
    # 6. Separa o response.text pelo marcador "===IMAGE_PROMPTS==="
    #    script_part = antes do marcador
    #    image_part = depois do marcador (parsear como JSON)
    # 7. Se o JSON de imagens falhar o parse, retorna image_prompts como lista vazia (não abortar)
    # 8. Retorna JSON: {"script": script_part, "image_prompts": [...], "source_chars": len(raw_text)}
    # 9. Trata exceções: retorna {"error": str(e)} com status 500
```

---

### 2.4 — Frontend: Painel de URL (`index.html`)

**Instrução:** Adicionar um novo card **acima** do card de configuração existente (ou como primeira seção do card de configuração — escolher o que ficar mais limpo visualmente).

```html
<!-- URL Scriptifier Card — inserir antes do card de Configuração -->
<div class="card" id="scriptifierCard">
  <div class="card-header">
    <span class="dot" style="background:var(--yellow)"></span>
    Roteirizar a partir de URL
  </div>
  <div class="card-body">
    <label>URL do artigo (Wikipedia, blog, notícia)</label>
    <div style="display:flex; gap:10px; margin-bottom:12px;">
      <input type="text" id="sourceUrl" placeholder="https://en.wikipedia.org/wiki/..." 
             style="flex:1; margin-bottom:0;">
      <button class="btn" id="scriptifyBtn" onclick="scriptify()" 
              style="width:auto; padding:12px 20px; white-space:nowrap;">
        ✨ Roteirizar
      </button>
    </div>
    <div class="status" id="scriptifyStatus"></div>
    
    <!-- Image prompts result — hidden until generated -->
    <div id="imagePromptsWrap" style="display:none; margin-top:16px;">
      <label>Prompts de Imagem Gerados (copie para o Gemini Web)</label>
      <div id="imagePromptsList" style="background:var(--surface2); border-radius:8px; 
           padding:14px; font-size:12px; font-family:var(--mono); line-height:2; 
           max-height:200px; overflow-y:auto; color:var(--muted);"></div>
      <button onclick="copyPrompts()" style="margin-top:8px; background:transparent; 
              border:1px solid var(--yellow); color:var(--yellow); border-radius:6px; 
              padding:8px 16px; font-family:var(--mono); font-size:12px; cursor:pointer;">
        📋 Copiar todos os prompts
      </button>
    </div>
  </div>
</div>
```

**Funções JS a implementar:**

```javascript
let generatedImagePrompts = [];

async function scriptify() {
  // 1. Pega apiKey e sourceUrl
  // 2. Valida que ambos existem
  // 3. Mostra status "Extraindo e roteirizando... (pode levar 30-60s)"
  // 4. Desabilita botão scriptifyBtn
  // 5. POST para /scriptify com {api_key, url}
  // 6. Se sucesso:
  //    a. Coloca script no textarea #textInput
  //    b. Atualiza charCount
  //    c. Salva imagePrompts em generatedImagePrompts
  //    d. Renderiza imagePromptsList: cada prompt em uma linha numerada
  //    e. Mostra imagePromptsWrap
  //    f. Status verde: "Roteiro gerado! {n} chars. Role para baixo e gere o áudio."
  // 7. Se erro: status vermelho com a mensagem
  // 8. Reabilita botão
}

function copyPrompts() {
  // Junta generatedImagePrompts com \n e copia para clipboard
  // Feedback visual no botão: "✓ Copiado!" por 2 segundos
}
```

---

### 2.5 — Teste da Fase 2

- [ ] URL de artigo da Wikipedia em inglês: roteiro gerado em inglês com ~2000 palavras
- [ ] URL de artigo em português: roteiro gerado em inglês (tradução automática pelo prompt)
- [ ] URL inválida ou sem conteúdo: mensagem de erro clara
- [ ] Após gerar roteiro: textarea preenchido, prompts de imagem visíveis e copiáveis
- [ ] Fluxo completo: URL → Roteiro → Enhance → TTS → WAV

---

## FASE 3 — Montagem de Vídeo com FFmpeg

**Problema a resolver:** Após gerar o áudio e as imagens (geradas manualmente no Gemini Web), o usuário precisa montar o vídeo. Queremos automatizar isso dentro do próprio sistema.

**Solução:** Nova rota `/assemble` que recebe o arquivo WAV + arquivos de imagem via multipart form, usa FFmpeg via subprocess para montar um MP4 com transições, e retorna o vídeo para download.

**Pré-requisito:** FFmpeg deve estar instalado no sistema. O Claude Code deve verificar isso no startup do app e printar um warning se não estiver disponível.

---

### 3.1 — Verificação de FFmpeg no Startup (`app.py`)

Adicionar logo após os imports:
```python
import subprocess
import shutil
import tempfile
import uuid

def check_ffmpeg():
    if shutil.which("ffmpeg") is None:
        print("[WARN] FFmpeg não encontrado. A Fase 3 (montagem de vídeo) não estará disponível.")
        return False
    return True

FFMPEG_AVAILABLE = check_ffmpeg()
```

---

### 3.2 — Lógica de Montagem FFmpeg (`app.py`)

```python
def assemble_video(audio_path: str, image_paths: list[str], output_path: str) -> bool:
    """
    Monta um vídeo MP4 a partir de um WAV e uma lista de imagens.
    
    Estratégia:
    1. Pegar a duração total do áudio com ffprobe
    2. Dividir a duração igualmente entre as imagens (duration_per_image = total / n_images)
    3. Montar um slideshow: cada imagem aparece por duration_per_image segundos
    4. Aplicar fade in/out de 0.5s entre as imagens (filter_complex com xfade)
    5. Combinar o slideshow com o áudio
    6. Output: MP4 H.264, AAC audio, resolução 1920x1080, qualidade CRF 23
    
    Comando FFmpeg para slideshow com crossfade:
    - Usar o filter_complex com concat e xfade para transições suaves
    - Se n_images <= 1: simples loop da imagem pela duração do áudio
    
    Retorna True se sucesso, False se falhar.
    Qualquer exceção deve ser capturada e logada, retornando False.
    """
```

---

### 3.3 — Rota `/assemble` (`app.py`)

```python
@app.route("/assemble", methods=["POST"])
def assemble():
    # 1. Verificar FFMPEG_AVAILABLE — se False, retornar 503 com mensagem clara
    # 2. Receber via multipart/form-data:
    #    - audio: arquivo WAV (obrigatório)
    #    - images: múltiplos arquivos de imagem (mínimo 1, máximo 20)
    # 3. Validações:
    #    - audio deve ter mimetype audio/* ou nome terminando em .wav
    #    - images devem ser image/jpeg ou image/png
    #    - Máximo 20 imagens
    # 4. Criar um diretório temporário com tempfile.mkdtemp()
    # 5. Salvar o WAV e as imagens no diretório temp
    # 6. Chamar assemble_video(audio_path, image_paths, output_path)
    # 7. Se sucesso: retornar o MP4 com send_file, download_name="video.mp4"
    # 8. Se falha: retornar erro 500
    # 9. Limpar o diretório temporário em um bloco finally (shutil.rmtree)
    # 10. Usar uuid4 para nomear os arquivos temporários e evitar conflitos
```

---

### 3.4 — Frontend: Painel de Montagem de Vídeo (`index.html`)

**Instrução:** Adicionar um novo card **após** o card de audio gerado (`#audioCard`), visível apenas quando o áudio foi gerado.

```html
<!-- Video Assembly Card — aparece depois que o áudio é gerado -->
<div class="card" id="assemblyCard" style="display:none;">
  <div class="card-header">
    <span class="dot" style="background:var(--yellow)"></span>
    Montar Vídeo (FFmpeg)
  </div>
  <div class="card-body">
    <p style="font-size:13px; color:var(--muted); font-family:var(--mono); 
              margin-bottom:16px; line-height:1.6;">
      Faça upload das imagens geradas (mín. 1, máx. 20). O sistema vai distribuí-las 
      igualmente pela duração do áudio com transições de fade.
    </p>
    
    <label>Imagens (JPG ou PNG, em ordem)</label>
    <input type="file" id="imageFiles" accept="image/jpeg,image/png" multiple
           style="width:100%; background:var(--surface2); border:1px solid var(--border); 
                  border-radius:8px; padding:12px; color:var(--text); 
                  font-family:var(--mono); font-size:13px; margin-bottom:16px; cursor:pointer;">
    
    <div id="imagePreviewList" style="display:flex; flex-wrap:wrap; gap:8px; 
         margin-bottom:16px;"></div>
    
    <button class="btn" id="assembleBtn" onclick="assembleVideo()" style="background:var(--yellow); color:#000;">
      🎬 Montar Vídeo
      <div class="spinner" id="assembleSpinner" style="border-top-color:#000;"></div>
    </button>
    
    <div class="status" id="assemblyStatus"></div>
    
    <!-- Download de vídeo — hidden until ready -->
    <div id="videoResult" style="display:none; margin-top:16px;">
      <a id="videoDownloadLink" class="download-btn" 
         style="border-color:var(--yellow); color:var(--yellow);" download="video.mp4">
        ⬇ Baixar MP4
      </a>
    </div>
  </div>
</div>
```

**Funções JS a implementar:**

```javascript
let currentAudioBlob = null; // Guardar o blob do áudio gerado

// Modificar a função generate() para salvar o blob:
// Após criar o blob do áudio, adicionar: currentAudioBlob = blob;
// E mostrar o assemblyCard: document.getElementById('assemblyCard').style.display = 'block';

// Preview de imagens ao selecionar
document.getElementById('imageFiles').addEventListener('change', function() {
  // Mostrar thumbnails das imagens selecionadas em imagePreviewList
  // Cada thumbnail: 60x60px, object-fit cover, border-radius 4px
  // Mostrar contador: "X imagens selecionadas"
});

async function assembleVideo() {
  // 1. Verificar que currentAudioBlob existe e imageFiles tem arquivos
  // 2. Montar FormData: append audio (currentAudioBlob, "audio.wav") e cada imagem
  // 3. POST para /assemble
  // 4. Se sucesso: criar URL do MP4, setar em videoDownloadLink, mostrar videoResult
  // 5. Se erro: mostrar assemblyStatus com mensagem vermelha
  // 6. Loading state no assembleBtn durante o processo
}
```

---

### 3.5 — Teste da Fase 3

- [ ] Sem FFmpeg: card de montagem mostra mensagem de erro ao tentar montar
- [ ] 1 imagem + áudio curto: vídeo gerado com a imagem estática pela duração total
- [ ] 5 imagens + áudio: cada imagem aparece por duração_total/5 segundos com fade entre elas
- [ ] 15 imagens (caso de uso real): vídeo de ~15 min gerado corretamente
- [ ] Download do MP4 funcionando

---

## Requisitos Gerais (Aplicar em Todas as Fases)

### `requirements.txt` final:
```
flask>=3.0.0
google-genai>=1.0.0
newspaper3k==0.2.8
lxml[html_clean]
nltk
```

### `.env.example`:
```
# Copie este arquivo para .env e preencha
GEMINI_API_KEY=AIza...
FLASK_PORT=5000
FLASK_DEBUG=false
```

### Tratamento de erros (padrão para todas as rotas):
- Sempre retornar JSON com chave `"error"` em casos de falha
- Nunca expor stack traces completos no response (logar no servidor, retornar mensagem amigável)
- Status HTTP corretos: 400 (input inválido), 500 (erro interno), 503 (serviço indisponível)

### Preservar o que já existe:
- O `ENHANCE_SYSTEM_PROMPT` e a rota `/enhance` não devem ser modificados
- A rota `/generate` original deve continuar funcionando
- O design visual (CSS variables, fontes IBM Plex) deve ser preservado
- Todos os textos da UI podem permanecer em português

---

## Ordem de Execução para o Claude Code

```
1. Ler os arquivos existentes: app.py e index.html
2. Implementar Fase 1 completamente
3. Testar Fase 1 (checar se não quebrou nada)
4. Implementar Fase 2
5. Testar Fase 2
6. Implementar Fase 3
7. Testar Fase 3
8. Gerar requirements.txt e .env.example
9. Confirmar que todos os testes passaram
```

**Ao final, o Claude Code deve printar um resumo** de todas as rotas disponíveis:
```
[TTS Studio] Rotas disponíveis:
  GET  /                → Interface principal
  POST /enhance         → Entonação inteligente (existente)
  POST /generate        → TTS curto, retorna WAV (existente)
  POST /generate-stream → TTS longo com chunking + SSE de progresso (NOVO)
  POST /scriptify       → Roteirizar URL → Script + Image Prompts (NOVO)
  POST /assemble        → Montar MP4 com imagens + áudio via FFmpeg (NOVO)
```