# Parte 15 — Frontend: React + Vite

## Resumo
Plano para criar o frontend SPA do Video AI Automation usando React + Vite, consumindo a API FastAPI existente. O frontend será um dashboard local de produção de conteúdo com interface para todas as funcionalidades do backend.

## Por que React + Vite (e não Next.js)
- Aplicação é 100% localhost, sem necessidade de SSR/SSG
- API já existe em FastAPI — não precisa de API routes no frontend
- Zero necessidade de SEO (ferramenta privada)
- Vite é mais rápido e leve para SPA
- Menos complexidade = menos atrito no desenvolvimento

---

## Stack do Frontend

| Camada | Tecnologia | Motivo |
|---|---|---|
| Framework | React 18 | Componentes, hooks, ecossistema |
| Bundler | Vite | Dev server rápido, HMR instantâneo |
| Roteamento | React Router v6 | SPA routing padrão |
| Estado servidor | TanStack Query (React Query) | Cache, refetch, loading states automáticos |
| Estado local | Zustand | Estado global leve (API key, preferências) |
| HTTP | Axios | Interceptors, cancelamento, upload com progresso |
| Estilização | Tailwind CSS v4 | Prototipagem rápida, design system consistente |
| Componentes UI | shadcn/ui | Componentes acessíveis, customizáveis, sem vendor lock-in |
| Gráficos | Recharts | Charts para dashboard de analytics e custos |
| Ícones | Lucide React | Ícones consistentes (mesmo usado pelo shadcn) |
| Formulários | React Hook Form + Zod | Validação tipada que espelha os schemas Pydantic |
| Markdown | react-markdown | Renderizar scripts e respostas da assistente |
| SSE | EventSource nativo | Para streaming de TTS (já funciona com SSE) |
| TypeScript | Sim | Tipagem alinhada com os schemas Pydantic do backend |

---

## Estrutura de Pastas

```
frontend/
├── public/
├── src/
│   ├── api/                      # Camada de comunicação com FastAPI
│   │   ├── client.ts             # Axios instance configurada
│   │   ├── media.ts              # Endpoints /media/*
│   │   ├── ai.ts                 # Endpoints /ai/*
│   │   ├── ideas.ts              # Endpoints /ideas/*
│   │   ├── youtube.ts            # Endpoints /youtube/*
│   │   ├── analytics.ts          # Endpoints /analytics/*
│   │   ├── broll.ts              # Endpoints /broll/*
│   │   ├── usage.ts              # Endpoints /usage/*
│   │   └── health.ts             # Endpoint /health
│   ├── components/               # Componentes reutilizáveis
│   │   ├── ui/                   # shadcn/ui components
│   │   ├── layout/               # Shell, Sidebar, Header
│   │   ├── media/                # Players, upload, progress
│   │   ├── charts/               # Wrappers de Recharts
│   │   └── common/               # Loading, Error, Empty states
│   ├── pages/                    # Páginas (1 por rota)
│   │   ├── Dashboard.tsx
│   │   ├── ScriptStudio.tsx
│   │   ├── TTSStudio.tsx
│   │   ├── VideoAssembly.tsx
│   │   ├── ShortsGenerator.tsx
│   │   ├── IdeasLab.tsx
│   │   ├── BRollSearch.tsx
│   │   ├── YouTubeResearch.tsx
│   │   ├── ChannelAnalytics.tsx
│   │   ├── AIAssistant.tsx
│   │   ├── UsageCosts.tsx
│   │   └── Settings.tsx
│   ├── hooks/                    # Custom hooks
│   │   ├── useSSE.ts             # Hook para Server-Sent Events
│   │   ├── useJobPolling.ts      # Hook para polling de assembly jobs
│   │   └── useApiKey.ts          # Hook para gerenciar API key
│   ├── stores/                   # Zustand stores
│   │   └── appStore.ts           # API key, tema, preferências
│   ├── types/                    # Tipos TypeScript (espelham schemas Pydantic)
│   │   ├── media.ts
│   │   ├── ai.ts
│   │   ├── ideas.ts
│   │   ├── youtube.ts
│   │   ├── analytics.ts
│   │   └── usage.ts
│   ├── lib/                      # Utilitários
│   │   └── utils.ts
│   ├── App.tsx                   # Router principal
│   ├── main.tsx                  # Entry point
│   └── index.css                 # Tailwind + global styles
├── .env                          # VITE_API_BASE_URL=http://localhost:8000
├── package.json
├── tsconfig.json
├── vite.config.ts
└── tailwind.config.ts
```

---

## Páginas e Funcionalidades

### 1. Dashboard (`/`)
**Objetivo:** Visão geral do workspace.

- Card com status do backend (`GET /health`)
- Resumo de custo de IA do mês atual (`GET /usage/summary`)
- Últimas ideias geradas
- Jobs de vídeo recentes
- Links rápidos para cada seção

**Endpoints consumidos:** `/health`, `/usage/summary`

---

