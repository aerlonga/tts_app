# 🎙️ TTS Studio

Gerador de áudio local usando **Gemini 2.5 Flash TTS** da Google.

---

## 📦 Requisitos

- Python 3.9+
- Uma **Gemini API Key** → https://aistudio.google.com/app/apikey

---

## 🚀 Instalação e uso

### 1. Instale as dependências

```bash
pip install flask google-genai
```

### 2. Rode o servidor

```bash
python app.py
```

### 3. Abra no navegador

```
http://localhost:5000
```

---

## 🎤 Como usar

1. Cole sua **Gemini API Key** no campo indicado
2. Escolha a **voz** desejada
3. Cole ou edite o **texto/roteiro**
4. Clique em **Gerar Áudio**
5. Ouça direto no player ou **baixe o arquivo WAV**

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

---

## 📁 Estrutura

```
tts_app/
├── app.py        ← Backend Flask + Gemini API
├── index.html    ← Interface web
└── README.md     ← Este arquivo
```

---

## ⚠️ Observações

- O áudio é gerado em formato **WAV (24kHz mono)**
- Textos longos podem levar **5–15 segundos** para processar
