# Aula 01 — Indexação, Chunking e Bancos de Dados Vetoriais

> **Fonte(s) desta aula:**
> - **OSHIN, Mayo; CAMPOS, Nuno.** *Learning LangChain: Building AI and LLM Applications with LangChain and LangGraph*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Capítulo 1 (*LLM Fundamentals with LangChain*, pp. 1–22) e Capítulo 2 (*RAG Part I: Indexing Your Data*, pp. 23–56).
> - **HUYEN, Chip.** *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Capítulo 6 (*RAG and Agents*, seções *Retrieval Algorithms* e *Retrieval Optimization*, pp. 254–278).
> - **ALAMMAR, Jay; GROOTENDORST, Maarten.** *Hands-On Large Language Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Capítulo 8 (*Semantic Search and Retrieval-Augmented Generation*, seções *Dense Retrieval* e *Chunking Long Texts*, pp. 225–239).
> - **PHOENIX, James; TAYLOR, Mike.** *Prompt Engineering for Generative AI*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Capítulo 4 (*Document Loaders* e *Text Splitters*, pp. 158–168) e Capítulo 5 (*Vector Databases with FAISS and Pinecone*, pp. 185–214).
> - **OPENAI.** *OpenAI Cookbook*. Disponível em: `https://cookbook.openai.com/`.

---

## 1. Problema e Definição

Modelos de linguagem de grande escala (*Large Language Models* — LLMs) possuem conhecimento paramétrico estático, limitado à data de corte do treinamento e sem acesso nativo a bases privadas ou transacionais. Mesmo em modelos com janelas de contexto extensas, enviar bases documentais inteiras em cada requisição é inviável em produção devido ao custo linear por token, ao aumento da latência de pré-preenchimento (*Time to First Token* — TTFT) e à perda de precisão de recuperação em sequências longas.

O pipeline de **Indexação e Recuperação Vetorial** prepara uma base externa para consulta em tempo de execução por meio de quatro etapas formais:
1. **Extração e Normalização (*Document Loading*):** Conversão de arquivos heterogêneos (PDF, HTML, DOCX, CSV) em objetos `Document` contendo o texto (`page_content`) e um dicionário de metadados (`metadata` com origem, data, autor e controle de acesso).
2. **Particionamento (*Chunking*):** Divisão de documentos longos em segmentos menores (*chunks*) compatíveis com o limite de tokens do modelo de *embeddings* e com a granularidade semântica das consultas.
3. **Codificação Vetorial (*Embedding*):** Projeção de cada *chunk* em um vetor denso $\mathbf{v} \in \mathbb{R}^d$ (por exemplo, $d = 1536$), no qual textos com significado próximo apresentam alta similaridade geométrica (similaridade de cosseno, produto interno ou distância euclidiana $L_2$).
4. **Armazenamento e Indexação Incremental:** Persistência dos vetores e metadados em índices otimizados para busca de vizinhos mais próximos (*Nearest Neighbor Search*), sincronizando adições, edições e exclusões sem reindexar documentos inalterados.

