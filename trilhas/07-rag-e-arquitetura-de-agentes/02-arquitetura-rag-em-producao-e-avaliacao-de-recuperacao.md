# Aula 02 — Arquitetura RAG em Produção e Avaliação de Recuperação

> **Fonte(s) desta aula:**
> - **OSHIN, Mayo; CAMPOS, Nuno.** *Learning LangChain: Building AI and LLM Applications with LangChain and LangGraph*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Capítulo 3 (*RAG Part II: Chatting with Your Data*, pp. 57–93).
> - **HUYEN, Chip.** *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Capítulo 6 (*Term-Based Retrieval*, *Hybrid Search*, *Reranking* e *Evaluating Retrieval*, pp. 256–279).
> - **ALAMMAR, Jay; GROOTENDORST, Maarten.** *Hands-On Large Language Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Capítulo 8 (*Reranking*, *Retrieval Evaluation Metrics*, *RAG* e *RAG Evaluation*, pp. 239–258).
> - **PHOENIX, James; TAYLOR, Mike.** *Prompt Engineering for Generative AI*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Capítulo 5 (*Self-Querying* e *Alternative Retrieval Mechanisms*, pp. 214–221).
> - **OPENAI.** *OpenAI Cookbook*. Disponível em: `https://cookbook.openai.com/`.

---

## 1. Problema e Definição

Um pipeline de Geração Aumentada por Recuperação (*Retrieval-Augmented Generation* — RAG) elementar — que codifica a pergunta bruta do usuário em um vetor denso, recupera os $k$ fragmentos mais próximos e os concatena no prompt — apresenta limitações severas em produção. A busca puramente vetorial (*dense retrieval*) perde precisão em termos exatos, códigos alfanuméricos, cláusulas, siglas e nomes próprios raros. Além disso, mensagens conversacionais frequentemente são ambíguas, dependem de turnos anteriores ou exigem filtros estruturados sobre metadados e bancos relacionais.

Uma **Arquitetura RAG em Produção** resolve essas restrições integrando busca híbrida, reordenação em múltiplos estágios (*multi-stage reranking*), transformação/roteamento de consultas e avaliação quantitativa desacoplada entre recuperação e geração.

### Recuperação Léxica, Densa, Esparsa e Busca Híbrida (*Hybrid Search*)
- **Recuperação Léxica (*Term-Based Retrieval*):** Opera sobre um índice invertido que mapeia cada termo do vocabulário para a lista de documentos que o contêm (*posting lists*). O algoritmo padrão é o **Okapi BM25**, que aprimora o TF-IDF aplicando saturação assintótica à frequência do termo e normalizando o escore pelo tamanho do documento em relação à média da coleção.
- **Recuperação Densa e Esparsa Aprendida:** Enquanto *bi-encoders* densos geram vetores contínuos compactos ($d \in [384, 3072]$), modelos esparsos aprendidos como **SPLADE** expandem termos e atribuem pesos no espaço do vocabulário bruto, preservando compatibilidade com índices invertidos.
- **Busca Híbrida e Reciprocal Rank Fusion (RRF):** Como os escores do BM25 (ilimitados) e as similaridades de cosseno ($[-1, 1]$) possuem escalas incompatíveis, a combinação paralela de múltiplos recuperadores utiliza o **Reciprocal Rank Fusion (RRF)**. Para cada documento $D$ avaliado por $m$ recuperadores, a pontuação fundida depende apenas da posição (*rank*) $r_i(D)$ em cada lista ordenada $i$:

$$\text{RRF}(D) = \sum_{i=1}^{m} \frac{1}{k + r_i(D)}$$

onde $k$ é uma constante de suavização (tipicamente $k = 60$) que amortece discrepâncias extremas de posição em um único recuperador.

### Reranking em Dois Estágios e Ordenação no Contexto
Para equilibrar latência e precisão, a recuperação em produção opera em dois estágios: o primeiro estágio utiliza busca híbrida rápida (BM25 + ANN) para pré-selecionar $N$ candidatos (ex.: $N = 50$); o segundo aplica um **Cross-Encoder** (*monoBERT* ou *Cohere Rerank*) para pontuar cada par `(consulta, documento)` com atenção cruzada completa e selecionar os *top-k* finais (ex.: $k = 5$). Como LLMs sofrem perda de atenção no meio de contextos extensos (curva em U), os documentos mais relevantes após o *reranking* devem ser posicionados no início ou no fim do contexto enviado no prompt.

