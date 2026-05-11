# Parte 14 — Migração SQLite → PostgreSQL + pgvector

## Resumo
Plano para substituir o SQLite por PostgreSQL + pgvector, trocando o acesso direto via `sqlite3` por SQLAlchemy (ORM) com migrações via Alembic, e substituindo o RAG baseado em JSON por busca vetorial real com pgvector.

## Contexto — O que existe hoje

### Arquivos que serão reescritos
| Arquivo | Linhas | O que faz |
|---|---|---|
| `app/repositories/db.py` | 165 | Conexão sqlite3, schema DDL, `initialize_database()` |
| `app/repositories/ai_usage_repository.py` | 158 | Logs de custo de IA (INSERT, SUM, GROUP BY) |
| `app/repositories/idea_repository.py` | 91 | Cache de ideias por fingerprint/data |
| `app/repositories/video_repository.py` | 109 | CRUD de vídeos + snapshots de métricas |
| `app/repositories/youtube_repository.py` | 196 | Cache de payloads YouTube, upsert channels/competitors |
| `app/repositories/knowledge_repository.py` | 178 | Leitura de documentos para alimentar o RAG |
| `app/services/rag_service.py` | 94 | RAG com hash-based embeddings + JSON |
| `app/core/config.py` | 73 | `database_url` aponta para sqlite |
| `scripts/init_db.py` | 20 | Inicialização do banco |

### Dependências atuais no `requirements.txt`
- `SQLAlchemy>=2.0.0` ← já listado mas NÃO usado (repositories usam `sqlite3` direto)
- `alembic>=1.13.0` ← já listado mas NÃO usado

---

## Etapas da Migração

### Etapa 1 — Infraestrutura PostgreSQL (sem mexer no código)

**Objetivo:** Ter PostgreSQL + pgvector rodando no WSL.

```bash
# 1. Instalar PostgreSQL
sudo apt update
sudo apt install postgresql postgresql-contrib

# 2. Iniciar o serviço
sudo service postgresql start

# 3. Criar usuário e banco
sudo -u postgres psql -c "CREATE USER ttsapp WITH PASSWORD 'ttsapp_local';"
sudo -u postgres psql -c "CREATE DATABASE video_ai_automation OWNER ttsapp;"

# 4. Instalar pgvector
sudo apt install postgresql-16-pgvector
# (ou a versão que corresponder ao seu PostgreSQL)

# 5. Habilitar pgvector no banco
sudo -u postgres psql -d video_ai_automation -c "CREATE EXTENSION IF NOT EXISTS vector;"

# 6. Testar conexão
psql -U ttsapp -d video_ai_automation -h localhost -c "SELECT 1;"
```

**Critério de aceite:** `psql` conecta, `SELECT 1` retorna, `\dx` mostra `vector` como extensão instalada.

---

### Etapa 2 — Modelos SQLAlchemy (substituir o DDL do db.py)

**Objetivo:** Criar modelos ORM que substituem as `CREATE TABLE` manuais do `db.py`.

**Criar:** `app/models/__init__.py`, `app/models/base.py`, `app/models/tables.py`

```python
# app/models/base.py
from sqlalchemy.orm import DeclarativeBase

class Base(DeclarativeBase):
    pass
```

```python
# app/models/tables.py  (resumo — cada tabela vira uma classe)
from sqlalchemy import Column, Integer, String, Float, Text, DateTime, Date, ForeignKey, Index
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from app.models.base import Base

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    description = Column(Text)
    platform = Column(String(20))
    content_type = Column(String(20))
    duration_seconds = Column(Integer)
    topic = Column(Text)
    nicho = Column(Text)
    published_at = Column(DateTime)
    youtube_video_id = Column(String(50), unique=True)
    script_path = Column(Text)
    audio_path = Column(Text)
    video_path = Column(Text)
    created_at = Column(DateTime, server_default=func.now())
    # Embedding para busca vetorial
    embedding = Column(Vector(768), nullable=True)

class Idea(Base):
    __tablename__ = "ideas"
    id = Column(Integer, primary_key=True)
    title = Column(Text)
    hook = Column(Text)
    format = Column(String(20))
    platform = Column(String(20))
    topic = Column(Text)
    keywords = Column(Text)  # JSON array
    source = Column(String(20))
    status = Column(String(20))
    reason = Column(Text)
    estimated_duration_seconds = Column(Integer, default=0)
    content_type = Column(String(20))
    language = Column(String(10))
    request_fingerprint = Column(Text)
    generated_on = Column(String(10))
    created_at = Column(DateTime, server_default=func.now())
    embedding = Column(Vector(768), nullable=True)

# ... Channel, CompetitorVideo, MetricsSnapshot,
#     ContentReference, Experiment, AIUsageLog
#     (mesmos campos que o schema SQLite atual + coluna embedding onde fizer sentido)
```

