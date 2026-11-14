# Referências Bibliográficas — Trilha 07: RAG e Arquitetura de Agentes

Este documento consolida todas as fontes primárias utilizadas na construção das Aulas `01` a `04` da **Trilha 07 (`07-rag-e-arquitetura-de-agentes`)**, mapeando os capítulos e páginas exatos dos livros-base processados no acervo e as referências técnicas oficiais de engenharia de agentes e recuperação de informação, além de registrar os capítulos reservados para consulta avançada fora das aulas.

---

## 1. Livros-Base Utilizados nas Aulas

1. **OSHIN, Mayo; CAMPOS, Nuno.** *Learning LangChain: Building AI and LLM Applications with LangChain and LangGraph*. 1ª Edição. Sebastopol: O'Reilly Media, Fevereiro de 2025. ISBN 978-1-098-16728-8.
   - **Capítulos integrados nas aulas:**
     - **Capítulo 1 — *LLM Fundamentals with LangChain* (pp. 1–22):** Interface `Runnable`, métodos `invoke`, `batch`, `stream` e composição declarativa (LCEL) vs. imperativa (`@chain`) (Aulas 01, 02 e 03).
     - **Capítulo 2 — *RAG Part I: Indexing Your Data* (pp. 23–56):** *Document Loaders*, `RecursiveCharacterTextSplitter`, *embeddings*, `PGVector`, sincronização incremental via `SQLRecordManager` e `index()`, `MultiVectorRetriever`, RAPTOR e ColBERTv2 (Aula 01).
     - **Capítulo 3 — *RAG Part II: Chatting with Your Data* (pp. 57–93):** *Rewrite-Retrieve-Read*, *Multi-Query Retrieval*, *RAG-Fusion* (RRF), *HyDE*, roteamento lógico e semântico, `SelfQueryRetriever` e *Text-to-SQL* (Aula 02).
     - **Capítulo 4 — *Using LangGraph to Add Memory to Your Chatbot* (pp. 95–114):** `StateGraph`, esquemas de estado tipados, funções redutoras (`add_messages`), *checkpointers* (`MemorySaver`, `PostgresSaver`), `thread_id` e higiene de histórico (`trim_messages`, `filter_messages`, `merge_message_runs`) (Aula 04).
     - **Capítulo 5 — *Cognitive Architectures with LangGraph* (pp. 115–133):** Hierarquia de arquiteturas cognitivas (Código $\to$ Chamada Única $\to$ Cadeia $\to$ Roteador $\to$ Máquina de Estados) e o *trade-off* entre agência e confiabilidade (Aula 03).
     - **Capítulo 6 — *Agent Architecture* (pp. 135–153):** Ciclo *Plan-Do* e *ReAct* no LangGraph (`ToolNode`, `tools_condition`), *Always Calling a Tool First* e pré-seleção vetorial dinâmica para catálogos extensos de ferramentas (Aulas 03 e 04).
     - **Capítulo 7 — *Agents II* (pp. 155–170):** Ciclos de *Reflection* (`generate` $\leftrightarrow$ `reflect`), composição de subgrafos com estados compartilhados ou isolados e arquiteturas multiagentes (*Supervisor*, *Hierarchical*, *Network*) (Aulas 03 e 04).
     - **Capítulo 8 — *Patterns to Make the Most of LLMs* (pp. 171–189):** Fronteira de Pareto entre agência e confiabilidade, modos de *streaming* (`updates`, `values`, `debug`, `astream_events`), controles *Human-in-the-Loop* (`interrupt_before`, `update_state`, *fork/time-travel*) e estratégias de concorrência/multitarefa (Aulas 03 e 04).