### Transformação, Roteamento e Construção de Consultas
1. **Transformação de Consultas (*Query Transformation*):**
   - *Rewrite-Retrieve-Read*: Um LLM reformula a pergunta conversacional, resolvendo referências do histórico e removendo ruído antes da busca.
   - *Multi-Query* e *RAG-Fusion*: O LLM decompõe a pergunta em 3 a 5 consultas distintas executadas em paralelo, aplicando união deduplicada (*Multi-Query*) ou fusão via RRF (*RAG-Fusion*).
   - *HyDE (Hypothetical Document Embeddings)*: O LLM gera um documento hipotético respondendo à consulta; o *embedding* desse documento sintético é usado na busca vetorial para reduzir a assimetria entre perguntas curtas e documentos longos.
2. **Roteamento (*Query Routing*) e Construção (*Query Construction*):**
   - *Roteamento Lógico vs. Semântico*: O roteamento lógico usa saída estruturada (`.with_structured_output()`) para escolher a fonte de dados (ex.: base fiscal, código ou CRM). O roteamento semântico compara o *embedding* da consulta com exemplos de cada rota via similaridade de cosseno, sem chamada gerativa.
   - *Text-to-Metadata Filter (`SelfQueryRetriever`)* e *Text-to-SQL*: Convertem restrições em linguagem natural em filtros estruturados de metadados (`AttributeInfo`) ou consultas SQL parametrizadas em modo somente leitura.

### Métricas de Avaliação de Recuperação e Geração
- **Avaliação da Recuperação:**
  - *Context Precision* ($\text{Precision}@k$) e *Context Recall* ($\text{Recall}@k$): Fração de documentos relevantes entre os $k$ recuperados e fração do total de relevantes da base capturada nos *top-k*.
  - *MRR (Mean Reciprocal Rank)*: Média do inverso da posição do primeiro documento relevante ($\frac{1}{\text{rank}_1}$).
  - *MAP (Mean Average Precision)*: Média das precisões apuradas em cada posição com documento relevante, penalizando irrelevantes no topo.
  - *NDCG (Normalized Discounted Cumulative Gain)*: Mede rankings com relevância graduada e desconto logarítmico por posição.
- **Avaliação da Geração (*LLM-as-a-Judge* / Ragas):**
  - *Faithfulness (Groundedness)*, *Citation Recall* e *Citation Precision*: Grau em que cada afirmação é sustentada pelos documentos recuperados e citada com precisão.
  - *Answer Relevance*: Aderência direta da resposta à pergunta original.

---

## 2. Aplicação Prática

O código a seguir implementa o padrão **RAG-Fusion** com geração fundamentada em **LangChain (LCEL)**, combinando reformulação estruturada de consultas, fusão via **RRF ($k=60$)** e restrição explícita de citação de fontes.

