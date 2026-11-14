# Trilha 07 — RAG e Arquitetura de Agentes

## Objetivo da Trilha
Capacitar o engenheiro de software e de IA a projetar, implementar e operar sistemas de Geração Aumentada por Recuperação (*Retrieval-Augmented Generation* — RAG) e arquiteturas baseadas em fluxos de trabalho determinísticos e agentes autônomos em produção. A trilha aborda desde o pipeline de ingestão, particionamento (*chunking*), indexação incremental e busca vetorial/híbrida até a construção de grafos de estado cíclicos, engenharia de interfaces de ferramentas (*Agent-Computer Interface*), controle de concorrência, *guardrails*, roteamento de modelos e observabilidade ponta a ponta.

## Pré-requisitos Recomendados
- **Trilha 01 — Fundamentos de Engenharia e Ciência da Computação:** Estruturas de dados, algoritmos de grafos, complexidade assintótica e concorrência.
- **Trilha 04 — Arquitetura de Software, Dados e Sistemas Distribuídos:** Bancos de dados relacionais e não relacionais, *caching*, mensageria e resiliência em chamadas de rede.
- **Trilha 05 — Engenharia de Machine Learning e Deep Learning:** Álgebra linear aplicada, espaços vetoriais, métricas de distância/similaridade e arquiteturas *Transformer*.
- **Trilha 06 — LLMs, Prompt Engineering e Avaliação:** Tokenização, modelos de *embeddings* densos, estruturação determinística de saídas (*JSON Schema* / *Function Calling*) e avaliação automatizada (*LLM-as-a-Judge*).

---

## Sequência de Aulas

| Ordem | Arquivo | Título da Aula | Tópicos-Chave |
| :--- | :--- | :--- | :--- |
| **01** | `01-indexacao-chunking-e-bancos-de-dados-vetoriais.md` | Indexação, Chunking e Bancos de Dados Vetoriais | Ingestão documental; particionamento recursivo, por tokens e sensível à sintaxe; *Contextual Retrieval*; indexação multi-representação (`MultiVectorRetriever`, RAPTOR e *late interaction* com ColBERTv2); sincronização incremental com `RecordManager`; algoritmos *k-NN* exato vs. *ANN* (HNSW, IVF, PQ, LSH) em `FAISS`, `PGVector` e `Pinecone`. |
| **02** | `02-arquitetura-rag-em-producao-e-avaliacao-de-recuperacao.md` | Arquitetura RAG em Produção e Avaliação de Recuperação | Recuperação léxica (índice invertido, TF-IDF, Okapi BM25) vs. densa e esparsa aprendida (SPLADE); *Hybrid Search* com *Reciprocal Rank Fusion* (RRF) e *reranking* via *Cross-Encoders*; transformação de consultas (*Rewrite*, *Multi-Query*, *RAG-Fusion*, *HyDE*); roteamento lógico/semântico, *Self-Querying* e *Text-to-SQL*; geração fundamentada e métricas de avaliação (`Context Precision`, `Context Recall`, `NDCG`, `MRR`, `MAP`, `Faithfulness` e `Answer Relevance`). |
| **03** | `03-workflows-deterministicos-vs-agentes-autonomos.md` | Workflows Determinísticos vs. Agentes Autônomos | Fronteira de Pareto entre agência e confiabilidade; probabilidade de erro composto em múltiplas etapas; hierarquia de arquiteturas cognitivas; padrões de *workflows* determinísticos (*Prompt Chaining*, *Routing*, *Parallelization*, *Orchestrator-Workers*, *Evaluator-Optimizer* e *Document Chains*) vs. agentes autônomos (*ReAct*, *Plan-and-Execute*, *Reflexion* e *Tree of Thoughts*); desacoplamento entre planejamento, validação e execução. |
| **04** | `04-grafos-de-estado-ferramentas-e-observabilidade-de-agentes.md` | Grafos de Estado, Ferramentas e Observabilidade de Agentes | Orquestração cíclica com `LangGraph` (`StateGraph`, esquemas tipados, *reducers*, *checkpointers* e gestão de memória de curto e longo prazo); subgrafos e topologias multiagentes (*Supervisor*, *Hierarchical*, *Network*); engenharia de *Agent-Computer Interface* (ACI), pré-seleção vetorial de ferramentas e *Human-in-the-Loop*; arquitetura de produção (*Model Gateway*, *caches* exato e semântico, *guardrails* de entrada/saída com dicionário reverso de PII) e observabilidade (*Traces*, métricas operacionais, detecção de *drift* e sinais de *feedback*). |

---

## Como Estudar esta Trilha
1. **Ordem estrita de execução:** As aulas foram estruturadas em progressão cumulativa. A camada de recuperação de dados (Aulas 01 e 02) constitui a base de aumento de contexto consumida como ferramenta pelos fluxos de trabalho e agentes autônomos (Aulas 03 e 04).
2. **Implementação guiada por critérios de engenharia:** Ao estudar cada padrão (como *RAG-Fusion*, *Hybrid Search* ou ciclos multiagentes), avalie sistematicamente o impacto em latência (*Time to First Token* e latência total), consumo de tokens e taxa de falha composta descritos na seção **3. Critério de Decisão** de cada aula.
3. **Consulta às fontes primárias:** Utilize o arquivo `referencias.md` desta trilha para localizar os capítulos e páginas exatas nos livros-base e na documentação técnica, incluindo os capítulos reservados para consulta avançada sobre implantação proprietária.
