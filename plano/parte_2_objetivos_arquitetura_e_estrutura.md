# Parte 2 - Objetivos, Arquitetura e Estrutura

## Resumo
Este documento consolida os objetivos da refatoração, a arquitetura alvo do backend e a estrutura de pastas proposta para o projeto migrado.

## Objetivo
Definir a direção técnica da migração para FastAPI, incluindo organização por camadas, módulos esperados e responsabilidades principais do backend.

## Conteúdo consolidado
- A principal motivação da migração é sair de Flask para FastAPI ganhando documentação automática, validação com Pydantic, melhor organização modular e base mais adequada para integrações futuras de IA.
- Os objetivos centrais são: migrar sem quebrar funcionalidades, separar o backend em routers, services e repositories, adicionar schemas para entradas e saídas, preparar endpoints para YouTube Data API e Analytics API, estruturar o projeto para a assistente de IA e manter tudo rodando em localhost.
- A arquitetura alvo organiza o fluxo como: usuário ou dashboard, `app/main.py`, routers, services, repositories, storage e APIs externas.
- O fluxo de geração de vídeo longo deve ficar explícito: geração de roteiro, revisão manual do roteiro, geração de áudio, busca de assets, montagem do vídeo e persistência local.
- O maior ponto de custo atual é TTS. Por isso, o plano exige separar geração de roteiro de geração de áudio para evitar retrabalho.
- A estrutura de pastas alvo inclui `app/core`, `app/routers`, `app/schemas`, `app/services`, `app/repositories`, `app/storage`, `app/utils`, além de `tests/`, `storage/` e arquivos de configuração na raiz.

### Módulos de service esperados (com base no app.py real)
A camada de services precisa cobrir não apenas o que o `plano_melhoria.md` prevê, mas também o que já existe e funciona no Flask:

| Service | Responsabilidade | Base atual no Flask |
|---|---|---|
| `gemini_service.py` | Integração com Gemini API (texto e TTS) | Chamadas diretas a `genai.Client` |
| `audio_service.py` | TTS curto (WAV direto) e TTS longo (chunking + checkpointing + SSE) | `/generate` e `/generate-stream` |
| `video_service.py` | Montagem de vídeo longo via FFmpeg (Ken Burns two-pass) | `/assemble` |
| `short_service.py` | Geração de roteiros de shorts derivados | `/shorts/scriptify` |
| `image_search_service.py` | Busca de imagens e assets externos | Parcialmente no frontend atual |
| `broll_service.py` | Busca e download de B-Roll do archive.org | `/broll/search` e `/broll/download` |
| `media_service.py` | Orquestrador de geração de mídia completa | Coordenação entre os services acima |
| `script_service.py` | Roteirização de URL (newspaper3k + Gemini) e anotação de entonação | `/scriptify` e `/enhance` |
| `youtube_data_service.py` | YouTube Data API (futuro) | Não existe ainda |
| `youtube_analytics_service.py` | YouTube Analytics API (futuro) | Não existe ainda |
| `idea_service.py` | Geração e gestão de ideias (futuro) | Não existe ainda |
| `ai_assistant_service.py` | Assistente com RAG (futuro) | Não existe ainda |

### Comportamentos técnicos que a arquitetura precisa suportar
- **SSE (Server-Sent Events)**: o FastAPI precisa suportar streaming de progresso via `StreamingResponse`.
- **Jobs assíncronos**: a montagem de vídeo roda em background thread com tracking de status e progresso.
- **Checkpointing em disco**: chunks de TTS são salvos em PCM para permitir retomada sem reprocessamento.
- **Detecção de hardware**: identificação automática de NVENC para encoding via GPU.
- **Cleanup de temporários**: rotina em background para remover sessões e jobs antigos.

## Prioridades e decisões
- A refatoração é custo neutro por si só; aumento de custo virá apenas com novas chamadas de IA.
- O padrão arquitetural oficial passa a ser `routers -> services -> repositories`.
- A etapa de aprovação manual do roteiro é obrigatória no desenho do fluxo de mídia.
- O projeto deve nascer preparado para expansão futura, mas sem antecipar implementação de frontend.
- O B-Roll (archive.org) é uma funcionalidade existente e deve ter service próprio, não ser tratado como feature futura.

## Critérios de aceite e pontos de atenção
- A arquitetura proposta deve permitir mapear cada função crítica atual do Flask para um módulo futuro claro.
- A estrutura de pastas deve ser suficiente para suportar mídia, IA, YouTube APIs, B-Roll, storage e persistência local.
- O documento deve deixar explícito que otimização de custo começa na modelagem do fluxo, não apenas no monitoramento.
- A arquitetura deve suportar SSE, jobs assíncronos e checkpointing desde o início, não como adição posterior.
