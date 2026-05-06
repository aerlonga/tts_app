# 🎙️ TTS Studio

Gerador de áudio local usando **Gemini 2.5 Flash TTS** da Google. Evoluído para uma pipeline semi-automatizada de produção de conteúdo (roteirização, narração e montagem de vídeos).

---

## 📦 Requisitos e Instalação (Primeira Vez)

Para usar todas as funcionalidades (incluindo montagem de vídeo), você precisa do Python 3.9+ e do FFmpeg instalados no sistema.

### 1. Instalar dependências do sistema
No Ubuntu/Debian, instale o FFmpeg (necessário para a montagem de vídeos):
```bash
sudo apt update
sudo apt install ffmpeg
```

### 2. Instalar dependências do Python
Recomendado usar um ambiente virtual (venv). Instale os pacotes listados no `requirements.txt`:
```bash
pip install -r requirements.txt
```

*(Caso não use o requirements.txt, você pode rodar: `pip install flask google-genai newspaper3k "lxml[html_clean]" nltk`)*

### 3. Configuração de Variáveis (Opcional)
Renomeie o `.env.example` para `.env` e configure sua API Key.
Uma **Gemini API Key** pode ser obtida em → https://aistudio.google.com/app/apikey

---

## 🚀 Como usar

### Iniciar o servidor
```bash
python app.py
```
Abra no navegador: `http://localhost:5000`

---

## ✨ Funcionalidades (Novidades)

### Fase 1 — Chunking + Progresso em Tempo Real
- **Textos longos sem timeout**: O sistema divide automaticamente textos longos (por parágrafos ou frases) e processa os pedaços individualmente em formato de stream (`/generate-stream`).
- **Barra de progresso**: Acompanhe o progresso da geração de áudio em tempo real na interface (aparece automaticamente para textos ≥ 500 caracteres).
- **Fallback**: Textos curtos (< 500 caracteres) ainda usam a rota original `/generate`.

### Fase 2 — Roteirização por URL
- **Roteiro automático**: Insira a URL de um artigo (Wikipedia, blog, notícia).
- **Extração inteligente**: O sistema extrai o conteúdo (usando `newspaper3k`) e envia para o Gemini criar um roteiro em inglês no estilo de canal "Dark".
- **Prompts de Imagem**: Gera automaticamente 15 prompts fotográficos em JSON na mesma requisição, que são exibidos com um botão de "Copiar Todos" na interface.

### Fase 3 — Montagem de Vídeo (FFmpeg)
- **Criação de MP4 via FFmpeg**: Após gerar o áudio, o card "Montar Vídeo" ficará disponível.
- **Slideshow animado**: Faça o upload das imagens geradas (de 1 a 20). O sistema calcula a duração do áudio (`ffprobe`), distribui as imagens igualmente e aplica efeito de fade cruzado (`xfade`).
- **Tratamento gracioso de erros**: Retorna erro claro (503) caso o FFmpeg não esteja no servidor. O MP4 resultante é servido imediatamente para download pelo navegador.

---

## 🎤 Geração Manual de Áudio

1. Cole sua **Gemini API Key** no campo indicado (ou no `.env`).
2. Escolha a **voz** desejada.
3. Cole ou edite o **texto/roteiro**.
4. (Opcional) Ative a **Entonação inteligente** para o Gemini adicionar marcações de voz.
5. Clique em **Gerar Áudio**.
6. Ouça direto no player ou **baixe o arquivo WAV**.

---

## 🎭 Vozes disponíveis

| Voz | Perfil |
|-----|--------|
| **Charon** | Profissional (recomendado para tutoriais) |
| **Kore** | Firme e direta |
| **Aoede** | Suave e acolhedora |
| **Puck** | Expressivo e dinâmico |
| **Fenrir** | Grave e imponente |
| **Leda** | Clara e articulada |
| **Orus** | Neutro e equilibrado |
| **Zephyr** | Leve e fluida |
| *(+ Novas)* | Alnilam, Enceladus, Gacrux, Umbriel, Schedar |

---

## 📁 Estrutura Atualizada

```
tts_app/
├── app.py              ← Backend Flask + Novas rotas (/generate-stream, /scriptify, /assemble)
├── index.html          ← Interface web completa (Cards de URL, Áudio e Montagem)
├── requirements.txt    ← Dependências atualizadas do Python
├── .env.example        ← Modelo de variáveis de ambiente
└── README.md           ← Este arquivo
```
