# Parte 7 - Migração Etapa 5: YouTube Data API

## Resumo
Esta parte cobre a integração inicial com a YouTube Data API, com foco em coleta local, normalização e cache, sem envolver IA neste primeiro momento.

## Objetivo
Permitir pesquisa de vídeos e canais concorrentes, armazenando dados úteis localmente e preservando quota da API.

## Conteúdo consolidado
- Criar `app/services/youtube_data_service.py`.
- Criar `app/schemas/youtube.py`.
- Criar `app/routers/youtube.py` com:
- `GET /youtube/search`
- `GET /youtube/videos/{video_id}`
- `GET /youtube/channels/{channel_id}`
- Adicionar `YOUTUBE_API_KEY` ao `.env`.
- Salvar resultados no banco antes de qualquer envio para IA.
- Calcular localmente métricas como views por dia, taxa like por view e ordenação por relevância.
- Implementar cache para evitar consumo desnecessário da quota diária da API.
- Nesta etapa, Gemini não deve ser acionado para análise de concorrentes.

## Prioridades e decisões
- Primeiro coletar e organizar dados, depois pensar em análise com IA.
- Apenas os itens mais relevantes devem ser candidatos a etapas futuras com Gemini.
- A quota da YouTube Data API precisa ser tratada como recurso limitado desde a primeira integração.

## Critérios de aceite e pontos de atenção
- Busca por termo retorna lista normalizada.
- Detalhes de vídeo e canal retornam dados consistentes.
- As principais métricas derivadas são calculadas localmente.
- O fluxo usa cache para reduzir repetição e proteger quota.
