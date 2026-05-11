# Parte 12 - Custos, Riscos e Operação Local

## Resumo
Esta parte consolida o plano operacional do backend em localhost, o controle de custo de IA e os principais riscos da migração.

## Objetivo
Garantir que a evolução do backend mantenha visibilidade de custo, previsibilidade operacional e mitigação dos riscos mais sensíveis.

## Conteúdo consolidado

### Operação local
- O backend continua rodando 100% em localhost.
- Requisitos: Python 3.11+, pip, Git, (opcional) Ollama para modelos locais.
- Fluxo de instalação: clonar repo, criar venv, instalar dependências, configurar `.env`, criar pastas de storage, subir com `uvicorn`.
- Acesso: `/docs` (Swagger), `/redoc`, `/health`, `/usage/summary`.

### requirements.txt sugerido (conforme plano_melhoria.md)
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

### Controle de custo de IA
- O controle deve registrar feature, provider, model, tokens e custo estimado por chamada.
- Features a rastrear separadamente: `video_script_generation`, `tts_generation`, `idea_generation`, `competitor_analysis`, `title_generation`, `description_generation`, `short_script_generation`, `thumbnail_analysis` (futuro).
- A maior fonte de custo continua sendo TTS e seu retrabalho.
- Endpoint principal: `GET /usage/summary` com detalhamento por feature via `GET /usage/by-feature`.

### Projeção de custo estimado

| Cenário | Estimativa mensal |
|---|---|
| Só FastAPI + organização (sem novos features) | R$ 45–50 |
| Ideias 1x/dia com cache ativo | R$ 50–60 |
| Ideias + análise de concorrentes 1x/dia (top 10) | R$ 63–78 |
| Assistente usada várias vezes ao dia | R$ 100–150 |

> O principal fator de variação é o retrabalho de áudio (TTS), não o texto.

### Riscos da migração

| Risco | Nível | Mitigação |
|---|---|---|
| Quebrar geração de vídeo | 🔴 Alto | Migrar em etapas, testar cada service |
| Retrabalho de áudio multiplicando custo | 🔴 Alto | Separar `generate-script` de `generate-video` |
| Perder configurações do .env | 🟡 Médio | Usar `.env.example`, validar via pydantic-settings |
| Paths de arquivo quebrados | 🟡 Médio | Testar local_storage com caminhos absolutos e relativos |
| Comportamento do Gemini mudando | 🟡 Médio | Isolar em service e testar com prompt fixo |
| OAuth YouTube exigir re-auth | 🟡 Médio | Documentar passo a passo, salvar refresh_token |
| Ollama gerando resultado ruim em PT | 🟡 Médio | Testar com volume pequeno antes do roteamento |
| Custo de IA subindo sem visibilidade | 🟡 Médio | Implementar `ai_usage_logs` desde Etapa 2 |

### Quota da YouTube Data API
- 10.000 unidades por dia (gratuita).
- `search.list`: 100 unidades por chamada.
- `videos.list`: 1 unidade por chamada.
- Proteger com cache local e coleta criteriosa.

## Prioridades e decisões
- Log de custo entra cedo para evitar cegueira operacional.
- A operação local é requisito permanente, não estágio provisório.
- Riscos ligados a mídia e áudio merecem validação adicional em cada etapa.
- Ollama só deve entrar em produção depois de validação real de qualidade em português.

## Critérios de aceite
- O backend deve continuar simples de rodar localmente.
- Deve haver clareza sobre onde o custo cresce e como será observado.
- Os principais riscos devem estar vinculados a ações práticas de mitigação.
- A projeção de custo deve ser consultável como referência para decisões de escopo.
