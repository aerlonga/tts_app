# Parte 13 - Pendências, TODOs e Notas Finais

## Resumo
Esta parte reúne os itens pendentes, próximos passos de backend e notas finais de estudo presentes no plano original.

## Objetivo
Fechar o material dividido com uma visão clara do que ainda precisa ser feito no curto, médio e longo prazo, além do caminho de aprendizado sugerido.

## Conteúdo consolidado

### Pendências imediatas
- [ ] Analisar o código Flask atual e listar rotas existentes ← **feito na Parte 1**
- [ ] Listar serviços externos usados (Gemini API, archive.org)
- [ ] Listar variáveis de ambiente existentes
- [ ] Completar `.env.example`
- [ ] Subir estrutura FastAPI básica (Etapas 1 e 2)
- [ ] Criar `ai_usage_logs` já no início

### Curto prazo
- [ ] Migrar services com separação de roteiro e vídeo
- [ ] Migrar todos os endpoints existentes (ver mapeamento na Parte 11)
- [ ] Adicionar YouTube Data API sem IA
- [ ] Criar banco local com tabelas principais
- [ ] Salvar vídeos publicados automaticamente
- [ ] Implementar cache de ideias

### Médio prazo
- [ ] Integrar YouTube Analytics API com OAuth
- [ ] Criar dashboard local simples
- [ ] Adicionar scheduler local para publicação
- [ ] Coletar métricas automaticamente

### Longo prazo
- [ ] Embeddings e banco vetorial
- [ ] Assistente com RAG completo
- [ ] Validação de Ollama em português
- [ ] Roteamento híbrido local versus Gemini
- [ ] Eventual fine-tuning para tarefas específicas

### Caminho de aprendizado sugerido
1. Python para backend e automação ← já tem
2. FastAPI + Pydantic ← essa refatoração
3. APIs REST e httpx ← essa refatoração
4. LLM APIs (Gemini, OpenAI, etc.) ← já tem
5. RAG com embeddings ← próximo passo de estudo
6. Banco vetorial (ChromaDB) ← junto com RAG
7. Ollama e modelos locais ← já pode começar (testar em PT)
8. Agentes e function calling ← depois do RAG
9. Fine-tuning básico ← longo prazo
10. MLOps e monitoramento ← longo prazo

### Perfil técnico-alvo
Backend developer evoluindo para AI engineer aplicado — combinando engenharia de software com IA generativa em produto real.

## Prioridades e decisões
- Os itens imediatos e de curto prazo são os que destravam a migração real do backend.
- O restante deve ser tratado como evolução progressiva, não pré-requisito para concluir a base FastAPI.
- O plano de aprendizado acompanha o projeto, mas não substitui entregas concretas de engenharia.
- As funcionalidades adjacentes ao projeto principal (ex: Trello/marketing, flask-login) são independentes do escopo desta migração e não devem bloquear nem ser confundidas com requisitos da refatoração FastAPI.

## Critérios de aceite
- Esta parte funciona como checklist estratégico do que vem depois da divisão do plano.
- Itens de aprendizado não devem ser confundidos com requisitos obrigatórios da primeira migração.
- As pendências continuam coerentes com a ordem técnica definida nas partes anteriores.
- A referência de rotas existentes (Parte 1) e mapeamento de endpoints (Parte 11) devem estar sempre atualizados conforme o app.py real.
