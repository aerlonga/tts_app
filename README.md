# TTS Studio

Aplicacao para producao de conteudo com IA: roteirizacao, TTS, geracao de Shorts, busca de b-roll, montagem de video e integracoes com YouTube. O projeto agora roda em containers Docker, com backend FastAPI e frontend React/Vite servido por Nginx.

## Requisitos

Para subir a aplicacao com Docker, voce precisa apenas de:

- Docker
- Docker Compose v2
- Um arquivo `.env` na raiz do projeto

O FFmpeg e as dependencias Python/Node sao instalados dentro das imagens Docker.

## Configuracao

Copie o arquivo de exemplo e preencha as chaves necessarias:

```bash
cp .env.example .env
```

Principais variaveis:

```env
GEMINI_API_KEY=
DATABASE_URL=sqlite:///storage/app.db
STORAGE_PATH=storage
YOUTUBE_API_KEY=
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REFRESH_TOKEN=
```

Uma Gemini API Key pode ser criada em:

```text
https://aistudio.google.com/app/apikey
```

Por padrao, o Docker Compose sobrescreve os caminhos internos para usar SQLite em `/app/storage/app.db` e monta `./storage` como volume persistente.

## Subir Com Docker

Na raiz do projeto:

```bash
docker compose up --build
```

Depois que os containers iniciarem:

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Health check: `http://localhost:8000/health`

O frontend tambem encaminha chamadas para o backend usando `/api`, entao este endpoint deve funcionar:

```bash
curl http://localhost:5173/api/health
```

## Rodar Em Segundo Plano

```bash
docker compose up -d --build
```

Ver status:

```bash
docker compose ps
```

Ver logs:

```bash
docker compose logs -f
```

Ver logs de um servico especifico:

```bash
docker compose logs -f backend
docker compose logs -f frontend
```

Parar tudo:

```bash
docker compose down
```

## Estrutura Docker

```text
tts_app/
├── Dockerfile                 # Imagem do backend FastAPI
├── docker-compose.yml         # Orquestra backend e frontend
├── .dockerignore
├── app/
│   ├── main.py                # Entrypoint FastAPI: app.main:app
│   └── ...
├── frontend/
│   ├── Dockerfile             # Build Vite + Nginx
│   ├── nginx.conf             # Serve frontend e proxy /api para o backend
│   ├── .dockerignore
│   └── ...
├── requirements.txt
├── storage/                   # Persistencia local montada no container
└── .env.example
```

## Servicos

O `docker-compose.yml` sobe dois servicos:

- `backend`: FastAPI com Uvicorn em `0.0.0.0:8000`
- `frontend`: Nginx servindo o build do React em `localhost:5173`

O Nginx do frontend redireciona `/api/*` para o backend interno `http://backend:8000/*`.

## Desenvolvimento Sem Docker

O fluxo recomendado agora e Docker. Caso precise rodar localmente sem containers:

Backend:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Frontend:

```bash
cd frontend
npm install
npm run dev
```

No modo Vite dev, o frontend roda em `http://localhost:5173` e usa o proxy `/api` configurado em `frontend/vite.config.ts`.

## Funcionalidades

- Geracao de audio TTS com Gemini
- Streaming de TTS para textos longos
- Roteirizacao a partir de texto ou URL
- Geracao de ideias e Shorts
- Pacote de producao para Shorts
- Busca e download de b-roll em fontes publicas
- Montagem de videos com FFmpeg
- Integracoes com YouTube Data API e YouTube Analytics
- Registro de uso/custos de IA

## Testes E Validacao Rapida

Com os containers de pe:

```bash
curl http://localhost:8000/health
curl http://localhost:5173/api/health
```

Ambos devem retornar:

```json
{"status":"ok"}
```
