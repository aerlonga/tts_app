# Parte 1 - Visão Geral e Estado Atual

## Resumo
Este documento consolida a visão geral do sistema e o estado atual do backend conforme definido em `plano_melhoria.md`. Ele serve como ponto de partida para toda a migração, deixando claro o que já existe, o que precisa ser preservado e qual contexto técnico guia as próximas etapas.

## Objetivo
Registrar o funcionamento atual do sistema e explicitar as capacidades que não podem ser quebradas durante a refatoração de Flask para FastAPI.

## Conteúdo consolidado
- O sistema atual automatiza geração de conteúdo para vídeos longos e shorts, com foco em YouTube e TikTok.
- Hoje ele já usa Gemini para geração de conteúdo e TTS, busca assets externos, monta vídeos localmente e faz upload ou agendamento para plataformas.
- O projeto roda 100% em localhost e continuará assim mesmo após a refatoração.
- O backend atual está concentrado em Flask, com lógica operacional já funcional para áudio, vídeo, shorts e integração com Gemini.
- O roadmap de produto inclui assistente de IA, análise de concorrentes, métricas do próprio canal, RAG, banco vetorial e dashboard local, mas essas capacidades ainda não fazem parte do backend base atual.
- O que já funciona e não pode quebrar: geração de vídeo longo, geração de short, busca de assets, geração de áudio ou narração, integração com Gemini e upload ou agendamento para YouTube e TikTok.

### Rotas existentes no Flask (`app.py`)
As seguintes rotas compõem o backend real e devem ser preservadas ou ter equivalência clara na migração:

| Rota Flask | Método | Descrição |
|---|---|---|
| `/` | GET | Serve interface HTML principal |
| `/enhance` | POST | Anotação de entonação via Gemini (text model) |
| `/generate` | POST | TTS curto — retorna WAV direto |
| `/generate-stream` | POST | TTS longo com chunking, SSE e checkpointing em disco |
| `/scriptify` | POST | Roteirização de URL via newspaper3k + Gemini |
| `/shorts/scriptify` | POST | Geração de shorts derivados do roteiro longo |
| `/assemble` | POST | Montagem de vídeo em background (retorna job_id) |
| `/assemble/status/<id>` | GET | Status e progresso de job de montagem |
| `/assemble/download/<id>` | GET | Download do MP4 finalizado |
| `/broll/search` | POST | Pesquisa B-Roll no archive.org |
| `/broll/download` | POST | Download de clip do archive.org para uso local |

### Funcionalidades técnicas existentes
Além das rotas, o backend atual implementa os seguintes comportamentos que precisam ser preservados:

- **Chunking de TTS**: texto dividido em blocos de até 9500 caracteres com throttling de 62 segundos entre chunks.
- **Checkpointing em disco**: cada chunk de áudio (PCM) é salvo em arquivo; em caso de retomada, chunks já processados são reaproveitados.
- **Session management**: sessões com ID único permitem retomar TTS interrompido.
- **SSE (Server-Sent Events)**: progresso em tempo real para o frontend durante geração de TTS longo.
- **FFmpeg Ken Burns two-pass**: Pass 1 gera clips individuais com efeito zoompan, Pass 2 concatena todos os clips com o áudio.
- **Detecção automática de NVENC**: fallback para libx264 se GPU Nvidia não estiver disponível.
- **Suporte misto imagem + vídeo**: assets podem ser JPG/PNG (recebem Ken Burns) ou MP4/MOV/WebM (trimados e recodificados).
- **Ordenação natural de assets**: sort por padrão "parte 1", "parte 2", etc.
- **Manifest-based asset ordering**: quando presente, o manifesto controla a ordem dos assets na montagem.
- **B-Roll via archive.org**: busca em coleções de domínio público (Prelinger, NASA, National Archives).
- **Cleanup worker**: thread em background que remove diretórios temporários com mais de 2 horas.
- **Parsing tolerante de JSON**: extração de JSON de respostas do Gemini com limpeza de trailing commas e code fences.

## Prioridades e decisões
- A migração deve começar com foco em continuidade operacional, não em redesign amplo.
- O comportamento já validado em Flask é a referência funcional para a camada FastAPI.
- Qualquer nova organização interna deve preservar o fluxo atual antes de adicionar features futuras.
- O backend é a prioridade exclusiva nesta fase; frontend fica fora do escopo.

## Critérios de aceite e pontos de atenção
- O sistema deve conseguir usar esta parte como referência para entender o que existe hoje sem abrir o documento inteiro.
- As funcionalidades críticas que não podem quebrar devem estar claramente listadas.
- As rotas Flask existentes devem estar mapeadas para servir de checklist na migração.
- Nenhum objetivo futuro desta parte deve ser tratado como requisito já implementado.
