# Aula 01 — Visão Geral do Curso, Trilhas e Protocolo de Estudo

> **Fonte(s) desta aula:**
> - Documentação Interna do Curso: `trilhas/00-grade-curricular.md` (Grade Curricular Oficial — Diretoria de Análise de Dados da ITAJr).
> - Documentação Interna do Curso: `README.md` e `.agent/instrucoes-tutor.md` (Protocolo Operacional do Tutor Socrático — `PROFESSOR_IA`).
> - Índices das Trilhas Técnicas (`00-indice.md`): Trilhas `01` a `07` em `trilhas/`.

---

## 1. Problema e Definição

A atuação técnica na Diretoria de Análise de Dados da ITAJr exige domínio integrado de manipulação de dados, engenharia de software assistida por IA, estatística inferencial, arquitetura de dados, Machine Learning e sistemas baseados em LLMs. O estudo fragmentado por tutoriais isolados gera lacunas operacionais graves: membros tentam construir agentes de IA sem dominar validação de esquemas em Python, implementam modelos preditivos sem prevenir vazamento de dados (*data leakage*) ou entregam análises sem rigor estatístico.

Para eliminar essas lacunas, o programa `PROFESSOR_IA` organiza a capacitação em uma grade sequencial auditada composta por **33 aulas**: esta **aula inaugural** (Módulo `00`) seguida por **7 trilhas técnicas** (`01` a `07`, totalizando **32 aulas técnicas**). Cada aula foi projetada para ser concluída em **15 a 25 minutos de estudo** e segue uma estrutura fixa de quatro seções: **Problema e Definição**, **Aplicação Prática**, **Critério de Decisão** e **Erros Comuns**.

O modelo pedagógico utilizado pelo agente nas **7 trilhas técnicas (`01` a `07`)** é o **ensino socrático por blocos** (enquanto esta aula inaugural `00` é **exclusivamente expositiva e não contém perguntas**):

1. O tutor divide a aula técnica em 3 a 5 blocos curtos e objetivos.
2. Ao final de cada bloco, formula 1 ou 2 perguntas de verificação conceitual ou prática sobre raciocínio técnico, interpretação de resultados e escolha de ferramentas.
3. Se o aluno errar ou der uma resposta incompleta, o tutor corrige o equívoco, completa diretamente o que faltou e segue com a aula para o bloco seguinte (sem repetir a mesma pergunta nem exigir nova tentativa).

Além do formato das aulas, há uma restrição operacional crítica de engenharia de contexto: **toda aula deve ser realizada em um chat novo**. Conversas longas que acumulam múltiplas aulas saturam e poluem a janela de contexto do modelo de linguagem. Quando isso ocorre, instruções antigas perdem prioridade de atenção, trechos de código de aulas anteriores interferem nas perguntas da aula atual e a avaliação socrática perde precisão. Por essa razão, cada sessão de chat executa **estritamente uma única aula**, do diagnóstico inicial até a sincronização do progresso na nuvem.

---

## 2. Aplicação Prática

### Panorama das 7 Trilhas Técnicas e Conteúdos

A grade curricular foi ordenada por dependências técnicas acumulativas. A tabela abaixo resume todas as trilhas que você percorrerá após concluir esta aula inaugural:

