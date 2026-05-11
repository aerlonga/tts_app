# Parte 10 - Migração Etapa 8: Assistente IA com RAG

## Resumo
Esta parte documenta a evolução futura do backend para uma assistente de IA com memória, ferramentas e roteamento entre provedores.

## Objetivo
Planejar a camada de assistente sem antecipar sua implementação antes de a base de backend, persistência e integrações estar estável.

## Conteúdo consolidado
- Criar `app/services/ai_assistant_service.py`.
- Adicionar embeddings para ideias, roteiros, referências e dados relevantes.
- Configurar banco vetorial, com ChromaDB ou alternativa equivalente.
- Criar `POST /ai/assistant`.
- Integrar Ollama para tarefas simples, mantendo Gemini para tarefas estratégicas.
- Implementar roteamento baseado em tipo de tarefa.
- A assistente futura deve operar com ferramentas como consulta de vídeos publicados, métricas do canal, busca de concorrentes, busca de ideias anteriores e geração de novas sugestões.
- O RAG deve usar contexto salvo localmente, não treino de modelo, para recuperar histórico útil do projeto.

## Prioridades e decisões
- Esta etapa é explicitamente futura; não deve atrasar a migração do backend base.
- Modelos locais em português precisam ser validados antes de confiança operacional.
- Fine-tuning não substitui RAG e não é prioridade nesta fase.

## Critérios de aceite e pontos de atenção
- O plano da assistente deve depender de banco relacional, banco vetorial e integrações já existentes.
- O roteamento Gemini versus Ollama deve ser tratado como decisão de qualidade e custo.
- O risco principal é retrabalho causado por baixa qualidade de modelos locais em português.