2. **HUYEN, Chip.** *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, Janeiro de 2025. ISBN 978-1-098-16630-4.
   - **Capítulos integrados nas aulas:**
     - **Capítulo 6 — *RAG and Agents* (pp. 253–306):** Recuperação léxica (índice invertido, TF-IDF, Okapi BM25) vs. vetorial densa e esparsa aprendida (SPLADE), algoritmos *k-NN* e *ANN* (HNSW, IVF, PQ, LSH, Annoy), *Hybrid Search* com RRF, *reranking* e posicionamento em formato de U, *Contextual Retrieval*, métricas de recuperação (`Context Precision`, `Context Recall`, `NDCG`, `MRR`, `MAP`), matemática do erro composto em agentes ($p^N$), desacoplamento entre geração/validação de plano e execução, taxonomia de falhas de planejamento/ferramentas, estudos de ablação e sistemas de memória (Aulas 01, 02, 03 e 04).
     - **Capítulo 10 — *AI Engineering Architecture and User Feedback* (pp. 449–494):** Arquitetura progressiva de engenharia de IA, *Input/Output Guardrails* (mascaramento de PII com dicionário reverso e proteção contra injeção de prompt), *Model Router* e *Model Gateway*, *Exact Cache* vs. *Semantic Cache*, observabilidade (*Logs* vs. *Traces*, MTTD, MTTR, CFR, TTFT, TPOT, TPS, detecção de *drift*) e sinais explícitos/implícitos de *feedback* conversacional (Aula 04).

3. **ALAMMAR, Jay; GROOTENDORST, Maarten.** *Hands-On Large Language Models: Language Understanding and Generation*. 1ª Edição. Sebastopol: O'Reilly Media, Outubro de 2024. ISBN 978-1-098-15096-9.
   - **Capítulos integrados nas aulas:**
     - **Capítulo 7 — *Advanced Text Generation Techniques and Tools* (seção *Agents: Creating a System of LLMs*, pp. 216–224):** Estruturação do ciclo *ReAct* (*Thought*, *Action*, *Action Input*, *Observation*) com ferramentas de busca e cálculo (Aula 03).
     - **Capítulo 8 — *Semantic Search and Retrieval-Augmented Generation* (pp. 225–258):** Busca semântica densa, *chunking* de textos longos (um vetor por documento vs. múltiplos vetores com sobreposição), *reranking* em dois estágios com *Cross-Encoders* (*monoBERT*), cálculo passo a passo de *Mean Average Precision* (MAP) e *nDCG*, geração fundamentada com citações (*Citation Recall* e *Citation Precision*) e avaliação automatizada com *Ragas* (*Faithfulness* e *Answer Relevance*) (Aulas 01 e 02).

4. **PHOENIX, James; TAYLOR, Mike.** *Prompt Engineering for Generative AI: Future-Proof Inputs for Reliable AI Outputs*. 1ª Edição. Sebastopol: O'Reilly Media, Maio de 2024. ISBN 978-1-098-15343-4.
   - **Capítulos integrados nas aulas:**
     - **Capítulo 4 — *Advanced Techniques for Text Generation with LangChain* (pp. 125–184):** *Document Loaders*, *Text Splitters* (`CharacterTextSplitter`, `TokenTextSplitter`, `RecursiveCharacterTextSplitter`), decomposição de tarefas, encadeamento sequencial e paralelo em LCEL (`RunnableParallel`, `RunnablePassthrough`, `itemgetter`) e cadeias de documentos (*Stuff*, *Refine*, *Map-Reduce* e *Map Re-rank*) (Aulas 01 e 03).
     - **Capítulo 5 — *Vector Databases with FAISS and Pinecone* (pp. 185–222):** Indexação local com `FAISS` (`IndexFlatL2`, persistência em disco e fusão de índices), bancos vetoriais gerenciados com `Pinecone` (*serverless*, *upsert* em lotes com *retry* e filtragem de metadados), `SelfQueryRetriever` com `AttributeInfo` e mecanismos alternativos (`ContextualCompressionRetriever`, `EnsembleRetriever`, `ParentDocumentRetriever`, `TimeWeightedVectorStoreRetriever`) (Aulas 01 e 02).
     - **Capítulo 6 — *Autonomous Agents with Memory and Tools* (pp. 223–266):** Comparação entre *ReAct* e *OpenAI Function/Tool Calling*, `StructuredTool` com validação `args_schema`, *Agent Toolkits* (CSV e SQL), arquiteturas *Plan-and-Execute* (*BabyAGI*) e *Tree of Thoughts* (ToT), sistemas de memória (`ConversationBufferWindowMemory`, `ConversationSummaryBufferMemory`, `ConversationTokenBufferMemory`, `MongoDBChatMessageHistory`) e instrumentação de *Callbacks* (`BaseCallbackHandler`, `get_openai_callback`) (Aulas 03 e 04).