| Trilha | Título | Aulas | Conteúdos Principais |
| :--- | :--- | :---: | :--- |
| **01** | **Python e Manipulação de Dados** | 7 | Estruturas nativas (`list`, `tuple`, `dict`, `set`), referências, geradores e `Type Hints`; vetorização com NumPy (`ndarray`) e `pandas` (`.loc`/`.iloc`); ingestão (CSV, JSON, Parquet), limpeza e junções (`merge`, `concat`, `melt`); agregações (`groupby`, `agg`, `transform`) e séries temporais (`resample`, `rolling`); APIs HTTP com `httpx`, `Pydantic` e `FastAPI`; apps com `Streamlit`; versionamento e Pull Requests com Git e GitHub. |
| **02** | **Engenharia de Software Assistida por IA** | 3 | Engenharia orientada a especificação versus *vibe coding*, problema dos 70% e regras persistentes (`GEMINI.md`, `CLAUDE.md`, `AGENTS.md`); ciclo *Plan-Execute-Verify-Report* (Google Antigravity, Claude Code e OpenAI Codex) e higiene de contexto; auditoria de segurança (SQL Injection, segredos, autorização) e testes com `pytest`. |
| **03** | **SQL, Estatística e Storytelling com Dados** | 5 | Consultas analíticas SQL (*row-store* vs. *column-store*, ordem lógica de avaliação, `CASE`, `COALESCE`, `GROUPING SETS`, CTEs); *Window Functions* (`PARTITION BY`, `LAG`), séries temporais e coortes (retenção e LTV); análise exploratória, estimadores robustos (mediana, IQR, MAD), Teorema Central do Limite e *Bootstrap*; testes A/B (permutação, Welch, Qui-Quadrado, *p-value*, poder estatístico, MDE); visualização executiva, Gestalt e storytelling. |
| **04** | **Engenharia e Arquitetura de Dados** | 4 | Ciclo de vida da engenharia de dados, confiabilidade (RTO/RPO), latência e padrões (*Data Warehouse*, *Data Lake*, *Lakehouse* Bronze-Silver-Gold, *Lambda*, *Kappa*, *Data Mesh*); armazenamento OLTP (*B-Trees*, *LSM-Trees*) vs. OLAP colunar (Parquet, Arrow, Delta Lake, Iceberg) e modelagem (Inmon, Kimball/*Star Schema*, SCDs, *Data Vault*, OBT); ingestão *batch* e *streaming* (CDC, Kafka, *Event Time*, *watermarks*, idempotência, DLQs); ELT, junções distribuídas, atualização física (`MERGE`, WAP), qualidade e entrega (*Semantic Layer*, *Feature Stores*, *Reverse ETL*). |
| **05** | **Machine Learning e Sistemas em Produção** | 5 | Critérios ML vs. heurísticas, alinhamento com métricas de negócio, curadoria/anotação e desbalanceamento; *feature engineering* (MCAR/MAR/MNAR, escalonamento, *One-Hot*, *Feature Hashing*) e prevenção de *data leakage* (`Pipeline`, `ColumnTransformer`); modelos supervisionados (OLS, *Ridge*/*Lasso*, Regressão Logística, SVM, CART) e *ensembles* (*Random Forests*, *Gradient Boosting*, XGBoost, *Stacking*); validação (`StratifiedKFold`, `GroupKFold`, `TimeSeriesSplit`), métricas, calibração, limiar financeiro e avaliação por fatias; *deploy* (*batch* vs. *online*), compressão, serviço `FastAPI` e monitoramento de *drift* (KS e PSI). |
| **06** | **LLMs, Prompt Engineering e Avaliação** | 4 | Fundamentos de LLMs, tokenização (BPE/`tiktoken`), *embeddings*, Transformer (Q/K/V, GQA, RoPE, KV Cache), Pré-treinamento/SFT/RLHF/DPO e amostragem; engenharia de prompts, papéis, *Instruction Hierarchy*, orçamento de tokens, *Lost in the Middle*, *Few-Shot* e raciocínio em tempo de teste (CoT, *Self-Consistency*, ToT); saídas estruturadas (JSON Schema/Pydantic), `logprobs`, *Tool Calling* e ReAct; avaliação (*AI-as-a-Judge*, NLI, *pass@k*), RAG vs. *Finetuning* (LoRA/QLoRA), *guardrails* contra *Prompt Injection* e otimização de inferência (TTFT, TPOT, *PagedAttention*, *Continuous Batching*). |
| **07** | **RAG e Arquitetura de Agentes** | 4 | Ingestão, *chunking*, *Contextual Retrieval*, indexação multi-representação, sincronização incremental e busca vetorial (*k-NN* vs. HNSW/IVF/PQ em FAISS, PGVector, Pinecone); recuperação híbrida (BM25 + densa + RRF), *reranking* com *Cross-Encoders*, transformação de consultas (*HyDE*, *Multi-Query*) e métricas de RAG; fronteira entre *workflows* determinísticos (padrões Anthropic) e agentes autônomos (*ReAct*, *Plan-and-Execute*, *Reflexion*); grafos de estado (`LangGraph`), topologias multiagentes, *Agent-Computer Interface*, *Human-in-the-Loop*, *Model Gateway*, *guardrails* de PII e observabilidade. |

