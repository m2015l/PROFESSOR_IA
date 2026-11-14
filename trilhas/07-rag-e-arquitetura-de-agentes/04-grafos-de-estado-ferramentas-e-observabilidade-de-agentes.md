# Aula 04 — Grafos de Estado, Ferramentas e Observabilidade de Agentes

> **Fonte(s) desta aula:**
> - **OSHIN, Mayo; CAMPOS, Nuno.** *Learning LangChain: Building AI and LLM Applications with LangChain and LangGraph*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Capítulo 4 (*Using LangGraph to Add Memory to Your Chatbot*, pp. 95–114), Capítulo 6 (*Agent Architecture*, pp. 135–153), Capítulo 7 (*Agents II*, pp. 155–170) e Capítulo 8 (*Patterns to Make the Most of LLMs*, pp. 171–189).
> - **HUYEN, Chip.** *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Capítulo 6 (*Tool Selection*, *Failure Modes* e *Memory*, pp. 285–306) e Capítulo 10 (*AI Engineering Architecture and User Feedback*, pp. 449–493).
> - **PHOENIX, James; TAYLOR, Mike.** *Prompt Engineering for Generative AI*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Capítulo 6 (*Understanding and Using Memory* e *Callbacks*, pp. 248–266).
> - **ANTHROPIC.** *Building Effective Agents*. Anthropic Research, 2024. Disponível em: `https://www.anthropic.com/research/building-effective-agents`.
> - **OPENAI.** *OpenAI Cookbook*. Disponível em: `https://cookbook.openai.com/`.

---

## 1. Problema e Definição

Implementar agentes autônomos em produção utilizando laços `while` imperativos e listas de mensagens em memória volátil ocasiona perda de estado em falhas de processo, impossibilidade de pausar a execução para aprovação humana (*Human-in-the-Loop*), condições de corrida em chamadas simultâneas, queda de precisão na escolha de ferramentas quando o catálogo cresce e cegueira operacional diante de falhas silenciosas.

A engenharia de agentes em produção resolve esses problemas modelando o fluxo como uma **Máquina de Estados em Grafo (`StateGraph`)**, aplicando princípios de **Interface Agente-Computador (*Agent-Computer Interface* — ACI)** e operando sob uma arquitetura de *guardrails*, *caches*, roteamento e observabilidade.

### Grafos de Estado, Persistência e Higiene de Memória no LangGraph
No **LangGraph**, a orquestração cíclica baseia-se em quatro componentes:
1. **Estado Tipado e Redutores (*State & Reducers*):** O estado compartilhado é um esquema `TypedDict` ou `Pydantic`. Cada campo pode declarar uma função redutora via `Annotated[tipo, reducer]` (como `add_messages`), que mescla determinísticamente as atualizações retornadas por cada nó ao histórico existente (anexando novas mensagens ou sobrescrevendo por `id`), evitando perda de estado entre etapas.
2. **Nós (*Nodes*) e Arestas (*Edges*):** Nós são funções que recebem o estado atual e retornam atualizações parciais. Arestas estáticas (`add_edge`) e condicionais (`add_conditional_edges`) governam as transições (ex.: verificar via `tools_condition` se a última `AIMessage` contém `tool_calls` para acionar o `ToolNode` ou encerrar em `END`).
3. **Checkpointers e Threads:** Um *checkpointer* (`PostgresSaver`, `SqliteSaver`, `MemorySaver`) persiste o *snapshot* de cada superpasso vinculado a um `thread_id`, permitindo retomada de falhas, inspeção (`get_state`), edição manual (`update_state`) e viagem no tempo/ramificação (*time-travel* via `get_state_history`).
4. **Gestão de Memória de Curto e Longo Prazo:** Para respeitar o limite de tokens e a integridade estrutural exigida pelas APIs, aplica-se `trim_messages` (com `strategy="last"`, `include_system=True`, `allow_partial=False` e `start_on="human"`), além de `filter_messages` e `merge_message_runs`. Para memória de longo prazo entre sessões, utilizam-se sumarização incremental (`ConversationSummaryBuffer`), extração de entidades e bancos vetoriais episódicos.