**Decisão sobre embeddings:** A dimensão `768` é para modelos como `text-embedding-004` (Gemini) ou `nomic-embed-text` (Ollama). Se usar outro modelo, ajustar.

**Critério de aceite:** Modelos refletem todas as 8 tabelas do `db.py` atual + colunas `embedding` nas tabelas que alimentam o RAG.

---

### Etapa 3 — Configuração SQLAlchemy + sessão de banco

**Objetivo:** Substituir `db.py` (sqlite3 direto) por engine SQLAlchemy.

**Reescrever:** `app/repositories/db.py`

```python
# app/repositories/db.py  (nova versão)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import get_settings
from app.models.base import Base

engine = create_engine(get_settings().database_url, echo=False)
SessionLocal = sessionmaker(bind=engine)

def get_db() -> Session:
    """Dependency para routers FastAPI."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def initialize_database() -> None:
    """Cria todas as tabelas se não existirem."""
    Base.metadata.create_all(bind=engine)
```

**Atualizar:** `app/core/config.py`

```python
# Mudar de:
database_url: str = Field(default="sqlite:///./storage/app.db")

# Para:
database_url: str = Field(default="postgresql://ttsapp:ttsapp_local@localhost:5432/video_ai_automation")
```

**Atualizar:** `.env.example`

```env
DATABASE_URL=postgresql://ttsapp:ttsapp_local@localhost:5432/video_ai_automation
```

**Critério de aceite:** `initialize_database()` cria as tabelas no PostgreSQL. `\dt` no psql lista todas.

---

### Etapa 4 — Configurar Alembic (migrações)

**Objetivo:** Ter migrações versionadas para o schema do banco.

```bash
cd /home/aerlonga/tts_app
alembic init alembic
```

Configurar `alembic/env.py` para usar os modelos SQLAlchemy e o `DATABASE_URL` do config.

```bash
# Gerar migração inicial a partir dos modelos
alembic revision --autogenerate -m "initial schema"

# Aplicar migração
alembic upgrade head
```

**Critério de aceite:** `alembic upgrade head` cria as tabelas. `alembic downgrade -1` remove. Futuras alterações de schema passam por `alembic revision`.

---

### Etapa 5 — Reescrever repositories (o trabalho principal)

**Objetivo:** Substituir `sqlite3` direto por SQLAlchemy em todos os repositories.

**Ordem sugerida (do mais simples ao mais complexo):**

#### 5.1 — `ai_usage_repository.py`
- Trocar `connection.execute(SQL)` por `session.add(AIUsageLog(...))` e `session.query()`
- Manter a interface pública (`log_usage()`, `get_summary()`, `get_usage_by_feature()`)
- Testar via `GET /usage/summary`

#### 5.2 — `idea_repository.py`
- Trocar por SQLAlchemy queries
- Manter `get_cached_ideas()` e `save_ideas()`
- Testar via `POST /ideas/generate`

#### 5.3 — `video_repository.py`
- Trocar `ensure_video()`, `get_video_by_youtube_id()`, `save_metrics_snapshot()`
- Testar via YouTube Analytics integration

#### 5.4 — `youtube_repository.py`
- O mais extenso (196 linhas)
- Trocar `upsert_channel()`, `upsert_competitor_video()`, cache de payloads
- Testar via `GET /youtube/search`

#### 5.5 — `knowledge_repository.py`
- Trocar `get_documents()` para ler via SQLAlchemy
- Este será revisitado na Etapa 7 quando o RAG usar embeddings reais

**Regra:** Cada repository reescrito deve manter a mesma interface pública. Os services e routers NÃO devem precisar de alteração.

**Critério de aceite:** Todos os endpoints continuam funcionando identicamente, mas agora persistem no PostgreSQL.

---

### Etapa 6 — Migrar dados existentes (se houver)

**Objetivo:** Transferir dados do SQLite para PostgreSQL.