### Fluxo Operacional de Cada Aula

Toda sessão de estudo executa o seguinte ciclo determinístico no repositório `PROFESSOR_IA`:

```text
[1. Abrir Chat Novo]
        |
        v
[2. Inicialização Automática do Tutor]
   -> git pull --ff-only origin main
   -> python scripts/identificar_aluno.py (via ALUNO_TOKEN em .aluno.env)
   -> seleciona a próxima aula não concluída em trilhas/
        |
        v
[3. Condução da Aula (1 única aula)]
   -> aula inaugural (00): exposição direta sobre o curso, sem perguntas
   -> trilhas técnicas (01 a 07): apresentação da(s) fonte(s) + 3 a 5 blocos com perguntas (e correção/complementação direta caso falte algo)
        |
        v
[4. Encerramento e Sincronização]
   -> atualização de progresso.local.md (data UTC, acerto %, parecer objetivo)
   -> python scripts/sync_progresso.py (envio autenticado ao painel da Diretoria)
        |
        v
[5. Fim da Sessão -> Abrir Chat Novo para a Próxima Aula]
```

---

## 3. Critério de Decisão

Para extrair o máximo retorno técnico do programa, utilize os critérios abaixo:

- **Estudo sequencial versus consulta sob demanda (`referencias.md`):** Siga a ordem das aulas (`00` até `07`) para consolidar os pré-requisitos necessários. Cada aula condensa os conceitos de maior impacto nos projetos da Diretoria; tópicos extensos ou especializados (provas formais, consenso Paxos/Raft, redes neurais profundas ou recursos proprietários) ficam mapeados em `referencias.md` para consulta sob demanda quando um projeto exigir.
- **Permanecer no chat atual versus abrir um chat novo:** Use o chat atual apenas para concluir a aula em andamento e esclarecer eventuais dúvidas rápidas sobre ela após o término. Ao concluir e sincronizar a aula, **abra obrigatoriamente um chat novo** para a aula seguinte; o tutor bloqueará o início de outra aula na mesma conversa.
- **Acompanhamento de fontes externas:** Quando a aula citar URLs de documentações, artigos ou vídeos, aceite a abertura da fonte no início da sessão sempre que quiser acompanhar exemplos completos e diagramas originais.

---

## 4. Erros Comuns

- **Fazer várias aulas no mesmo chat:** Continuar no mesmo chat após terminar uma aula acumula histórico irrelevante, degrada a atenção do modelo e mistura conceitos de aulas diferentes. *Correção:* encerre a conversa após `python scripts/sync_progresso.py` e abra um chat novo; seu progresso é retomado automaticamente via `identificar_aluno.py`.
- **Pular trilhas de fundação:** Avançar direto para as Trilhas `06` ou `07` sem dominar `Pydantic`/`FastAPI`, SQL, estatística e validação de ML impede diagnosticar falhas reais em produção. *Correção:* siga a sequência de `00-grade-curricular.md`.
- **Pedir respostas prontas ou decorar sintaxe:** O tutor avalia raciocínio técnico e escolha de ferramentas, não memorização de parâmetros. *Correção:* responda com sua justificativa em cada bloco das trilhas `01` a `07`; se houver erro conceitual, resposta incompleta ou apenas troca de nome de método, o tutor corrigirá/completará diretamente os pontos necessários e avançará com a aula.
- **Editar `trilhas/` ou rodar `git push` manualmente:** As aulas são mantidas centralmente pela Diretoria e o envio de progresso ocorre via API autenticada. *Correção:* nunca edite `trilhas/` nem execute `git push`; utilize apenas `python scripts/sync_progresso.py`.
