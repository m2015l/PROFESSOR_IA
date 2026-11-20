# Aula 03 — Workflows Determinísticos vs. Agentes Autônomos

> **Fonte(s) desta aula:**
> - **ANTHROPIC.** *Building Effective Agents*. Anthropic Research, 2024. Disponível em: `https://www.anthropic.com/research/building-effective-agents`.
> - **OSHIN, Mayo; CAMPOS, Nuno.** *Learning LangChain: Building AI and LLM Applications with LangChain and LangGraph*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Capítulo 5 (*Cognitive Architectures with LangGraph*, pp. 115–133), Capítulo 6 (*Agent Architecture*, pp. 135–153), Capítulo 7 (*Agents II*, pp. 155–170) e Capítulo 8 (*Patterns to Make the Most of LLMs*, pp. 171–189).
> - **HUYEN, Chip.** *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Capítulo 6 (*RAG and Agents*, seção *Agents*, pp. 279–305).
> - **PHOENIX, James; TAYLOR, Mike.** *Prompt Engineering for Generative AI*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Capítulo 4 (*Task Decomposition*, *Prompt Chaining* e *Document Chains*, pp. 168–184) e Capítulo 6 (*Autonomous Agents with Memory and Tools*, pp. 223–261).
> - **OPENAI.** *OpenAI Cookbook*. Disponível em: `https://cookbook.openai.com/`.

---

## 1. Problema e Definição

No desenvolvimento com LLMs, o termo "agente" é frequentemente atribuído de forma imprecisa a qualquer sistema composto por múltiplas chamadas. Na engenharia de IA, entretanto, distingue-se estritamente **Workflows Determinísticos** de **Agentes Autônomos** com base na **Fronteira de Pareto entre Agência e Confiabilidade**:
- **Workflows Determinísticos:** Sistemas nos quais os LLMs e as ferramentas externas são orquestrados por fluxos de controle predefinidos em código. A ordem das etapas, as ramificações e as condições de parada são governadas deterministicamente pela aplicação.
- **Agentes Autônomos:** Sistemas nos quais o próprio LLM dirige dinamicamente o fluxo de controle, decidindo quais ferramentas acionar, inspecionando os retornos do ambiente (*observações*) e determinando quando encerrar o ciclo.

### Matemática do Erro Composto e Hierarquia de Arquiteturas Cognitivas
Delegar o controle de fluxo a um modelo estocástico eleva a latência, o custo de tokens e a variância operacional devido à **acumulação exponencial de erros**. Se um agente apresenta probabilidade de acerto de $p = 0,95$ ($95\%$) em cada passo, a probabilidade de concluir com êxito uma trajetória de $N$ etapas independentes é $P(\text{sucesso}) = p^N$:
- Em $N = 1$ etapa: $0,95^1 = 95,0\%$;
- Em $N = 10$ etapas: $0,95^{10} \approx 59,9\%$;
- Em $N = 50$ etapas: $0,95^{50} \approx 7,7\%$.

Portanto, o projeto deve seguir a **Hierarquia de Arquiteturas Cognitivas**, selecionando o menor grau de autonomia capaz de atender aos requisitos:
1. **Nível 0 — Código Determinístico Puro:** Algoritmos tradicionais sem invocação de modelos.
2. **Nível 1 — Chamada Única de LLM:** Uma transformação direta de entrada em saída (tipicamente com saída estruturada).
3. **Nível 2 — Cadeia Sequencial (*Chain*):** Sequência fixa de chamadas a LLMs (ex.: gerar SQL $\to$ executar consulta $\to$ sintetizar resposta).
4. **Nível 3 — Roteador (*Router*):** Classificação da entrada para selecionar qual subfluxo acíclico (DAG) será executado.
5. **Nível 4 — Máquina de Estados / Agente Autônomo:** Grafo contendo **ciclos** (*loops*), no qual o LLM decide iterativamente a próxima ação até atingir a condição de parada.