### Estratégias de Chunking e Otimização de Representação
Gerar um único vetor para um documento inteiro comprime tópicos distintos em uma média pouco discriminativa, enquanto fragmentos excessivamente curtos perdem contexto referencial:
- **Particionamento Recursivo (`RecursiveCharacterTextSplitter`):** Aplica sequencialmente uma lista ordenada de separadores (por padrão `["\n\n", "\n", " ", ""]`). O divisor mantém parágrafos inteiros abaixo de `chunk_size`; se um bloco exceder o limite, recorre ao próximo delimitador, preservando fronteiras sintáticas. Para código-fonte ou Markdown, utilizam-se gramáticas específicas via `from_language`.
- **Particionamento por Tokens (`TokenTextSplitter` / `from_tiktoken_encoder`):** Dimensiona os blocos com o tokenizador exato do modelo, evitando truncamentos silenciosos. O parâmetro `chunk_overlap` (10% a 20% do `chunk_size`) mantém tokens compartilhados entre blocos consecutivos para preservar a continuidade nas bordas.
- **Recuperação Contextual (*Contextual Retrieval*):** Técnica proposta pela Anthropic na qual um LLM anexa um prefixo explicativo curto (50 a 100 tokens) a cada *chunk* antes da geração do *embedding*, situando o fragmento em relação ao documento de origem (por exemplo, identificando a qual empresa e trimestre pertence um trecho financeiro).
- **Indexação Multi-Representação:** Desacopla a unidade indexada para busca da unidade entregue ao gerador:
  - `MultiVectorRetriever` e `ParentDocumentRetriever`: Indexam-se resumos concisos (eficazes para tabelas ou relatórios densos) ou *chunks* menores no banco vetorial, mantendo uma chave `doc_id` associada ao documento completo ou bloco pai armazenado em um `docstore` chave-valor.
  - **RAPTOR (*Recursive Abstractive Processing for Tree-Organized Retrieval*):** Agrupa *chunks* por similaridade vetorial (*clustering*) e gera resumos recursivos em árvore hierárquica, atendendo tanto consultas factuais locais (folhas) quanto consultas temáticas globais (nós superiores).
  - **Interação Tardia (*Late Interaction* — ColBERTv2):** Em vez de comprimir o *chunk* em um único vetor (*bi-encoder*), armazena um vetor contextualizado por token. Na busca, calcula o operador *MaxSim* (soma das similaridades máximas entre cada token da consulta e os tokens do documento), preservando correspondências finas com menor custo que um *cross-encoder*.

### Algoritmos de Busca Vetorial: k-NN Exato vs. ANN
A busca exata (*k-Nearest Neighbors* — k-NN, como `IndexFlatL2` ou `IndexFlatIP` no FAISS) compara o vetor de consulta contra todos os $N$ vetores da base com complexidade $O(N \cdot d)$. Acima de centenas de milhares de vetores, utilizam-se algoritmos de **Busca Aproximada de Vizinhos Mais Próximos (*Approximate Nearest Neighbors* — ANN)**, avaliados pelo equilíbrio entre revocação (*recall*), consultas por segundo (QPS), tempo de construção e consumo de memória:
- **HNSW (*Hierarchical Navigable Small World*):** Grafo multicamadas com conexões de longo alcance no topo e refinamento local na base. Entrega alta velocidade e *recall* elevado, com maior consumo de RAM.
- **IVF (*Inverted File Index*):** Particiona o espaço vetorial em $C$ células de Voronoi via *k-means* e restringe a busca às `nprobe` células mais próximas.
- **PQ (*Product Quantization*):** Decompõe cada vetor de dimensão $d$ em subvetores e quantiza cada parte para o centroide mais próximo de um *codebook*, reduzindo drasticamente o tamanho do índice em memória (frequentemente combinado como `IVFPQ`).
- **LSH (*Locality-Sensitive Hashing*) e Annoy:** Particionam o espaço por funções de *hash* projetivas ou florestas de árvores de projeção aleatória.

---

## 2. Aplicação Prática

O código abaixo utiliza **LangChain**, **PostgreSQL (`PGVector`)** e **`SQLRecordManager`**. O `RecordManager` calcula o *hash* do conteúdo e dos metadados de cada *chunk* vinculado a `source_id_key`, garantindo **idempotência**: documentos inalterados são ignorados (`num_skipped`), documentos editados têm os *chunks* antigos substituídos e documentos obsoletos são removidos.

