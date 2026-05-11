# Parte 4 - Migração Etapa 2: Gemini e Usage

## Resumo
Esta parte trata da extração da integração com Gemini para uma camada de service e da criação antecipada de rastreamento de custo e uso de IA.

## Objetivo
Isolar a comunicação com Gemini desde o começo da migração e garantir visibilidade de custo por feature antes de expandir o backend.

## Conteúdo consolidado
- Criar `app/services/gemini_service.py`.
- Mover para esse service toda a lógica de chamada à API Gemini.
- Criar `app/schemas/ai.py` com modelos Pydantic de entrada e saída.
- Criar `app/routers/ai.py` com `POST /ai/generate`.
- Criar `app/repositories/ai_usage_repository.py` para registrar chamadas de IA.
- Validar que a resposta produzida pelo novo endpoint mantenha equivalência com o comportamento anterior.
- O log de uso deve registrar feature, provider, model, tokens e custo estimado desde esta etapa.

## Prioridades e decisões
- Controle de custo começa aqui, não depois.
- A integração com Gemini precisa ficar isolada o suficiente para suportar futura troca de modelo, ajuste de prompts e eventual roteamento híbrido.
- O log de uso é requisito estrutural do backend, não feature opcional.

## Critérios de aceite e pontos de atenção
- `POST /ai/generate` retorna resposta válida do Gemini.
- Toda chamada via novo fluxo registra uso em `ai_usage_logs`.
- A migração não deve alterar comportamento sem necessidade nesta fase.
- Erros da API externa precisam ter tratamento claro no service e no router.