### Os Cinco Padrões Canônicos de Workflows (Anthropic) e Cadeias Documentais
1. **Encadeamento de Prompts (*Prompt Chaining*):** Decompõe uma tarefa em uma sequência fixa de chamadas onde cada etapa processa a saída da anterior, permitindo validações programáticas (*gates*) intermediárias. Para processamento de múltiplos documentos, divide-se em quatro estratégias: *Stuff* (concatenação única no prompt), *Refine* (atualização iterativa sequencial documento a documento), *Map-Reduce* (processamento paralelo independente na etapa *Map* e agregação na etapa *Reduce*) e *Map Re-rank* (execução por documento com nota de confiança e seleção da maior pontuação).
2. **Roteamento (*Routing*):** Classifica a intenção ou a complexidade da requisição e a direciona para prompts especializados, ferramentas específicas ou modelos de portes distintos (ex.: consultas simples para modelos rápidos e econômicos; problemas complexos para modelos de fronteira).
3. **Paralelização (*Parallelization*):** Executa chamadas concorrentes agregadas programaticamente em duas variantes:
   - *Sectioning*: Divisão da tarefa em subtarefas independentes executadas em paralelo (ex.: gerar resposta ao usuário enquanto outra chamada verifica políticas de segurança).
   - *Voting*: Execução da mesma tarefa múltiplas vezes para agregação por voto majoritário, reduzindo falsos negativos em revisões críticas de código ou conformidade.
