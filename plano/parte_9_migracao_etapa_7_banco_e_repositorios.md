# Parte 9 - Migração Etapa 7: Banco e Repositórios

## Resumo
Esta parte estrutura a persistência relacional do backend para suportar vídeos, ideias, concorrentes, métricas e logs de IA.

## Objetivo
Formalizar o banco local e os repositories que alimentarão tanto as features atuais quanto a futura assistente de IA.

## Conteúdo consolidado
- Criar tabelas para `videos`, `ideas`, `channels`, `competitor_videos`, `metrics_snapshots`, `content_references`, `experiments` e `ai_usage_logs`.
- Atualizar `video_repository.py` e `idea_repository.py`.
- Criar script inicial de seed ou migração.
- Manter SQLite como ponto de partida por ser suficiente para localhost.
- Modelar persistência de forma que vídeos publicados, ideias geradas, coleta de concorrentes e custo de IA fiquem disponíveis para consultas futuras.

### Schema SQL de referência (conforme plano_melhoria.md)

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
  feature TEXT,
  provider TEXT,
  model TEXT,
  input_tokens INTEGER,
  output_tokens INTEGER,
  estimated_cost_usd REAL,
  video_id INTEGER,
  created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

## Prioridades e decisões
- A persistência deixa de ser acessória e passa a ser base da inteligência futura do sistema.
- O banco deve ser simples para operar localmente, mas completo o suficiente para suportar histórico, cache e análises.
- O schema deve contemplar desde já uso de custo por feature e snapshots de métricas.
- A tabela `ai_usage_logs` é obrigatória desde a Etapa 2 e deve estar formalmente incorporada ao banco nesta etapa caso ainda não tenha sido criada como SQLite.

## Critérios de aceite e pontos de atenção
- As tabelas previstas devem existir no banco local: `videos`, `ideas`, `channels`, `competitor_videos`, `metrics_snapshots`, `content_references`, `experiments` e `ai_usage_logs`.
- Repositories precisam cobrir leitura e gravação para os fluxos principais.
- A tabela `ai_usage_logs` deve estar funcional e integrada com o `ai_usage_repository.py` criado na Etapa 2.
- A estrutura deve ser suficiente para alimentar ideias com cache, monitoramento de uso e integrações do YouTube.
- Deve haver um script de migração ou seed reproduzível para recriar o banco do zero.
