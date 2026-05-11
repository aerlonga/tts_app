# Parte 3 - Migração Etapa 1: Setup FastAPI

## Resumo
Esta parte cobre a primeira etapa operacional da migração: subir a base FastAPI sem remover o Flask existente.

## Objetivo
Criar a fundação mínima do novo backend, garantindo que FastAPI rode em paralelo ao estado atual e ofereça uma base segura para as próximas migrações.

## Conteúdo consolidado
- Criar `app/main.py` como ponto de entrada FastAPI.
- Criar `app/core/config.py` usando `pydantic-settings` para leitura das variáveis de ambiente.
- Criar o endpoint `GET /health` retornando `{ "status": "ok" }`.
- Garantir que `uvicorn app.main:app --reload` suba sem erros.
- Confirmar que a documentação automática em `/docs` esteja disponível.
- Não remover Flask nesta etapa.

## Prioridades e decisões
- A prioridade aqui é infraestrutura mínima e previsível, não migração de lógica de negócio.
- FastAPI deve coexistir com Flask até haver equivalência suficiente de comportamento.
- Configuração centralizada com `pydantic-settings` passa a ser a base do backend novo.

## Critérios de aceite e pontos de atenção
- `GET /health` responde corretamente.
- `/docs` abre e documenta a aplicação FastAPI.
- O servidor FastAPI sobe localmente sem quebrar o fluxo existente em Flask.
- Esta etapa só termina quando a base nova estiver estável o bastante para receber routers reais.
