# Parte 5 - Migração Etapa 3: Mídia, TTS, Vídeo e Shorts

## Resumo
Esta é a etapa mais crítica da migração funcional, cobrindo a separação da lógica de roteiro, TTS, vídeo, shorts e busca de assets em serviços dedicados.

## Objetivo
Migrar o núcleo operacional do backend atual para FastAPI preservando o comportamento já funcional e reduzindo risco de retrabalho de áudio.

## Conteúdo consolidado
- Criar `audio_service.py`, `video_service.py`, `short_service.py`, `image_search_service.py`, `broll_service.py`, `script_service.py` e `media_service.py`.
- Criar `app/schemas/media.py`.
- Criar `app/routers/media.py` com:
  - `POST /media/generate-script`
  - `POST /media/generate-video`
  - `POST /media/generate-short`
  - `POST /media/search-assets`
  - `POST /media/enhance` (migração de `/enhance`)
  - `POST /media/generate-tts` (migração de `/generate`)
  - `POST /media/generate-tts-stream` (migração de `/generate-stream`)
  - `POST /media/assemble` (migração de `/assemble`)
  - `GET /media/assemble/status/{job_id}` (migração de `/assemble/status/<id>`)
  - `GET /media/assemble/download/{job_id}` (migração de `/assemble/download/<id>`)
- Criar `app/routers/broll.py` com:
  - `POST /broll/search` (migração de `/broll/search`)
  - `POST /broll/download` (migração de `/broll/download`)
- Criar `app/storage/local_storage.py`.
- O fluxo recomendado passa a ser: gerar roteiro, revisar manualmente, aprovar, gerar áudio, buscar assets, montar vídeo.
- A etapa deve preservar os comportamentos hoje concentrados em Flask, incluindo TTS curto, TTS com chunking e checkpointing, roteirização por URL, geração de shorts derivados, montagem de vídeo e busca de assets.

### Mapeamento de rotas Flask → FastAPI

| Rota Flask | Rota FastAPI | Service responsável |
|---|---|---|
| `POST /enhance` | `POST /media/enhance` | `script_service.py` |
| `POST /generate` | `POST /media/generate-tts` | `audio_service.py` |
| `POST /generate-stream` | `POST /media/generate-tts-stream` | `audio_service.py` |
| `POST /scriptify` | `POST /media/generate-script` | `script_service.py` |
| `POST /shorts/scriptify` | `POST /media/generate-short` | `short_service.py` |
| `POST /assemble` | `POST /media/assemble` | `video_service.py` |
| `GET /assemble/status/<id>` | `GET /media/assemble/status/{job_id}` | `video_service.py` |
| `GET /assemble/download/<id>` | `GET /media/assemble/download/{job_id}` | `video_service.py` |
| `POST /broll/search` | `POST /broll/search` | `broll_service.py` |
| `POST /broll/download` | `POST /broll/download` | `broll_service.py` |

## Prioridades e decisões
- Separar `generate-script` de `generate-video` é decisão obrigatória para proteger custo de TTS.
- O novo desenho deve preservar SSE, chunking, checkpointing em disco, parsing tolerante de JSON, ordenação natural de assets e jobs assíncronos de montagem.
- A etapa deve favorecer equivalência funcional antes de otimizações internas mais profundas.
- O B-Roll (archive.org) é funcionalidade existente e deve ser migrado nesta etapa, não postergado.
- O `/enhance` (anotação de entonação) é funcionalidade existente e deve ser preservado.

## Critérios de aceite e pontos de atenção
- Geração de vídeo longo funciona do início ao fim.
- Geração de short funciona do início ao fim.
- Roteiro pode ser gerado sem disparar TTS.
- TTS curto (WAV direto) continua funcionando para textos pequenos.
- TTS longo com chunking, SSE e checkpointing funciona como antes.
- A montagem de vídeo continua suportando status e download por job.
- B-Roll search e download funcionam como antes.
- Anotação de entonação (`/enhance`) funciona como antes.
- Fluxos mais caros ou frágeis, como TTS longo e FFmpeg, precisam de validação extra após a migração.
- Todas as rotas Flask listadas na Parte 1 devem ter equivalência clara nesta etapa.