### Engenharia de Ferramentas (ACI), Seleção Dinâmica e Modos de Falha
- **Design *Poka-Yoke* de ACI:** A especificação de ferramentas (`args_schema` em Pydantic com tipos `Literal`, restrições de formato e docstrings claras) deve tornar erros de invocação estruturalmente impossíveis. Exigir caminhos de arquivo absolutos em vez de relativos evita falhas após mudanças de diretório; retornar erros semânticos detalhados pelo `ToolNode` permite autocorreção pelo modelo no passo seguinte.
- **Pré-seleção Dinâmica e Primeira Ferramenta Fixa:** Acima de 10 a 15 ferramentas vinculadas simultaneamente, a acurácia de seleção cai e o custo de tokens sobe. Soluciona-se indexando as descrições das ferramentas em um banco vetorial para vincular (`bind_tools`) apenas as *top-k* ferramentas relevantes para a consulta atual. Quando uma busca inicial é obrigatória, modela-se uma aresta fixa para chamar a ferramenta antes do primeiro nó do LLM (*Always Calling a Tool First*).
- **Modos de Falha e Ablação:** As falhas de ação classificam-se em: (1) ferramenta inexistente; (2) parâmetros fora do esquema; (3) esquema válido com valores semânticos incorretos; e (4) falha externa da API da ferramenta. Estudos de ablação medem o ganho marginal de cada ferramenta para remover aquelas que degradam o agente.

### Subgrafos, Topologias Multiagentes e Human-in-the-Loop
Sistemas complexos dividem responsabilidades em **Subgrafos** (com esquema compartilhado ou isolado por função adaptadora) organizados em topologias **Supervisor** (coordenador central que despacha para especialistas), **Hierárquica** (supervisores em múltiplos níveis) ou **Rede** (transferência direta entre agentes). Para ações de escrita críticas (*Write Actions*), configura-se `interrupt_before=["tools"]`, pausando a execução antes do efeito colateral para que o operador humano possa autorizar (invocando o grafo com `None`), editar argumentos via `update_state` ou cancelar. Requisições concorrentes na mesma *thread* são tratadas por políticas explícitas (*Reject*, *Queue*, *Interrupt* ou *Fork and Merge*).

### Arquitetura de Produção: Gateways, Caches, Guardrails e Observabilidade
1. **Model Gateway e Caches:** O *Model Gateway* centraliza autenticação, controle de custos, *rate limiting* e *fallback* entre provedores. O **Cache Exato** armazena respostas para prompts idênticos (com isolamento por *tenant*), enquanto o **Cache Semântico** busca respostas anteriores por similaridade vetorial acima de um limiar estrito $\tau$ (ex.: $\tau \ge 0,96$).
2. **Guardrails e Dicionário Reverso de PII:** *Input guardrails* mitigam *prompt injection* e mascaram dados sensíveis (**PII**) por marcadores (`[CPF_1]`) mantidos em um **dicionário reverso de PII**, reidratando os dados apenas na saída autorizada. *Output guardrails* validam formato, segurança e fidelidade factual.
3. **Observabilidade, Traces e Sinais de Feedback:** **Traces distribuídos** capturam a árvore completa de execução (*spans* de nós, prompts, chamadas de ferramentas, tokens apurados via *callbacks*, latência e custo). Monitoram-se métricas de inferência (**TTFT**, **TPOT**, **TPS**) e de confiabilidade (**MTTD** — *Mean Time to Detect*, **MTTR** — *Mean Time to Recover*, **CFR** — *Change Failure Rate*), detecção de *drift* e sinais de *feedback* explícitos (votos) e implícitos (abandono, regeneração, reformulação e edições do usuário, utilizáveis como pares de preferência para DPO).

---

## 2. Aplicação Prática

O código a seguir implementa um agente em **LangGraph** com estado tipado, `MemorySaver`, poda segura de histórico (`trim_messages`) e interrupção *Human-in-the-Loop* (`interrupt_before=["tools"]`) para auditoria antes da execução de ferramentas.

