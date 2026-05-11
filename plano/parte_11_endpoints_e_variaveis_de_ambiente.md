# Parte 11 - Endpoints e Variáveis de Ambiente

## Resumo
Visão consolidada dos contratos HTTP e variáveis de ambiente, incluindo mapeamento Flask→FastAPI.

## Objetivo
Centralizar a referência de endpoints e configuração para implementação, validação e operação local.

## Endpoints por módulo

### Health
- `GET /health`

### IA / Gemini
- `POST /ai/generate`
- `POST /ai/assistant` (futuro)

### Ideias
- `POST /ideas/generate`

### Mídia
- `POST /media/enhance` ← `/enhance`
- `POST /media/generate-script` ← `/scriptify`
- `POST /media/generate-tts` ← `/generate`
- `POST /media/generate-tts-stream` ← `/generate-stream`
- `POST /media/generate-video` ← novo
- `POST /media/generate-short` ← `/shorts/scriptify`
- `POST /media/search-assets`
- `POST /media/assemble` ← `/assemble`
- `GET /media/assemble/status/{job_id}` ← `/assemble/status/<id>`
- `GET /media/assemble/download/{job_id}` ← `/assemble/download/<id>`

### B-Roll
- `POST /broll/search` ← `/broll/search`
- `POST /broll/download` ← `/broll/download`

### YouTube Data API
- `GET /youtube/search`
- `GET /youtube/videos/{video_id}`
- `GET /youtube/channels/{channel_id}`

### Analytics
- `GET /analytics/youtube/channel-summary`
- `GET /analytics/youtube/videos`
- `GET /analytics/youtube/videos/{video_id}`

### Controle de uso
- `GET /usage/summary`
- `GET /usage/by-feature`

## Mapeamento Flask → FastAPI

| Rota Flask | Rota FastAPI | Etapa |
|---|---|---|
| `GET /` | Frontend (fora do escopo) | — |
| `POST /enhance` | `POST /media/enhance` | 3 |
| `POST /generate` | `POST /media/generate-tts` | 3 |
| `POST /generate-stream` | `POST /media/generate-tts-stream` | 3 |
| `POST /scriptify` | `POST /media/generate-script` | 3 |
| `POST /shorts/scriptify` | `POST /media/generate-short` | 3 |
| `POST /assemble` | `POST /media/assemble` | 3 |
| `GET /assemble/status/<id>` | `GET /media/assemble/status/{job_id}` | 3 |
| `GET /assemble/download/<id>` | `GET /media/assemble/download/{job_id}` | 3 |
| `POST /broll/search` | `POST /broll/search` | 3 |
| `POST /broll/download` | `POST /broll/download` | 3 |

## Variáveis de ambiente previstas
- `APP_ENV`, `APP_NAME`, `APP_DEBUG`, `APP_HOST`, `APP_PORT`
- `GEMINI_API_KEY`, `GEMINI_MODEL`
- `YOUTUBE_API_KEY`
- `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REDIRECT_URI`, `YOUTUBE_REFRESH_TOKEN`
- `STORAGE_PATH`
- `DATABASE_URL`
- `OLLAMA_BASE_URL`, `OLLAMA_MODEL`
- `VECTOR_DB_PATH`

## Prioridades e decisões
- `.env.example` deve refletir o backend alvo, não apenas o estado legado em Flask.
- O mapeamento Flask→FastAPI serve como checklist de migração.
- Configurações de IA, banco, storage e OAuth devem ficar separadas.

## Critérios de aceite
- Todas as rotas Flask existentes devem ter equivalência FastAPI listada.
- O template de ambiente deve cobrir FastAPI, Gemini, YouTube APIs, banco e modelos locais.
