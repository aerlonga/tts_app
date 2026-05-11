# Parte 6 - Migração Etapa 4: Ideias com Cache

## Resumo
Esta parte introduz o módulo de geração de ideias com cache local para reduzir chamadas repetidas ao Gemini.

## Objetivo
Criar uma feature de geração de ideias reutilizável, estruturada e com controle de custo por reaproveitamento diário.

## Conteúdo consolidado
- Criar `app/services/idea_service.py`.
- Criar `app/schemas/ideas.py`.
- Criar `app/routers/ideas.py` com `POST /ideas/generate`.
- Criar `app/repositories/idea_repository.py`.
- Configurar SQLite local como base inicial da feature.
- Implementar cache: se o mesmo tema já gerou ideias no mesmo dia, reutilizar os dados salvos.
- Adicionar `force=true` para permitir regeneração manual ignorando cache.
- A resposta deve retornar ideias estruturadas com metadados úteis para backend e uso futuro.

## Prioridades e decisões
- A lógica de cache é parte central da feature, não melhoria posterior.
- O banco local é suficiente para a primeira versão.
- O desenho deve favorecer persistência reutilizável para assistente futura e análises posteriores.

## Critérios de aceite e pontos de atenção
- `POST /ideas/generate` retorna lista estruturada de ideias.
- Requisições repetidas para o mesmo tema no mesmo dia reutilizam cache quando `force=false`.
- `force=true` ignora cache e gera novamente.
- Chamadas redundantes ao Gemini devem cair de forma mensurável nesta etapa.