```python
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_postgres.vectorstores import PGVector
from langchain.indexes import SQLRecordManager, index

CONNECTION_STRING = "postgresql+psycopg://usuario:senha@localhost:5432/rag_producao"
COLLECTION_NAME = "normas_tecnicas_v1"

embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = PGVector(
    embeddings=embeddings,
    collection_name=COLLECTION_NAME,
    connection=CONNECTION_STRING,
    use_jsonb=True,
)

# Inicialização do RecordManager para controle de hashes e estado
record_manager = SQLRecordManager(f"pgvector/{COLLECTION_NAME}", db_url=CONNECTION_STRING)
record_manager.create_schema()

# Extração e particionamento calibrado por tokens
raw_docs = PyPDFLoader("dados/manual_operacional.pdf").load()
splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    model_name="gpt-4o",
    chunk_size=500,
    chunk_overlap=75,
)
chunks = splitter.split_documents(raw_docs)

for chunk in chunks:
    chunk.metadata["departamento"] = "engenharia"

# Sincronização incremental idempotente
resultado_sync = index(
    docs_source=chunks,
    record_manager=record_manager,
    vector_store=vectorstore,
    cleanup="incremental",
    source_id_key="source",
)
# Retorna: {'num_added': X, 'num_updated': Y, 'num_skipped': Z, 'num_deleted': W}
```

---

## 3. Critério de Decisão

| Dimensão de Projeto | Opção A | Opção B | Critério Técnico de Escolha |
| :--- | :--- | :--- | :--- |
| **Granularidade do Chunk** | Pequenos (`128`–`256` tokens) | Médios/Grandes (`512`–`1024` tokens) | Use blocos pequenos para busca factual pontual (ou com `ParentDocumentRetriever`); use `512`–`1024` tokens quando a resposta exigir contexto de múltiplos parágrafos. |
| **Tabelas e Relatórios** | *Chunking* direto do texto bruto | `MultiVectorRetriever` (Resumo $\to$ Tabela) | *Embeddings* de tabelas brutas têm baixa revocação; indexe um resumo em linguagem natural e recupere a tabela íntegra em Markdown/HTML via `doc_id`. |
| **Modo de Limpeza (`index`)** | `cleanup="incremental"` | `cleanup="full"` | Use `incremental` em atualizações parciais ou contínuas por `source_id_key`; use `full` apenas quando o lote contiver 100% dos documentos vigentes da base. |
| **Algoritmo ANN** | HNSW | IVF + PQ (`IVFPQ`) | Escolha **HNSW** quando baixa latência (< 20 ms) e *recall* (> 95%) forem prioritários e houver RAM suficiente; escolha **IVFPQ** para dezenas de milhões de vetores sob restrição de memória. |
| **Infraestrutura Vetorial** | Local (`FAISS`) ou Relacional (`PGVector`) | Gerenciado (`Pinecone`, `Weaviate`) | Use **FAISS** para cargas estáticas locais; **PGVector** para unificar transações ACID, filtros JSONB e vetores; **Pinecone** para escalabilidade gerenciada com *namespaces*. |

---

## 4. Erros Comuns

- **Ingestão repetida sem `RecordManager`:** Executar `vectorstore.add_documents(chunks)` em tarefas agendadas duplica vetores, multiplica custos de API e contamina os *top-k* resultados com versões desatualizadas do mesmo arquivo.
- **Incompatibilidade de modelos de *embedding* entre indexação e busca:** Trocar o modelo da consulta sem reindexar a base armazenada invalida o cálculo de distância, mesmo quando ambos os modelos possuem a mesma dimensão vetorial.
- **Particionamento cego de tabelas e código:** Aplicar corte fixo por caracteres separa cabeçalhos de tabelas de suas linhas e assinaturas de funções de seu corpo; utilize divisores sintáticos ou `MultiVectorRetriever`.
- **Fusão incorreta de índices locais no FAISS:** Mesclar índices via `index1.add(index2.reconstruct_n(0, index2.ntotal))` reatribui os IDs originais do segundo índice e falha em estruturas que não suportam `reconstruct` (como `IndexIVFFlat`) sem mapeamento externo (`IndexIDMap`).
- **Fragmentos sem contexto referencial:** Armazenar *chunks* com referências relativas ("O indicador subiu 12% no trimestre") sem `chunk_overlap`, metadados de título ou *Contextual Retrieval* impede a identificação da entidade ou período correspondente.