```python
# scripts/migrate_sqlite_to_postgres.py
import sqlite3
from sqlalchemy.orm import Session
from app.repositories.db import SessionLocal
from app.models.tables import Video, Idea, AIUsageLog, Channel, CompetitorVideo
# ... etc

def migrate():
    sqlite_conn = sqlite3.connect("storage/app.db")
    sqlite_conn.row_factory = sqlite3.Row
    
    with SessionLocal() as session:
        # Para cada tabela: SELECT * do SQLite → INSERT no PostgreSQL
        for row in sqlite_conn.execute("SELECT * FROM videos"):
            session.add(Video(**dict(row)))
        # ... repetir para todas as tabelas
        session.commit()

    sqlite_conn.close()
    print("Migração concluída.")
```

**Critério de aceite:** Dados antigos aparecem no PostgreSQL. Contagens batem entre SQLite e PostgreSQL.

---

### Etapa 7 — RAG com pgvector (substituir o hack JSON)

**Objetivo:** Trocar o RAG baseado em hash+cosine+JSON por busca vetorial real com pgvector.

**Reescrever:** `app/services/rag_service.py`

**Fluxo novo:**
```
1. knowledge_repository busca documentos do banco
2. Para cada documento sem embedding → gerar embedding via Ollama ou Gemini
3. Salvar embedding na coluna `embedding` (pgvector Vector(768))
4. Busca = query SQL com operador pgvector: ORDER BY embedding <=> query_embedding
```

**Geração de embeddings (escolher 1):**

| Opção | Modelo | Dimensão | Custo | Qualidade PT |
|---|---|---|---|---|
| Gemini API | `text-embedding-004` | 768 | Gratuito até 1500 req/min | ✅ Boa |
| Ollama local | `nomic-embed-text` | 768 | Gratuito (local) | ✅ Boa |
| Ollama local | `mxbai-embed-large` | 1024 | Gratuito (local) | ✅ Boa |

**Exemplo de busca vetorial com pgvector:**
```python
from pgvector.sqlalchemy import Vector
from sqlalchemy import text

def search(self, query: str, limit: int = 5) -> list[dict]:
    query_embedding = self._generate_embedding(query)
    
    results = session.execute(
        text("""
            SELECT id, title, content, source_type,
                   1 - (embedding <=> :embedding) AS score
            FROM ideas
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :embedding
            LIMIT :limit
        """),
        {"embedding": str(query_embedding), "limit": limit}
    ).fetchall()
    
    return [dict(row) for row in results]
```

**Critério de aceite:** `POST /ai/assistant` retorna resultados baseados em similaridade vetorial real, não hash.

---

### Etapa 8 — Remover SQLite e limpar

**Objetivo:** Remover código e dependências do SQLite.

- [ ] Remover `storage/app.db`
- [ ] Remover `storage/vector_db/assistant_index.json`
- [ ] Remover referências a `sqlite3` em todo o código
- [ ] Remover `database_path` property do config (substituída por `database_url` nativo do SQLAlchemy)
- [ ] Atualizar `.env.example`
- [ ] Atualizar `requirements.txt` (remover `chromadb` se não for usar, adicionar `pgvector` e `psycopg2-binary`)

**requirements.txt atualizado:**
```
# Adicionar
psycopg2-binary>=2.9.9
pgvector>=0.3.0

# Remover (se não usar mais)
chromadb>=0.5.0
```

---

## Resumo do impacto

| O que muda | Esforço |
|---|---|
| `app/repositories/db.py` | Reescrita total (sqlite3 → SQLAlchemy engine) |
| `app/repositories/*.py` (5 arquivos) | Reescrita de queries (sqlite3 → SQLAlchemy ORM) |
| `app/models/` (novo) | Criar modelos ORM para todas as tabelas |
| `app/services/rag_service.py` | Reescrita total (JSON → pgvector) |
| `app/core/config.py` | Ajuste mínimo (DATABASE_URL) |
| `scripts/init_db.py` | Simplificar (usar Alembic) |
| `alembic/` (novo) | Configurar migrações |
| Routers e services | **Zero mudança** (interface dos repositories não muda) |
| Frontend | **Zero mudança** |

## Ordem de execução

```
Etapa 1  →  Instalar PostgreSQL + pgvector (30 min)
Etapa 2  →  Criar modelos SQLAlchemy (2-3h)
Etapa 3  →  Configurar engine + sessão (1h)
Etapa 4  →  Configurar Alembic (1h)
Etapa 5  →  Reescrever 5 repositories (4-6h)
Etapa 6  →  Migrar dados existentes (1h)
Etapa 7  →  RAG com pgvector + embeddings reais (3-4h)
Etapa 8  →  Limpar SQLite (30 min)
```

**Estimativa total: ~15h de trabalho**, podendo ser feito em 2-3 sessões.