```python
import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableLambda
from pydantic import BaseModel, Field

# Parametrize o identificador do modelo via variável de ambiente para evitar dependência de modelos depreciados
llm = ChatOpenAI(model=os.environ["OPENAI_MODEL"], temperature=0)

class VariacoesConsulta(BaseModel):
    consultas: list[str] = Field(description="4 consultas de busca técnica reformuladas")

gerador_consultas = (
    ChatPromptTemplate.from_messages([
        ("system", "Gere 4 consultas de busca distintas para recuperar evidências sobre a pergunta."),
        ("human", "{pergunta}"),
    ])
    | llm.with_structured_output(VariacoesConsulta)
    | RunnableLambda(lambda x: x.consultas)
)

def reciprocal_rank_fusion(listas_resultados: list[list], k: int = 60, top_n: int = 5):
    pontuacoes, mapa_docs = {}, {}
    for docs in listas_resultados:
        for rank, doc in enumerate(docs):
            doc_id = doc.metadata.get("id", doc.page_content)
            mapa_docs[doc_id] = doc
            pontuacoes[doc_id] = pontuacoes.get(doc_id, 0.0) + 1.0 / (k + rank + 1)
    ordenados = sorted(pontuacoes.keys(), key=lambda x: pontuacoes[x], reverse=True)
    return [mapa_docs[i] for i in ordenados[:top_n]]

prompt_rag = ChatPromptTemplate.from_messages([
    ("system", "Responda usando EXCLUSIVAMENTE o contexto abaixo e cite [source]. "
               "Se faltar evidência, responda apenas: 'Informação insuficiente na base.'"),
    ("human", "Contexto:\n{contexto}\n\nPergunta: {pergunta}"),
])

def construir_chain_rag_fusion(retriever):
    retriever_rrf = gerador_consultas | retriever.map() | RunnableLambda(reciprocal_rank_fusion)
    return (
        {
            "contexto": lambda x: "\n\n".join(
                f"[{d.metadata.get('source', 'N/A')}] {d.page_content}"
                for d in retriever_rrf.invoke(x["pergunta"])
            ),
            "pergunta": lambda x: x["pergunta"],
        }
        | prompt_rag
        | llm
        | StrOutputParser()
    )
```

---

## 3. Critério de Decisão

| Técnica / Componente | Quando Utilizar | Quando Evitar | Impacto em Latência e Custo |
| :--- | :--- | :--- | :--- |
| **Busca Híbrida (BM25 + Vetorial com RRF)** | Bases com códigos, cláusulas, siglas e nomes próprios combinados a buscas conceituais. | Bases pequenas puramente semânticas com *Context Recall* vetorial > 95%. | Baixa latência (busca paralela) e custo restrito ao índice invertido. |
| **Reranking (*Cross-Encoder*)** | Quando os *top-5* iniciais contêm ruído (*Context Precision* baixa), mas os corretos estão nos *top-50*. | Sistemas com limite estrito (< 150 ms) sem inferência em GPU. | Adiciona 50 ms a 300 ms conforme $N$ candidatos e tamanho dos *chunks*. |
| **RAG-Fusion / Multi-Query** | Consultas complexas, comparativas ("Compare 2022 e 2024") ou ambíguas. | Consultas factuais diretas sob restrição severa de custo de tokens. | Adiciona 1 chamada ao LLM antes da busca e múltiplas consultas paralelas. |
| **HyDE** | Forte disparidade estilística entre perguntas curtas e documentos técnicos extensos. | Domínios fechados onde o LLM desconhece a terminologia e gera texto incorreto. | Adiciona a geração de 1 parágrafo sintético antes da busca vetorial. |
| **Self-Querying / Text-to-SQL** | Consultas com filtros numéricos, datas, categorias ou agregações (`SUM`, `COUNT`, `AVG`). | Metadados inconsistentes ou ausência de esquema validado. | Exige 1 chamada ao LLM (`temperature=0`) para síntese estruturada. |

---

## 4. Erros Comuns

- **Corrigir falhas de recuperação apenas no prompt de geração:** Ajustar instruções do LLM gerador quando a causa é *Context Recall* baixo; sem o documento relevante nos *top-k*, o modelo omitirá o fato ou alucinará.
- **Executar *Text-to-SQL* com permissão de escrita ou sem *timeout*:** Conectar o banco a um usuário capaz de executar `INSERT`, `UPDATE`, `DELETE` ou `DROP`, ou permitir consultas sem `LIMIT` e *timeout*.
- **Somar pontuações brutas de BM25 e cosseno sem RRF:** A adição direta faz com que a escala ilimitada do BM25 sobreponha a similaridade de cosseno ($[-1, 1]$), anulando a busca vetorial.
- **Omitir corte de distância e instrução de rejeição:** Como a busca vetorial sempre retorna $k$ vizinhos mesmo para perguntas fora de escopo, não filtrar distâncias altas nem exigir recusa explícita induz respostas sem base factual.
- **Injetar dezenas de *chunks* sem *reranking*:** Enviar 20 a 30 fragmentos brutos degrada a atenção quando o dado crítico fica no meio do contexto e multiplica o custo de tokens.
