# 🎬 Video AI Automation — Plano de Refatoração e Workspace

> **Contexto:** Sistema de automação de conteúdo (vídeos longos + shorts) para YouTube/TikTok, rodando 100% em localhost. Backend atual em Flask sendo migrado para FastAPI. Futuramente terá assistente de IA com análise de tendências, RAG e integração com YouTube Data API + Analytics API.

---

## 📋 Índice

1. [Visão Geral do Sistema](#1-visão-geral-do-sistema)
2. [Estado Atual](#2-estado-atual)
3. [Objetivos da Refatoração](#3-objetivos-da-refatoração)
4. [Arquitetura Alvo](#4-arquitetura-alvo)
5. [Estrutura de Pastas](#5-estrutura-de-pastas)
6. [Plano de Migração em Etapas](#6-plano-de-migração-em-etapas)
7. [Endpoints](#7-endpoints)
8. [Variáveis de Ambiente](#8-variáveis-de-ambiente)
9. [Assistente de IA — Roadmap](#9-assistente-de-ia--roadmap)
10. [YouTube Data API + Analytics API](#10-youtube-data-api--analytics-api)
11. [Banco de Dados e RAG](#11-banco-de-dados-e-rag)
12. [Controle de Custo de IA](#12-controle-de-custo-de-ia)
13. [Como Rodar Localmente](#13-como-rodar-localmente)
14. [Riscos e Pontos de Atenção](#14-riscos-e-pontos-de-atenção)
15. [Pendências e TODOs](#15-pendências-e-todos)

---

## 1. Visão Geral do Sistema

### O que o sistema faz hoje
- Conecta com a **API do Gemini** para geração de conteúdo
- Gera **áudios** (voz/narração)
- Busca **imagens e vídeos gratuitos** em fontes externas
- Monta e exporta **vídeos longos** para YouTube
- Monta e exporta **shorts** para YouTube e TikTok
- Agenda/sobe conteúdo via integração com plataformas

### O que o sistema terá no futuro
- **Assistente de IA** que gera ideias baseadas em dados reais
- **Análise de concorrentes** via YouTube Data API
- **Análise do próprio canal** via YouTube Analytics API
- **RAG** — memória de vídeos publicados, métricas, roteiros e aprendizados
- **Banco vetorial** para busca semântica de ideias e referências
- **Dashboard local** para acompanhar performance e gerenciar publicações

### Onde roda
- **100% localhost** — sem deploy em servidor externo
- Repositório salvo no **GitHub** (código versionado, sem expor chaves)
- Acesso local via navegador: `http://localhost:8000/docs`

---

## 2. Estado Atual

### Stack atual
- Python + Flask
- API Gemini (integração existente e funcionando)
- Geração de áudio/vídeo/short operacional
- `.env` para configurações sensíveis

### O que já funciona (não quebrar)
- [ ] Geração de vídeo longo
- [ ] Geração de short
- [ ] Busca de assets (imagens/vídeos gratuitos)
- [ ] Geração de áudio/narração
- [ ] Integração com Gemini
- [ ] Upload/agendamento para YouTube e TikTok

---

## 3. Objetivos da Refatoração

### Por que migrar Flask → FastAPI

| Aspecto | Flask | FastAPI |
|---|---|---|
| Documentação automática | ❌ Manual | ✅ `/docs` (Swagger) automático |
| Tipagem e validação | ❌ Manual | ✅ Pydantic nativo |
| Performance assíncrona | ⚠️ Limitada | ✅ async/await nativo |
| Schemas de entrada/saída | ❌ Manual | ✅ Pydantic models |
| Organização modular | ⚠️ Depende de esforço | ✅ APIRouter nativo |
| Preparação para IA/agentes | ⚠️ Possível mas verboso | ✅ Mais natural |

### Objetivos concretos
1. Trocar Flask por FastAPI sem quebrar nenhuma funcionalidade existente
2. Separar lógica em camadas: routers → services → repositories
3. Adicionar schemas Pydantic para todas as entradas e saídas
4. Preparar endpoints para YouTube Data API e Analytics API
5. Estruturar projeto para receber o módulo de IA assistente
6. Garantir que tudo continue rodando 100% em localhost

> ⚠️ **Importante:** A refatoração Flask → FastAPI é **custo neutro** em relação ao uso de IA. Ela reorganiza código, não aumenta chamadas ao Gemini. O custo de IA só aumenta quando novos features (assistente, análise de concorrentes, etc.) forem ativados.

---

## 4. Arquitetura Alvo

```
[Usuário / Dashboard]
        ↓
[FastAPI — app/main.py]
        ↓
[Routers: health / media / ideas / youtube / analytics / ai]
        ↓
[Services: gemini / media / audio / video / image_search / youtube_data / youtube_analytics / idea / ai_assistant]
        ↓
[Repositories: video_repository / idea_repository]
        ↓
[Storage: local_storage]
        ↓
[APIs externas: Gemini / YouTube Data API / YouTube Analytics API / fontes de assets]
```

### Fluxo de geração de vídeo longo
```
POST /media/generate-video
        ↓
  media_service.py
        ↓
  ┌─────────────────────┐
  │  gemini_service      │ ← gera roteiro
  │  [aprovação manual]  │ ← ⚠️ aprovar roteiro ANTES de gerar áudio
  │  audio_service       │ ← gera narração (maior custo do sistema)
  │  image_search_service│ ← busca assets
  │  video_service       │ ← monta vídeo
  └─────────────────────┘
        ↓
  local_storage.py (salva arquivo)
        ↓
  Retorna path/status
```

> ⚠️ **Ponto crítico de custo:** O maior gasto do sistema é a geração de áudio/TTS, não o texto. Retrabalho de áudio (gerar → errar roteiro → ajustar → gerar de novo) pode multiplicar o custo rapidamente. Implemente uma etapa de revisão manual do roteiro antes de acionar o TTS.

### Fluxo da assistente de IA (futuro)
```
POST /ai/assistant
        ↓
  ai_assistant_service.py
        ↓
  ┌─────────────────────────────────┐
  │  RAG → banco vetorial           │ ← busca contexto relevante
  │  youtube_data_service           │ ← dados de concorrentes (filtrados)
  │  youtube_analytics_service      │ ← métricas do canal
  │  idea_repository                │ ← ideias anteriores
  └─────────────────────────────────┘
        ↓
  Gemini / Modelo local (Ollama)
        ↓
  Resposta com ideias, análise, sugestões
```

---

## 5. Estrutura de Pastas

```
video-ai-automation/
├── app/
│   ├── main.py                        # Ponto de entrada FastAPI
│   ├── core/
│   │   ├── config.py                  # Configurações via pydantic-settings
│   │   └── security.py                # (futuro) autenticação local
│   ├── routers/
│   │   ├── health.py                  # GET /health
│   │   ├── media.py                   # /media/generate-video, /media/generate-short, /media/search-assets
│   │   ├── ideas.py                   # /ideas/generate
│   │   ├── youtube.py                 # /youtube/search, /youtube/videos/{id}, /youtube/channels/{id}
│   │   ├── analytics.py               # /analytics/youtube/channel-summary, /videos, /videos/{id}
│   │   └── ai.py                      # /ai/generate, /ai/assistant (futuro)
│   ├── schemas/
│   │   ├── media.py                   # Pydantic models para media
│   │   ├── ideas.py                   # Pydantic models para ideias
│   │   ├── youtube.py                 # Pydantic models para YouTube
│   │   ├── analytics.py               # Pydantic models para analytics
│   │   └── ai.py                      # Pydantic models para IA
│   ├── services/
│   │   ├── gemini_service.py          # Integração com Gemini API
│   │   ├── media_service.py           # Orquestra geração de mídia
│   │   ├── audio_service.py           # Geração de áudio/narração
│   │   ├── video_service.py           # Montagem de vídeo longo
│   │   ├── short_service.py           # Montagem de shorts
│   │   ├── image_search_service.py    # Busca de imagens/vídeos gratuitos
│   │   ├── youtube_data_service.py    # YouTube Data API (API key)
│   │   ├── youtube_analytics_service.py # YouTube Analytics API (OAuth)
│   │   ├── idea_service.py            # Geração e gestão de ideias
│   │   └── ai_assistant_service.py    # (futuro) Assistente com RAG
│   ├── repositories/
│   │   ├── video_repository.py        # CRUD de vídeos no banco
│   │   ├── idea_repository.py         # CRUD de ideias no banco
│   │   └── ai_usage_repository.py     # Log de uso e custo de IA ← novo
│   ├── storage/
│   │   └── local_storage.py           # Gestão de arquivos locais
│   └── utils/
│       ├── logging.py                 # Configuração de logs
│       └── dates.py                   # Utilitários de data/hora
├── tests/
│   └── test_health.py
├── storage/                           # Arquivos gerados (vídeos, áudios, assets)
│   ├── videos/
│   ├── shorts/
│   ├── audio/
│   └── assets/
├── .env                               # NÃO commitar — variáveis reais
├── .env.example                       # Commitar — template sem valores
├── .gitignore
├── requirements.txt
└── README.md
```

### .gitignore mínimo recomendado
```
.env
storage/videos/
storage/shorts/
storage/audio/
storage/assets/
__pycache__/
*.pyc
.venv/
venv/
*.egg-info/
.DS_Store
```

---

## 6. Plano de Migração em Etapas

> **Regra:** Cada etapa deve deixar o sistema rodando antes de passar para a próxima.

---

### Etapa 1 — Setup FastAPI (sem quebrar nada)

**Objetivo:** Subir FastAPI ao lado do Flask. Não remover Flask ainda.

- [ ] Criar `app/main.py` com FastAPI básico
- [ ] Criar `app/core/config.py` com pydantic-settings lendo `.env`
- [ ] Criar `GET /health` retornando `{ "status": "ok" }`
- [ ] Confirmar que `uvicorn app.main:app --reload` sobe sem erros
- [ ] Confirmar que `/docs` abre

**Critério de aceite:** `/health` e `/docs` funcionando.

---

### Etapa 2 — Migrar integração com Gemini

**Objetivo:** Isolar toda lógica do Gemini em `services/gemini_service.py`.

- [ ] Criar `app/services/gemini_service.py`
- [ ] Mover lógica de chamada à API Gemini para o service
- [ ] Criar `app/schemas/ai.py` com Pydantic models para entrada/saída
- [ ] Criar `app/routers/ai.py` com `POST /ai/generate`
- [ ] **Criar `app/repositories/ai_usage_repository.py`** — logar cada chamada de IA desde o início
- [ ] Testar que gera resposta igual ao comportamento anterior

**Critério de aceite:** `POST /ai/generate` retorna resposta do Gemini e log de uso é registrado.

---

### Etapa 3 — Migrar geração de mídia

**Objetivo:** Mover toda lógica de geração de vídeo/áudio/short para services.

- [ ] Criar `app/services/audio_service.py`
- [ ] Criar `app/services/video_service.py`
- [ ] Criar `app/services/short_service.py`
- [ ] Criar `app/services/image_search_service.py`
- [ ] Criar `app/services/media_service.py` (orquestrador)
- [ ] Criar `app/schemas/media.py`
- [ ] Criar `app/routers/media.py` com endpoints:
  - `POST /media/generate-script` ← **novo:** gera só o roteiro, sem áudio
  - `POST /media/generate-video` ← recebe roteiro já aprovado e gera tudo
  - `POST /media/generate-short`
  - `POST /media/search-assets`
- [ ] Criar `app/storage/local_storage.py`
- [ ] Testar geração de vídeo longo completo
- [ ] Testar geração de short completo

> ⚠️ Separar `generate-script` de `generate-video` é essencial para evitar retrabalho de áudio. O fluxo recomendado é: gerar roteiro → revisar manualmente → aprovar → gerar áudio e vídeo.

**Critério de aceite:** Fluxo de geração funcionando igual ao Flask original, com etapa de roteiro separada.

---

### Etapa 4 — Geração de ideias com cache

**Objetivo:** Criar módulo de geração de ideias com IA e cache para evitar gastos repetidos.

- [ ] Criar `app/services/idea_service.py`
- [ ] Criar `app/schemas/ideas.py`
- [ ] Criar `app/routers/ideas.py` com `POST /ideas/generate`
- [ ] Criar `app/repositories/idea_repository.py` (salvar ideias no banco)
- [ ] Configurar banco SQLite local para desenvolvimento
- [ ] **Implementar cache de ideias:** se já gerou ideias para o mesmo tema hoje, reutilizar do banco
- [ ] **Adicionar parâmetro `force=true`** para forçar nova geração ignorando cache

**Critério de aceite:** `POST /ideas/generate` retorna lista de ideias estruturadas e evita chamadas redundantes ao Gemini.

---

### Etapa 5 — YouTube Data API (sem IA primeiro)

**Objetivo:** Conectar com YouTube Data API para pesquisar vídeos e canais — **salvar dados localmente antes de enviar para IA**.

- [ ] Criar `app/services/youtube_data_service.py`
- [ ] Criar `app/schemas/youtube.py`
- [ ] Criar `app/routers/youtube.py` com endpoints:
  - `GET /youtube/search`
  - `GET /youtube/videos/{video_id}`
  - `GET /youtube/channels/{channel_id}`
- [ ] Adicionar `YOUTUBE_API_KEY` no `.env`
- [ ] **Salvar resultados no banco sem enviar ao Gemini** — calcular views/dia, taxa like/view e ordenação localmente
- [ ] Implementar cache de resultados para não esgotar quota diária (10.000 unidades/dia)
- [ ] Testar busca por termo e retorno normalizado

> ⚠️ **Estratégia de custo:** Buscar e salvar dados dos concorrentes no banco primeiro. Só enviar ao Gemini os top 10 ou top 20 mais relevantes, nunca a lista completa. Calcular métricas como views/dia e engajamento localmente, sem usar IA para isso.

**Critério de aceite:** Busca retorna lista normalizada com métricas calculadas localmente. Gemini não é acionado nesta etapa.

---

### Etapa 6 — YouTube Analytics API

**Objetivo:** Conectar com Analytics API para métricas do próprio canal.

- [ ] Criar `app/services/youtube_analytics_service.py`
- [ ] Criar `app/schemas/analytics.py`
- [ ] Criar `app/routers/analytics.py` com endpoints:
  - `GET /analytics/youtube/channel-summary`
  - `GET /analytics/youtube/videos`
  - `GET /analytics/youtube/videos/{video_id}`
- [ ] Implementar fluxo OAuth 2.0 para autorização do canal
- [ ] Armazenar `refresh_token` no `.env` após primeiro login
- [ ] Testar métricas: views, watch time, retenção, CTR

**Critério de aceite:** Endpoint retorna métricas reais do canal (ou erro claro se OAuth não configurado).

---

### Etapa 7 — Banco de dados e repositórios

**Objetivo:** Estruturar persistência de dados para alimentar a assistente de IA.

- [ ] Criar tabelas no banco:
  - `videos` — histórico de vídeos publicados
  - `ideas` — ideias geradas e avaliadas
  - `channels` — canais concorrentes monitorados
  - `competitor_videos` — vídeos coletados da concorrência
  - `metrics_snapshots` — snapshots de métricas por período
  - `content_references` — referências externas salvas
  - `experiments` — testes de título, formato, duração
  - `ai_usage_logs` — log de custo por feature ← **novo**
- [ ] Atualizar `video_repository.py` e `idea_repository.py`
- [ ] Criar script de seed/migração inicial

---

### Etapa 8 — Assistente de IA com RAG (futuro)

**Objetivo:** Criar assistente que usa dados reais para sugerir conteúdo.

- [ ] Criar `app/services/ai_assistant_service.py`
- [ ] Implementar embeddings para ideias e roteiros
- [ ] Configurar banco vetorial (ChromaDB ou pgvector)
- [ ] Criar endpoint `POST /ai/assistant`
- [ ] Integrar com modelos locais via Ollama para tarefas simples — **testar qualidade em português antes de confiar no roteamento automático**
- [ ] Manter Gemini para decisões estratégicas
- [ ] Implementar roteamento: tarefa simples → Ollama, tarefa estratégica → Gemini

---

## 7. Endpoints

### Health
```
GET  /health
```
Resposta: `{ "status": "ok" }`

---

### IA / Gemini
```
POST /ai/generate
```
Body:
```json
{
  "prompt": "string",
  "model": "string (opcional)",
  "temperature": 0.7
}
```
Resposta:
```json
{
  "response": "string",
  "model_used": "string",
  "tokens_used": 0
}
```

---

### Geração de Ideias
```
POST /ideas/generate
```
Body:
```json
{
  "topic": "military aviation history",
  "platforms": ["youtube", "tiktok"],
  "content_type": "long_video",
  "language": "pt",
  "quantity": 10,
  "force": false
}
```
> `force: false` (padrão) → reutiliza ideias do banco se já gerou hoje para o mesmo tema.
> `force: true` → ignora cache e chama o Gemini novamente.

Resposta:
```json
{
  "ideas": [
    {
      "title": "string",
      "hook": "string",
      "format": "long_video | short",
      "platform": "youtube | tiktok",
      "reason": "string",
      "keywords": ["string"],
      "estimated_duration_seconds": 0
    }
  ],
  "from_cache": false
}
```

---

### Mídia
```
POST /media/generate-script    ← gera só o roteiro (texto, sem áudio)
POST /media/generate-video     ← recebe roteiro aprovado e gera tudo
POST /media/generate-short
POST /media/search-assets
```

---

### YouTube Data API
```
GET /youtube/search?q=...&max_results=10&order=viewCount
GET /youtube/videos/{video_id}
GET /youtube/channels/{channel_id}
```

---

### YouTube Analytics API
```
GET /analytics/youtube/channel-summary?start_date=...&end_date=...
GET /analytics/youtube/videos?start_date=...&end_date=...
GET /analytics/youtube/videos/{video_id}?start_date=...&end_date=...
```

---

### Controle de Custo
```
GET /usage/summary             ← resumo de custo por feature e período
GET /usage/by-feature          ← custo detalhado por endpoint/feature
```

---

## 8. Variáveis de Ambiente

Arquivo `.env.example` (commitar no GitHub):

```env
# Aplicação
APP_ENV=development
APP_NAME=video-ai-automation
APP_DEBUG=true
APP_HOST=127.0.0.1
APP_PORT=8000

# Gemini
GEMINI_API_KEY=
GEMINI_MODEL=gemini-1.5-flash

# YouTube Data API
YOUTUBE_API_KEY=

# YouTube Analytics API (OAuth 2.0)
YOUTUBE_CLIENT_ID=
YOUTUBE_CLIENT_SECRET=
YOUTUBE_REDIRECT_URI=http://localhost:8000/auth/youtube/callback
YOUTUBE_REFRESH_TOKEN=

# Storage
STORAGE_PATH=storage

# Banco de dados
DATABASE_URL=sqlite:///./database.db

# Ollama (modelos locais)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b

# Banco vetorial (futuro)
VECTOR_DB_PATH=storage/vector_db
```

---

## 9. Assistente de IA — Roadmap

### Fase 1 — Assistente com ferramentas (próximo passo real)
A assistente não precisa ser "treinada". Ela precisa de **ferramentas** e **contexto**.

Ferramentas que a assistente terá:
- `listar_videos_publicados()` — consulta banco local
- `buscar_metricas_video(video_id)` — consulta Analytics API
- `buscar_concorrentes(tema)` — consulta banco local (dados já coletados)
- `buscar_ideias_anteriores(tema)` — consulta banco de ideias
- `gerar_nova_ideia(contexto)` — chama Gemini
- `sugerir_titulo(roteiro)` — variações de título
- `analisar_tendencia(tema)` — compara dados históricos

### Fase 2 — Banco de conhecimento
Cada vídeo publicado alimenta o banco com:
- Título, descrição, tags, formato, duração
- Métricas após 7, 30 e 90 dias
- Roteiro original e versão final
- Nicho/tema/subnicho
- Resultado (bom, médio, ruim) avaliado pelo dono

### Fase 3 — RAG
Embeddings gerados para:
- Roteiros anteriores
- Ideias geradas e salvas
- Vídeos de concorrentes (título + descrição)
- Referências externas

### Fase 4 — Roteamento inteligente
```
Tarefa simples (geração de título, variação, resumo)
  → Ollama local (llama3.1:8b ou gemma2:9b)
  ⚠️ Validar qualidade em português antes de ativar o roteamento automático

Tarefa estratégica (análise de mercado, decisão de tema, plano)
  → Gemini API

Tarefa com dados internos (análise de performance, padrões)
  → RAG + modelo local ou Gemini
```

> ⚠️ **Atenção com Ollama em português:** Modelos 7B/8B locais têm qualidade inconsistente em português. Teste com volume pequeno antes de confiar no roteamento automático. O risco real é: o modelo local gerar resultado ruim → você refazer com Gemini → custo dobrado em vez de reduzido.

### Fase 5 — Fine-tuning (avançado, futuro distante)
Apenas para tarefas muito específicas como:
- Classificar ideias no formato exato do canal
- Gerar títulos no estilo do canal
- Classificar risco de demonetização
- Padronizar roteiros no template próprio

> ⚠️ Fine-tuning **não é para colocar conhecimento no modelo**. Para isso, use RAG.

---

## 10. YouTube Data API + Analytics API

### YouTube Data API — O que é possível

A API é pública e usa API key. Permite:

| Recurso | Disponível | Notas |
|---|---|---|
| Buscar vídeos por termo | ✅ | `search.list` |
| Detalhes de vídeo (views, likes, duração) | ✅ | `videos.list` |
| Dados de canal (inscritos, total de views) | ✅ | `channels.list` |
| Playlists | ✅ | `playlistItems.list` |
| Comentários | ✅ | `commentThreads.list` |
| Aba "Inspiração" do YouTube Studio | ❌ | Não exposta via API pública |

**Estratégia de uso com IA:**
- Buscar e salvar dados dos concorrentes no banco **sem enviar ao Gemini**
- Calcular views/dia, taxa like/view e engajamento **localmente**
- Enviar ao Gemini apenas os **top 10 ou top 20** mais relevantes, nunca a lista completa
- Quanto mais dados brutos você mandar (transcrições, descrições longas, muitos vídeos), mais caro fica

### YouTube Analytics API — O que é possível

Exige OAuth 2.0. Acesso apenas ao canal autorizado. Permite:

| Métrica | Disponível |
|---|---|
| Views por vídeo/período | ✅ |
| Watch time total | ✅ |
| Retenção média (%) | ✅ |
| CTR (click-through rate) | ✅ |
| Inscritos ganhos/perdidos | ✅ |
| Origem do tráfego | ✅ |
| Receita estimada | ✅ (se monetizado) |
| Dados demográficos | ✅ |

**Fluxo de autenticação OAuth:**
1. Criar projeto no Google Cloud Console
2. Habilitar YouTube Analytics API
3. Criar credenciais OAuth 2.0 (tipo Desktop ou Web)
4. Primeira vez: abrir URL de autorização, logar com a conta do canal
5. Salvar `refresh_token` no `.env`
6. A partir daí, o sistema renova o token automaticamente

---

## 11. Banco de Dados e RAG

### Banco relacional (SQLite local)

Para começar, SQLite é suficiente (arquivo local, sem servidor):

```sql
-- Vídeos publicados no canal
CREATE TABLE videos (
  id INTEGER PRIMARY KEY,
  title TEXT,
  description TEXT,
  platform TEXT,        -- youtube | tiktok
  content_type TEXT,    -- long_video | short
  duration_seconds INTEGER,
  topic TEXT,
  nicho TEXT,
  published_at DATETIME,
  youtube_video_id TEXT,
  script_path TEXT,
  audio_path TEXT,
  video_path TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Métricas por vídeo (snapshots periódicos)
CREATE TABLE metrics_snapshots (
  id INTEGER PRIMARY KEY,
  video_id INTEGER REFERENCES videos(id),
  snapshot_date DATE,
  views INTEGER,
  watch_time_minutes INTEGER,
  avg_retention_percent REAL,
  ctr_percent REAL,
  likes INTEGER,
  comments INTEGER,
  subscribers_gained INTEGER
);

-- Ideias geradas
CREATE TABLE ideas (
  id INTEGER PRIMARY KEY,
  title TEXT,
  hook TEXT,
  format TEXT,
  platform TEXT,
  topic TEXT,
  keywords TEXT,        -- JSON array
  source TEXT,          -- ai_generated | manual | competitor
  status TEXT,          -- pending | approved | rejected | done
  reason TEXT,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Vídeos de concorrentes
CREATE TABLE competitor_videos (
  id INTEGER PRIMARY KEY,
  youtube_video_id TEXT UNIQUE,
  title TEXT,
  description TEXT,
  channel_id TEXT,
  channel_title TEXT,
  published_at DATETIME,
  duration_seconds INTEGER,
  views INTEGER,
  likes INTEGER,
  comments INTEGER,
  views_per_day REAL,
  collected_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Log de uso de IA por feature
CREATE TABLE ai_usage_logs (
  id INTEGER PRIMARY KEY,
  feature TEXT,               -- video_script | tts | idea_generation | competitor_analysis | title_generation | etc.
  provider TEXT,              -- gemini | ollama
  model TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  estimated_cost_usd REAL,
  video_id INTEGER,           -- referência opcional ao vídeo relacionado
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Banco vetorial (ChromaDB — fase futura)

```python
# Exemplo de uso com ChromaDB
import chromadb

client = chromadb.PersistentClient(path="storage/vector_db")
collection = client.get_or_create_collection("ideas")

# Adicionar ideia com embedding
collection.add(
    documents=["Título: X\nRoteiro: Y\nResultado: Z views"],
    ids=["idea_001"],
    metadatas=[{"topic": "aviation", "views": 5000}]
)

# Buscar ideias similares
results = collection.query(
    query_texts=["aviação militar segunda guerra"],
    n_results=5
)
```

---

## 12. Controle de Custo de IA

> Implementar desde a **Etapa 2** da migração, antes de qualquer novo feature.

### Por que logar desde o início
Sem logs de custo, quando o gasto subir você vai perder tempo descobrindo de onde veio em vez de agir. Com os logs desde o começo, você sempre saberá:
- Quanto custa gerar um vídeo longo
- Quanto custa gerar um short
- Quanto custa a assistente por dia
- Qual endpoint está gastando mais

### Tabela `ai_usage_logs`

Registrar em toda chamada de IA:

| Campo | Descrição |
|---|---|
| `feature` | Qual funcionalidade disparou a chamada |
| `provider` | `gemini` ou `ollama` |
| `model` | Modelo usado (ex: `gemini-1.5-flash`) |
| `input_tokens` | Tokens de entrada |
| `output_tokens` | Tokens de saída |
| `estimated_cost_usd` | Custo estimado calculado localmente |
| `video_id` | Referência ao vídeo (se aplicável) |

### Features a rastrear separadamente

```
video_script_generation     ← geração de roteiro via Gemini
tts_generation              ← geração de áudio/narração (maior custo)
idea_generation             ← brainstorming de ideias
competitor_analysis         ← análise de vídeos concorrentes com IA
title_generation            ← sugestões de título
description_generation      ← geração de descrição
short_script_generation     ← roteiro de short
thumbnail_analysis          ← (futuro) análise de thumbnails
```

### Projeção de custo estimado

| Cenário | Estimativa mensal |
|---|---|
| Só FastAPI + organização (sem novos features) | R$ 45–50 |
| Ideias 1x/dia com cache ativo | R$ 50–60 |
| Ideias + análise de concorrentes 1x/dia (top 10 apenas) | R$ 63–78 |
| Assistente usada várias vezes ao dia | R$ 100–150 |

> O principal fator de variação é o **retrabalho de áudio (TTS)**, não o texto. Roteiros ajustados várias vezes antes da aprovação podem dobrar o custo mensal.

### Endpoint de monitoramento

```
GET /usage/summary?start_date=...&end_date=...
```

Resposta sugerida:
```json
{
  "period": "2024-01",
  "total_cost_usd": 12.50,
  "by_feature": {
    "tts_generation": 7.20,
    "video_script_generation": 2.80,
    "idea_generation": 1.30,
    "competitor_analysis": 1.20
  },
  "calls_by_feature": {
    "tts_generation": 45,
    "video_script_generation": 30,
    "idea_generation": 12,
    "competitor_analysis": 8
  }
}
```

---

## 13. Como Rodar Localmente

### Requisitos
- Python 3.11+
- pip
- Git
- (Opcional) Ollama instalado para modelos locais

### Instalação

```bash
# 1. Clonar repositório
git clone https://github.com/seu-usuario/video-ai-automation.git
cd video-ai-automation

# 2. Criar ambiente virtual
python -m venv venv
source venv/bin/activate  # Linux/Mac
# ou
venv\Scripts\activate     # Windows

# 3. Instalar dependências
pip install -r requirements.txt

# 4. Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com suas chaves reais

# 5. Criar pastas de storage
mkdir -p storage/videos storage/shorts storage/audio storage/assets

# 6. Rodar o servidor
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

### Acessar
- Documentação Swagger: http://localhost:8000/docs
- Documentação ReDoc: http://localhost:8000/redoc
- Health check: http://localhost:8000/health
- Resumo de custo de IA: http://localhost:8000/usage/summary

### requirements.txt sugerido

```
fastapi>=0.111.0
uvicorn[standard]>=0.29.0
pydantic>=2.7.0
pydantic-settings>=2.2.0
python-dotenv>=1.0.0
httpx>=0.27.0
google-generativeai>=0.5.0
google-auth>=2.29.0
google-auth-oauthlib>=1.2.0
google-api-python-client>=2.127.0
SQLAlchemy>=2.0.0
alembic>=1.13.0
chromadb>=0.5.0
ollama>=0.2.0
python-multipart>=0.0.9
```

---

## 14. Riscos e Pontos de Atenção

### Riscos da migração Flask → FastAPI

| Risco | Nível | Mitigação |
|---|---|---|
| Quebrar fluxo de geração de vídeo | 🔴 Alto | Migrar em etapas, testar cada service antes de remover Flask |
| Retrabalho de áudio multiplicando custo | 🔴 Alto | Separar `generate-script` de `generate-video`; aprovar roteiro manualmente antes do TTS |
| Perder configurações do .env | 🟡 Médio | Usar `.env.example` como referência, validar via pydantic-settings |
| Uploads/paths de arquivo quebrados | 🟡 Médio | Testar local_storage.py com caminhos absolutos e relativos |
| Integração Gemini mudando de comportamento | 🟡 Médio | Isolar em service e testar com prompt fixo |
| OAuth YouTube Analytics exigir re-autenticação | 🟡 Médio | Documentar passo a passo e salvar refresh_token |
| Ollama gerando resultado ruim em português e causando retrabalho | 🟡 Médio | Testar qualidade com volume pequeno antes de ativar roteamento automático |
| Custo de IA subindo sem visibilidade da causa | 🟡 Médio | Implementar `ai_usage_logs` desde a Etapa 2 |

### Limites conhecidos dos modelos locais (Ollama 3B/7B)

- Janela de contexto: 6k a 12k tokens — usar RAG para compensar
- Qualidade de raciocínio estratégico: inferior aos modelos grandes
- **Qualidade em português: inconsistente** — validar antes de confiar no roteamento automático
- Ideal para: geração de variações, classificação, extração de JSON, brainstorming inicial
- Não ideal para: análise estratégica, decisão final, roteiro completo
- Risco real: modelo local gera resultado ruim → você refaz com Gemini → custo dobrado

### Quota da YouTube Data API (gratuita)

- 10.000 unidades por dia
- Busca (`search.list`): 100 unidades por chamada
- Detalhes de vídeo (`videos.list`): 1 unidade por chamada
- Planejar cache local para não esgotar quota rapidamente
- Salvar resultados no banco e só buscar novamente quando necessário

---

## 15. Pendências e TODOs

### Imediatos
- [ ] Analisar código Flask atual e listar todas as rotas existentes
- [ ] Listar todos os serviços externos usados atualmente
- [ ] Listar todas as variáveis de ambiente existentes
- [ ] Criar `.env.example` com todas as variáveis identificadas
- [ ] Subir estrutura FastAPI básica (Etapas 1 e 2)
- [ ] Criar `ai_usage_logs` já na Etapa 2 (antes de qualquer novo feature)

### Curto prazo
- [ ] Migrar todos os services (Etapa 3) com separação de `generate-script` e `generate-video`
- [ ] Adicionar YouTube Data API com coleta de dados sem IA (Etapa 5)
- [ ] Criar banco de dados local com tabelas de vídeos, ideias e usage logs
- [ ] Implementar salvamento automático de vídeos publicados
- [ ] Implementar cache de ideias por tema/dia

### Médio prazo
- [ ] YouTube Analytics API com OAuth (Etapa 6)
- [ ] Dashboard local simples (HTML/React) com painel de custo de IA por feature
- [ ] Sistema de agendamento local (scheduler para publicação)
- [ ] Coleta automática de métricas dos vídeos publicados

### Longo prazo
- [ ] Embeddings e banco vetorial (ChromaDB)
- [ ] Assistente com RAG completo
- [ ] Testar Ollama em português com volume real antes de integrar no roteamento
- [ ] Integração com Ollama para roteamento híbrido (após validação de qualidade)
- [ ] Fine-tuning básico para tarefas específicas do canal

---

## Notas de Estudo — Para Consulta

### Caminho de aprendizado recomendado (paralelo ao projeto)

```
1. Python para backend e automação  ← você já tem
2. FastAPI + Pydantic                ← essa refatoração
3. APIs REST e httpx                 ← essa refatoração
4. LLM APIs (Gemini, OpenAI, etc.)  ← você já tem
5. RAG com embeddings               ← próximo passo de estudo
6. Banco vetorial (ChromaDB)        ← junto com RAG
7. Ollama e modelos locais          ← já pode começar (mas teste em português)
8. Agentes e function calling       ← depois do RAG
9. Fine-tuning básico               ← longo prazo
10. MLOps e monitoramento           ← longo prazo
```

### Diferença entre os perfis de IA

| Perfil | O que faz | Nível de entrada |
|---|---|---|
| AI Research Scientist | Cria modelos como o GPT do zero | Muito alto (PhDs, papers) |
| AI Engineer aplicado | Usa modelos prontos para construir produtos | **Acessível para devs backend** |
| LLM Engineer | RAG, fine-tuning, agentes, APIs de IA | Médio (seu alvo atual) |
| MLOps Engineer | Deploy, monitoramento, pipelines de ML | Médio-alto |

> **Seu perfil atual:** Backend Developer evoluindo para AI Engineer aplicado — combinando engenharia de software com IA generativa em produto real.

---

*Documento atualizado com observações sobre controle de custo, retrabalho de áudio, estratégia de uso da YouTube Data API e limitações do Ollama em português.*