### 2. Script Studio (`/scripts`)
**Objetivo:** Gerar e editar roteiros a partir de URLs.

- Input de URL do artigo fonte
- Botão "Roteirizar" → `POST /media/generate-script`
- Editor de texto com o roteiro retornado
- Lista de image prompts gerados (com preview)
- Botão "Anotar Entonação" → `POST /media/enhance`
- Botão "Aprovar e Gerar Vídeo" → envia para a página de assembly

**Endpoints consumidos:** `/media/generate-script`, `/media/enhance`

---

### 3. TTS Studio (`/tts`)
**Objetivo:** Gerar narração em áudio a partir de texto.

- Textarea para colar ou editar o roteiro
- Selector de voz (Charon, etc.)
- **Modo curto** → `POST /media/generate-tts` → player de áudio + download WAV
- **Modo longo (streaming)** → `POST /media/generate-tts-stream`
  - Barra de progresso por chunk via SSE
  - Indicador de throttle (60s entre chunks)
  - Suporte a retomada (session_id)
  - Player de áudio final + download
- Exibição de chunks processados vs skipped

**Endpoints consumidos:** `/media/generate-tts`, `/media/generate-tts-stream`
**Hooks especiais:** `useSSE.ts` para consumir o EventSource

---

### 4. Video Assembly (`/assembly`)
**Objetivo:** Montar vídeo final a partir de áudio + assets.

- Upload de áudio WAV
- Upload de imagens/vídeos (drag & drop com reordenação)
- Selector de formato: Long (16:9) ou Short (9:16)
- Opção de incluir B-Roll do archive.org (link para busca)
- Manifesto de ordenação visual
- Botão "Montar" → `POST /media/assemble`
- Progress bar via polling (`GET /media/assemble/status/{job_id}`)
- Download do MP4 quando concluído

**Endpoints consumidos:** `/media/assemble`, `/media/assemble/status/{id}`, `/media/assemble/download/{id}`
**Hooks especiais:** `useJobPolling.ts`

---

### 5. Shorts Generator (`/shorts`)
**Objetivo:** Gerar roteiros de shorts derivados do roteiro longo.

- Textarea com o roteiro longo de referência
- Config: quantidade (2 ou 3), duração (45s, 60s, 65s), plataforma
- Botão "Gerar Shorts" → `POST /media/generate-short`
- Cards com cada short: título, hook, script, CTA, image prompts, B-Roll keywords
- Botão para copiar script individual
- Botão para enviar short para TTS Studio

**Endpoints consumidos:** `/media/generate-short`

---

### 6. Ideas Lab (`/ideas`)
**Objetivo:** Brainstorming de ideias para conteúdo.

- Formulário: tópico, plataformas, tipo de conteúdo, idioma, quantidade
- Toggle `force` para ignorar cache
- Botão "Gerar Ideias" → `POST /ideas/generate`
- Badge `from_cache` quando usa cache
- Cards com cada ideia: título, hook, formato, keywords, duração estimada
- Ações: aprovar, rejeitar, enviar para Script Studio

**Endpoints consumidos:** `/ideas/generate`

---

### 7. B-Roll Search (`/broll`)
**Objetivo:** Pesquisar e baixar clips de domínio público.

- Input de keywords
- Selector de coleção (Prelinger, NASA, National Archives)
- Grid de resultados com thumbnail e preview
- Player de preview embutido (via archive.org embed)
- Botão "Baixar para uso" → `POST /broll/download`
- Indicador de clips já baixados disponíveis localmente

**Endpoints consumidos:** `/broll/search`, `/broll/download`

---

### 8. YouTube Research (`/youtube`)
**Objetivo:** Pesquisar concorrentes e coletar dados.

- Busca por termo → `GET /youtube/search`
- Tabela de resultados: título, views, likes, views/dia, like rate, canal
- Ordenação por views, views/dia, relevância
- Badge `from_cache` nos resultados
- Click em vídeo → detalhes (`GET /youtube/videos/{id}`)
- Click em canal → detalhes (`GET /youtube/channels/{id}`)
- Card de canal com inscritos, total de views, vídeos

**Endpoints consumidos:** `/youtube/search`, `/youtube/videos/{id}`, `/youtube/channels/{id}`

---

### 9. Channel Analytics (`/analytics`)
**Objetivo:** Métricas do próprio canal do YouTube.

- Seletor de período (últimos 7, 30, 90 dias ou custom)
- Dashboard com cards: views totais, watch time, CTR, retenção, inscritos
- Gráfico de linha: views ao longo do período
- Tabela de vídeos com métricas por vídeo
- Detalhe de vídeo individual
- Estado de erro claro quando OAuth não está configurado

**Endpoints consumidos:** `/analytics/youtube/channel-summary`, `/analytics/youtube/videos`, `/analytics/youtube/videos/{id}`

---

### 10. AI Assistant (`/assistant`)
**Objetivo:** Chat com a assistente de IA do projeto.