---

## 2. Documentação Oficial e Artigos Técnicos Integrados

- **ANTHROPIC.** *Building Effective Agents*. Anthropic Research (Erik Schluntz & Barry Zhang), Dezembro de 2024. Disponível em: `https://www.anthropic.com/research/building-effective-agents`.
  - **Escopo utilizado:** Distinção arquitetural entre *Workflows* e *Agents*, os cinco padrões fundamentais de fluxos de trabalho (*Prompt Chaining*, *Routing*, *Parallelization* [*Sectioning* & *Voting*], *Orchestrator-Workers* e *Evaluator-Optimizer*) e os princípios de engenharia de *Agent-Computer Interface* (ACI) e design *poka-yoke* de ferramentas (Aulas 03 e 04).
- **OPENAI.** *OpenAI Cookbook: Examples and Guides for Using the OpenAI API*. Disponível em: `https://cookbook.openai.com/`.
  - **Escopo utilizado:** Práticas recomendadas de *chunking* e contagem de tokens com `tiktoken`, busca vetorial e híbrida, chamadas paralelas e estruturadas de funções (*Tool Calling*), orquestração de múltiplos agentes e guardrails de validação em produção (Aulas 01, 02, 03 e 04).

---

## 3. Capítulos Reservados para Consulta Avançada Fora das Aulas

Conforme as diretrizes curriculares da fábrica, os capítulos abaixo tratam de recursos específicos de plataformas comerciais proprietárias ou tópicos visuais/multimodais complementares e ficam registrados como referência de consulta avançada fora do escopo das aulas regulares:

- **OSHIN, Mayo; CAMPOS, Nuno.** *Learning LangChain: Building AI and LLM Applications with LangChain and LangGraph* (O'Reilly, 2025):
  - **Capítulo 9 — *Deployment: Launching Your AI Application into Production* (pp. 191–214):** Implantação gerenciada na plataforma comercial *LangGraph Platform* (*LangGraph Cloud* API, configuração de `langgraph.json`, assistentes hospedados e integração com *LangGraph Studio*).
  - **Capítulo 10 — *Testing: Evaluation, Monitoring, and Continuous Improvement* (pp. 215–250):** Operação detalhada da interface proprietária *LangSmith* para gestão visual de conjuntos de dados, *tracing* hospedado e painéis de monitoramento específicos da plataforma.
  - **Capítulo 11 — *Building with LLMs* (pp. 251–258):** Panorama de produtos comerciais e evolução do ecossistema LangChain.
- **ALAMMAR, Jay; GROOTENDORST, Maarten.** *Hands-On Large Language Models* (O'Reilly, 2024):
  - **Capítulo 9 — *Multimodal Large Language Models* (pp. 259–286):** *Vision Transformers* (ViT), alinhamento contrastivo texto-imagem via CLIP/OpenCLIP e arquiteturas de ponte visão-linguagem (*Q-Former* no BLIP-2).
- **PHOENIX, James; TAYLOR, Mike.** *Prompt Engineering for Generative AI* (O'Reilly, 2024):
  - **Capítulo 7 a Capítulo 9 (pp. 267–366):** Geração e edição de imagens por difusão (*Midjourney*, *Stable Diffusion*, *ControlNet*).
  - **Capítulo 10 — *Building AI-Powered Applications* (pp. 367–390):** Estudo de caso complementar de construção de linha de comando e extensão de navegador para redação de blog.
