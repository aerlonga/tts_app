# Parte 8 - Migração Etapa 6: YouTube Analytics API

## Resumo
Esta parte adiciona acesso autenticado às métricas do próprio canal via YouTube Analytics API.

## Objetivo
Habilitar leitura de métricas reais do canal autorizado, criando a base para análise de performance e decisões assistidas por dados.

## Conteúdo consolidado
- Criar `app/services/youtube_analytics_service.py`.
- Criar `app/schemas/analytics.py`.
- Criar `app/routers/analytics.py` com:
- `GET /analytics/youtube/channel-summary`
- `GET /analytics/youtube/videos`
- `GET /analytics/youtube/videos/{video_id}`
- Implementar fluxo OAuth 2.0 para autorização do canal.
- Armazenar `refresh_token` no `.env` após o primeiro login.
- Cobrir métricas como views, watch time, retenção, CTR e outras disponíveis para o canal autorizado.

## Prioridades e decisões
- Esta integração é diferente da YouTube Data API porque exige autenticação do dono do canal.
- O backend deve tratar ausência de OAuth configurado como erro claro e explicável.
- Tokens de renovação precisam ser preservados com cuidado para evitar reautenticação desnecessária.

## Critérios de aceite e pontos de atenção
- Endpoints retornam métricas reais quando OAuth estiver configurado.
- Quando OAuth não estiver configurado, a resposta deve indicar o problema com clareza.
- O fluxo de renovação de acesso deve depender do `refresh_token`, não de login manual recorrente.