```python
from typing import Annotated, TypedDict
from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, trim_messages
from langchain_core.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.checkpoint.memory import MemorySaver

@tool
def consultar_saldo(conta_id: str) -> str:
    """Consulta o saldo de uma conta pelo identificador exato (ex: 'ACC-102')."""
    return f"Saldo da conta {conta_id}: R$ 14.500,00"

@tool
def transferir_pix(conta_origem_id: str, chave_destino: str, valor_reais: float) -> str:
    """Ação de escrita: executa transferência financeira irreversível em reais."""
    return f"Transferência de R$ {valor_reais:.2f} de {conta_origem_id} para {chave_destino} efetivada."

ferramentas = [consultar_saldo, transferir_pix]
llm = ChatOpenAI(model="gpt-4o", temperature=0).bind_tools(ferramentas)

class EstadoAgente(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

def no_modelo(state: EstadoAgente) -> dict:
    historico_podado = trim_messages(
        state["messages"],
        max_tokens=2000,
        strategy="last",
        token_counter=ChatOpenAI(model="gpt-4o"),
        include_system=True,
        allow_partial=False,
        start_on="human",
    )
    return {"messages": [llm.invoke(historico_podado)]}

construtor = StateGraph(EstadoAgente)
construtor.add_node("agente", no_modelo)
construtor.add_node("tools", ToolNode(ferramentas))
construtor.add_edge(START, "agente")
construtor.add_conditional_edges("agente", tools_condition)
construtor.add_edge("tools", "agente")

grafo = construtor.compile(checkpointer=MemorySaver(), interrupt_before=["tools"])

config = {"configurable": {"thread_id": "sessao-auditoria-01"}}
grafo.invoke({"messages": [HumanMessage(content="Transfira R$ 500 da conta ACC-102 para chave@empresa.com")]}, config)

# Após inspeção via grafo.get_state(config), retoma-se a execução aprovada passando None:
resultado = grafo.invoke(None, config)
```

---

## 3. Critério de Decisão

| Decisão de Arquitetura | Opção A | Opção B | Critério Técnico de Escolha |
| :--- | :--- | :--- | :--- |
| **Topologia Multiagente** | **Supervisor Centralizado** | **Subgrafos Hierárquicos / Rede** | Use **Supervisor** para coordenar 2 a 5 especialistas sob controle central; use **Hierárquica** quando cada domínio exigir subagentes próprios. |
| **Catálogo de Ferramentas** | `bind_tools` estático | Recuperador vetorial dinâmico | Use vinculação estática até 10 ferramentas; acima de 10–15, filtre esquemas via busca vetorial por consulta. |
| **Memória de Curto Prazo** | `trim_messages` (Janela Deslizante) | Sumarização (`ConversationSummaryBuffer`) | Use `trim_messages` para latência mínima em turnos recentes; use sumarização híbrida quando fatos iniciais forem indispensáveis. |
| **Estratégia de Cache** | **Cache Exato** (Hash de prompt) | **Cache Semântico** (Vetor $\ge \tau$) | Use **Cache Exato** em extrações determinísticas; use **Cache Semântico** apenas em FAQs públicas, nunca sem filtro de *tenant*. |
| **Output Guardrails** | Validação em lote pós-geração | Validação em *streaming* | Desative o *streaming* direto sob risco crítico de conformidade, validando a resposta completa antes da exibição. |

---

## 4. Erros Comuns

- **Fatiamento manual sem `trim_messages`:** Cortar listas com `messages[-5:]` frequentemente inicia o contexto com uma `ToolMessage` órfã (sem a `AIMessage` precedente que gerou o `tool_call`) ou descarta a `SystemMessage`, provocando erro HTTP 400 na API.
- **Vazamento entre usuários (*Cross-Tenant Leak*):** Reutilizar `thread_id` ou consultar cache semântico sem particionar por `tenant_id` e `user_id`, expondo dados privados entre clientes.
- **Mascaramento de PII sem dicionário reverso:** Substituir dados por `[REDACTED]` irreversivelmente antes das ferramentas impede que APIs internas recebam identificadores necessários ou exibe marcadores brutos ao usuário.
- **Colisão de histórico em subgrafos:** Compartilhar a chave `messages` sem isolar o estado interno do subgrafo polui o contexto do supervisor com chamadas intermediárias de ferramentas.
- **Monitorar apenas códigos HTTP sem *Traces* e *Drift*:** Uma execução pode retornar HTTP `200 OK` enquanto sofre loops redundantes, escolha errada de ferramenta ou degradação silenciosa de qualidade.