- Interface de chat (messages list + input)
- Selector de task_type: strategy, quick, summarize, classification
- Selector de provider: auto, gemini, ollama
- Exibição do contexto RAG usado (source_type, title, score)
- Exibição de provider usado + routing reason
- Markdown rendering para respostas
- Custo da chamada exibido no rodapé de cada resposta

**Endpoints consumidos:** `/ai/assistant`

---

### 11. Usage & Costs (`/usage`)
**Objetivo:** Monitorar gastos com IA.

- Cards resumo: total calls, total tokens, custo estimado, projeção mensal
- Gráfico de barras: custo por feature
- Tabela detalhada por feature + provider
- Filtro por período (date range picker)

**Endpoints consumidos:** `/usage/summary`, `/usage/by-feature`

---

### 12. Settings (`/settings`)
**Objetivo:** Configurar chaves e preferências.

- Input de Gemini API Key (salva em localStorage/Zustand, enviada em cada request)
- Input de YouTube API Key
- Status de conexões (Gemini OK, YouTube OK, Ollama OK, PostgreSQL OK)
- Toggle dark mode
- Informações do sistema (versão, uptime via `/health`)

---

## Etapas de Implementação

### Etapa 1 — Setup do projeto (1-2h)
- [ ] `npx create-vite frontend --template react-ts`
- [ ] Instalar dependências: React Router, TanStack Query, Zustand, Axios, Tailwind, shadcn/ui
- [ ] Configurar Tailwind + shadcn/ui
- [ ] Criar `src/api/client.ts` com Axios apontando para `http://localhost:8000`
- [ ] Configurar proxy no Vite para evitar CORS em dev
- [ ] Criar layout base: Sidebar + Content area

### Etapa 2 — Layout e navegação (2-3h)
- [ ] Criar shell com Sidebar (links para todas as páginas)
- [ ] Configurar React Router com todas as rotas
- [ ] Criar componentes base: Loading, ErrorBoundary, EmptyState
- [ ] Implementar dark mode toggle
- [ ] Criar store Zustand para API key e preferências

### Etapa 3 — Dashboard + Settings + Usage (3-4h)
- [ ] Settings: formulário de API keys com persistência em localStorage
- [ ] Dashboard: health check + usage summary + links rápidos
- [ ] Usage & Costs: summary cards + gráfico de barras + tabela por feature
- [ ] Validar que a camada `api/` funciona com o backend real

### Etapa 4 — Script Studio + TTS Studio (4-6h)
- [ ] Script Studio: input URL → roteirização → editor → enhance
- [ ] TTS curto: textarea → generate → player + download
- [ ] TTS streaming: implementar `useSSE.ts` → progress bar → player final
- [ ] Testar fluxo completo: URL → script → enhance → TTS

### Etapa 5 — Video Assembly + Shorts + B-Roll (4-6h)
- [ ] Video Assembly: upload áudio + assets → drag & drop reorder → montar → polling → download
- [ ] Shorts Generator: script longo → config → gerar → cards
- [ ] B-Roll Search: keywords → grid de resultados → preview → download
- [ ] Implementar `useJobPolling.ts`

### Etapa 6 — Ideas Lab + YouTube Research (3-4h)
- [ ] Ideas Lab: formulário → gerar → cards com ações
- [ ] YouTube Research: busca → tabela → detalhes de vídeo/canal

### Etapa 7 — Analytics + AI Assistant (3-4h)
- [ ] Channel Analytics: date picker → dashboard de métricas → gráficos
- [ ] AI Assistant: interface de chat → context display → markdown rendering

### Etapa 8 — Polimento e integração (2-3h)
- [ ] Fluxos de navegação entre páginas (ex: Idea → Script Studio → TTS → Assembly)
- [ ] Toasts/notificações para ações
- [ ] Loading states e error handling consistentes
- [ ] Responsive (funcionar bem na janela do navegador)
- [ ] Testar todos os fluxos end-to-end

---

## Configuração de CORS no FastAPI

O frontend rodará em `http://localhost:5173` (Vite) e o backend em `http://localhost:8000` (FastAPI). É necessário configurar CORS no `main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## Resumo de esforço

| Etapa | Estimativa |
|---|---|
| 1 — Setup | 1-2h |
| 2 — Layout e navegação | 2-3h |
| 3 — Dashboard + Settings + Usage | 3-4h |
| 4 — Script Studio + TTS Studio | 4-6h |
| 5 — Assembly + Shorts + B-Roll | 4-6h |
| 6 — Ideas Lab + YouTube Research | 3-4h |
| 7 — Analytics + AI Assistant | 3-4h |
| 8 — Polimento | 2-3h |
| **Total** | **~25-35h** |

---

## Decisões técnicas a confirmar

1. **Tailwind CSS v4** — ok ou prefere outra abordagem de estilização?
2. **shadcn/ui** — ok para componentes base ou prefere Material UI / Ant Design?
3. **API key** — salvar em localStorage e enviar em cada request, ou implementar sessão no backend?
4. **Tema escuro** — padrão ou claro como default?
5. **Idioma da interface** — português ou inglês?