4. **Orquestrador-Trabalhadores (*Orchestrator-Workers*):** Um LLM central (*orquestrador*) decompõe dinamicamente uma tarefa aberta em subtarefas variáveis, delega cada parte a instâncias *workers* especializadas e consolida os retornos (ex.: edição coordenada de múltiplos arquivos em um repositório).
5. **Avaliador-Otimizador (*Evaluator-Optimizer* / *Reflection*):** Ciclo fechado onde um LLM gerador produz um artefato e um segundo módulo (avaliador LLM ou verificador determinístico como compilador/*linter*) emite críticas estruturadas para refinamento iterativo até aprovação ou limite de tentativas.

### Arquiteturas de Agentes Autônomos: ReAct, Plan-and-Execute, Reflexion e ToT
- **ReAct (*Reason + Act*):** Alterna geração de raciocínio (*Thought*), chamada de ferramenta (*Action*) e leitura do resultado (*Observation*) em um laço contínuo.
- **Desacoplamento entre Planejamento e Execução (*Plan-and-Execute*):** Separa a geração do plano completo (módulo *Planner*) da execução de ações. Permite validar o plano inteiro por regras determinísticas ou juízes antes de disparar ferramentas com efeitos colaterais, reavaliando o plano após cada passo.
- **Reflexion e Tree of Thoughts (ToT):** O *Reflexion* armazena autocríticas verbais sobre falhas anteriores na memória episódica para guiar novas tentativas. O *Tree of Thoughts* expande múltiplos ramos de raciocínio simultâneos, aplicando busca em largura (BFS) ou profundidade (DFS) com avaliação heurística e retrocesso (*backtracking*).

---

## 2. Aplicação Prática

O código abaixo implementa o padrão **Evaluator-Optimizer (Reflection)** acoplado a uma validação determinística (*gate*) para síntese de consultas SQL seguras, garantindo que apenas comandos de leitura aprovados sejam retornados.

```python
import os
from typing import Literal
from pydantic import BaseModel, Field
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Parametrize o identificador do modelo via variável de ambiente para evitar dependência de modelos depreciados
llm = ChatOpenAI(model=os.environ["OPENAI_MODEL"], temperature=0)

class CandidatoSQL(BaseModel):
    consulta_sql: str = Field(description="Consulta SQL ANSI de leitura (SELECT)")

class AvaliacaoSQL(BaseModel):
    status: Literal["APROVADO", "REJEITADO"]
    critica_tecnica: str = Field(description="Erros sintáticos, colunas inválidas ou violação de segurança")

gerador = ChatPromptTemplate.from_messages([
    ("system", "Gere uma consulta SQL para o esquema: {esquema}. Corrija erros apontados nas críticas."),
    ("human", "Pedido: {pedido}\nCríticas: {historico_criticas}"),
]) | llm.with_structured_output(CandidatoSQL)

avaliador = ChatPromptTemplate.from_messages([
    ("system", "Audite o SQL contra o esquema {esquema}. Rejeite se houver comandos DML/DDL, "
               "ausência de LIMIT ou colunas inexistentes."),
    ("human", "Pedido: {pedido}\nSQL: {sql}"),
]) | llm.with_structured_output(AvaliacaoSQL)

def executar_avaliador_otimizador(pedido: str, esquema: str, max_iter: int = 3) -> str:
    criticas = "Nenhuma."
    proibidos = {"INSERT", "UPDATE", "DELETE", "DROP", "ALTER", "TRUNCATE"}
    for passo in range(max_iter):
        sql = gerador.invoke({"esquema": esquema, "pedido": pedido, "historico_criticas": criticas}).consulta_sql.strip()
        if proibidos.intersection(set(sql.upper().replace(";", " ").split())):
            criticas = "Gate determinístico violado: comando de escrita proibido."
            continue
        revisao = avaliador.invoke({"esquema": esquema, "pedido": pedido, "sql": sql})
        if revisao.status == "APROVADO":
            return sql
        criticas = f"Tentativa {passo + 1}: {revisao.critica_tecnica}"
    raise RuntimeError(f"Não convergiu após {max_iter} tentativas: {criticas}")
```

---

## 3. Critério de Decisão

| Padrão Arquitetural | Grau de Autonomia | Critério de Escolha (Quando Usar) | Restrição Operacional (Quando Evitar) |
| :--- | :--- | :--- | :--- |
| **Prompt Chaining / Routing** | Baixo (DAG estático) | Etapas previsíveis e fixas (ex.: classificação de chamado $\to$ extração $\to$ resposta). | Quando a sequência de passos depende de informações desconhecidas antes da execução. |
| **Parallelization (*Sectioning* / *Voting*)** | Baixo (DAG paralelo) | Subtarefas independentes executáveis concorrentemente para reduzir latência, ou consenso por votação. | Quando a etapa seguinte depende estritamente da saída da etapa anterior. |
| **Orchestrator-Workers** | Médio (Decomposição dinâmica) | Escopo de subtarefas variável por entrada (ex.: refatorar múltiplos módulos ou pesquisar N fontes). | Fluxos fixos nos quais a sobrecarga do LLM orquestrador é desnecessária. |
| **Evaluator-Optimizer (*Reflection*)** | Médio (Ciclo controlado) | Existência de verificadores objetivos (compiladores, *linters*, esquemas formais) onde a precisão justifica múltiplas chamadas. | Tarefas sem critério verificável ou com requisito de baixa latência (< 1 s). |
| **Agente Autônomo (*ReAct* / *Plan-and-Execute*)** | Alto (Grafo cíclico aberto) | Problemas abertos onde a trajetória de ferramentas não pode ser codificada previamente. | Operações padronizadas críticas que exigem caminho determinístico e custo fixo. |

---

## 4. Erros Comuns

- **Adotar agentes autônomos para fluxos sequenciais fixos:** Usar um agente *ReAct* aberto onde um *Prompt Chaining* ou *Router* de 3 etapas resolve o problema, multiplicando latência, custo e risco de desvio.
- **Omitir limites de parada em ciclos:** Executar loops de *Reflection* ou *ReAct* sem `max_iterations` e `max_execution_time`, permitindo execuções infinitas quando uma API externa falha.
- **Autoavaliação sem sinais externos (*Ungrounded Reflection*):** Pedir que o modelo revise sua própria resposta sem fornecer saídas de compiladores, validadores de esquema ou dados recuperados, degradando respostas inicialmente corretas.
- **Acoplar planejamento exploratório a ações de escrita (*Write Actions*):** Permitir que um agente dispare exclusões, pagamentos ou envios externos durante o loop exploratório sem validação prévia do plano completo.
- **Extração de ferramentas via *Regex* em texto livre:** Parsear chamadas de funções com expressões regulares frágeis quando o modelo suporta *Tool Calling* estruturado nativo.
