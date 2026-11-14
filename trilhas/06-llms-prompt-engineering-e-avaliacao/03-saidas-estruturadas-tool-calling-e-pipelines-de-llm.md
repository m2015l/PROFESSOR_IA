# Aula 03 — Saídas Estruturadas, Tool Calling e Pipelines de LLM

**Fonte(s) desta aula:**
- HUYEN, Chip. *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Cap. 2 (pp. 102–106) e Cap. 5 (pp. 211–252).
- ALAMMAR, Jay; GROOTENDORST, Maarten. *Hands-On Large Language Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Part II — Caps. 4–7 (pp. 111–224).
- BERRYMAN, John; ZIEGLER, Albert. *Prompt Engineering for LLMs*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Caps. 7–9 (pp. 147–221).
- PHOENIX, James; TAYLOR, Mike. *Prompt Engineering for Generative AI*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Cap. 3 (pp. 57–124).
- OPENAI. *OpenAI Cookbook: Function Calling and Structured Outputs*. URL: `https://cookbook.openai.com/`.

---

## 1. Problema e Definição

A integração de LLMs como módulos de software exige que suas saídas obedeçam a contratos estritos de interface (**Saídas Estruturadas / *Structured Outputs***). Huyen (2025) e Alammar & Grootendorst (2024) estruturam o controle de formato em quatro níveis do pipeline de geração:

1. **Condicionamento via Prompt e Sequências de Parada (*Stop Sequences*):** inclusão de esquemas explícitos, exemplos *few-shot* e delimitadores de início e fim reconhecíveis (ex.: abrir bloco ```` ```json ```` e configurar `stop=["```"]`). Embora reduza erros, não garante validade sintática em $100\%$ das chamadas.
2. **Amostragem Restrita por Gramática (*Constrained Sampling / Guided Generation*):** intervenção direta no vetor de *logits* $\mathbf{z} \in \mathbb{R}^{|V|}$ antes da função *softmax* a cada passo de decodificação. Uma especificação formal — expressão regular, gramática livre de contexto (CFG em formato EBNF) ou **JSON Schema** derivado de classes **Pydantic** — é compilada em uma Máquina de Estados Finitos (*Finite-State Machine* — FSM) ou autômato com pilha. Em cada passo $t$, o motor de inferência (Outlines, `llama.cpp` com gramáticas GGUF, Guidance ou APIs nativas com `response_format`) determina o subconjunto de tokens válidos $V_{\text{val}} \subset V$ que mantêm a transição gramatical legal e aplica a máscara $z_i = -\infty$ para todo $i \notin V_{\text{val}}$, garantindo conformidade sintática.
3. **Pós-processamento e Validação com Retentativa (*Post-processing & Reflexion*):** analisadores defensivos validam tipos e invariantes de domínio (via Pydantic/Instructor) e, caso ocorra `ValidationError`, devolvem o rastreamento do erro ao modelo para autocorreção em nova passagem.
4. **Ajuste Fino (*Finetuning*):** treinamento específico para análise semântica (*semantic parsing*, como Text-to-SQL ou DSLs proprietárias), reduzindo o tamanho das instruções de sintaxe no prompt.

Além da extração estruturada, LLMs operam como classificadores discretos mediante inspeção de **log-probabilidades (`logprobs`)**. Quando uma tarefa exige escolher entre rótulos fixos, o modelo calcula $\log P(x_t \mid x_{<t})$ para os tokens candidatos. Berryman e Ziegler (2024) destacam dois requisitos técnicos para classificação via `logprobs`:
- **Unicidade do primeiro token de classe:** se duas classes compartilham o mesmo token inicial (ex.: `"North America"` e `"Northeast Asia"` começam pelo token `"North"`), o primeiro passo de decodificação soma as probabilidades de ambas, distorcendo a decisão mesmo quando uma terceira classe (`"Europe"`) possui maior probabilidade individual. Portanto, cada rótulo deve iniciar com um token único.
- **Calibração de limiar e *logit bias*:** como a fronteira de decisão padrão do modelo pode divergir da precisão/revocação requerida pelo sistema, aplica-se um deslocamento aditivo $\alpha_c$ aos `logprobs` de cada classe (ou via `logit_bias` na API), ajustado por minimização de entropia cruzada (regressão logística) sobre dados rotulados de validação.

Para acessar informações externas em tempo real ou executar ações determinísticas, utiliza-se **Tool Calling (*Function Calling*)**. Internamente, *tool calling* preserva a geração autorregressiva: a API serializa as declarações de funções (assinaturas tipadas e descrições de argumentos em JSON Schema ou TypeScript) dentro da mensagem `system`. Em cada turno, o modelo executa decisões sequenciais token a token: (1) emitir resposta direta ou iniciar o cabeçalho de invocação de ferramenta; (2) selecionar o nome da função; (3) gerar o objeto JSON com argumentos nomeados; e (4) emitir o token de encerramento. A aplicação intercepta a chamada, executa a função localmente, anexa o retorno em uma mensagem com `role="tool"` associada ao `tool_call_id` e realiza nova requisição ao modelo. Combinado ao padrão **ReAct (*Reason + Act*, Yao et al., 2022)**, o modelo alterna passos de raciocínio explícito, invocação de ferramenta e observação do resultado.

Para processos complexos de múltiplas etapas ou documentos que ultrapassam a janela efetiva de atenção, substituem-se agentes conversacionais monolíticos por **Pipelines e Workflows de LLM** organizados em sequências lineares, **Grafos Acíclicos Direcionados (DAGs)** ou grafos cíclicos com limite estrito de iterações. No processamento de documentos longos segmentados (*token chunking* com janela deslizante e sobreposição), Phoenix e Taylor (2024) definem quatro arquiteturas: **Stuff** (inserção integral em chamada única), **Refine** (atualização iterativa da resposta a cada bloco subsequente), **Map-Reduce** (processamento independente de cada bloco na fase *Map* e agregação final na fase *Reduce*) e **Map-Rerank** (pontuação de confiança por bloco, selecionando a resposta de maior nota).

---

## 2. Aplicação Prática

O código a seguir implementa (1) validação estruturada com Pydantic e geração de prompt de reparo (*Reflexion*), (2) calibração de classificador binário via `logprobs` e (3) roteador de execução de *Tool Calling*.

```python
import json
import math
from typing import Literal
from pydantic import BaseModel, Field, ValidationError

# 1. Contrato de Saída Estruturada via Pydantic e prompt de autocorreção (Reflexion)
class ChamadoSuporteExtraido(BaseModel):
    categoria: Literal["faturamento", "infraestrutura", "seguranca"]
    severidade: int = Field(ge=1, le=5, description="Severidade de 1 (baixo) a 5 (crítico)")
    id_cliente: str = Field(pattern=r"^CLI-\d{4}$")
    resumo_tecnico: str = Field(min_length=10, max_length=200)

def validar_ou_gerar_prompt_correcao(payload_json: str) -> tuple[ChamadoSuporteExtraido | None, str | None]:
    try:
        return ChamadoSuporteExtraido.model_validate_json(payload_json), None
    except ValidationError as err:
        prompt_reparo = (
            f"O JSON gerado violou o esquema Pydantic:\n{err}\n"
            f"Corrija exclusivamente os campos inválidos mantendo o formato JSON."
        )
        return None, prompt_reparo

# 2. Calibração de Classificação Binária via Logprobs (Berryman & Ziegler, Cap. 7)
def classificar_com_logprobs_calibrados(
    logprob_sim: float, logprob_nao: float, vies_calibracao_sim: float = 0.0
) -> dict[str, float | str]:
    lp_sim = logprob_sim + vies_calibracao_sim
    max_lp = max(lp_sim, logprob_nao)
    p_sim = math.exp(lp_sim - max_lp)
    p_nao = math.exp(logprob_nao - max_lp)
    prob_sim = p_sim / (p_sim + p_nao)
    return {"decisao": "Sim" if prob_sim >= 0.5 else "Nao", "probabilidade_sim": round(prob_sim, 4)}

# 3. Despachante de Tool Calling com vinculação de tool_call_id
def consultar_status_servidor(hostname: str) -> str:
    status = {"srv-db-01": "ONLINE (CPU 42%)", "srv-cache-02": "DEGRADADO (RAM 96%)"}
    return json.dumps({"hostname": hostname, "status": status.get(hostname, "DESCONHECIDO")})

REGISTRO_FERRAMENTAS = {"consultar_status_servidor": consultar_status_servidor}

def executar_chamadas_ferramentas(tool_calls: list[dict]) -> list[dict]:
    respostas = []
    for tc in tool_calls:
        nome_fn = tc["function"]["name"]
        args = json.loads(tc["function"]["arguments"])
        respostas.append({
            "role": "tool",
            "tool_call_id": tc["id"],
            "name": nome_fn,
            "content": REGISTRO_FERRAMENTAS[nome_fn](**args),
        })
    return respostas

obj, erro = validar_ou_gerar_prompt_correcao(
    '{"categoria": "infraestrutura", "severidade": 4, "id_cliente": "CLI-9081", "resumo_tecnico": "Latência elevada no cluster primário."}'
)
print("Validado:", obj)
print("Classificação Calibrada:", classificar_com_logprobs_calibrados(-0.85, -0.55, vies_calibracao_sim=0.40))
```

---

## 3. Critério de Decisão

| Problema Arquitetural | Abordagem Recomendada | Critério Técnico de Escolha |
| :--- | :--- | :--- |
| **Classificação com centenas/milhares de exemplos rotulados e baixa latência** | Modelo de Representação (**BERT/DeBERTa** ajustado ou **Embeddings + Regressão Logística**) | Elimina a decodificação autorregressiva e erros de formatação, operando em poucos milissegundos com baixo custo computacional. |
| **Classificação Zero-Shot / Few-Shot sem dados de treino** | LLM Gerador com **restrição de token único + inspeção de `logprobs`** | Aproveita a generalização pré-treinada do LLM e fornece probabilidades contínuas calibráveis com geração de apenas $1$ token. |
| **Extração de dados tipados para integração com APIs ou bancos de dados** | **Constrained Sampling / Structured Outputs** (JSON Schema / Pydantic) + validação local | A máscara sobre os *logits* assegura validade sintática e o validador Pydantic garante restrições semânticas de domínio. |
| **Orquestração multi-etapas em produção vs. tarefas exploratórias** | **Workflow em DAG determinístico** para fluxos fixos; **Agente ReAct** apenas quando o fluxo de ações depende das observações | DAGs isolam falhas por tarefa, permitem combinar modelos de portes distintos por etapa e evitam laços improdutivos. |

---

## 4. Erros Comuns

1. **Depender apenas de instruções no prompt para obter JSON válido sem amostragem restrita por gramática ou parser defensivo:** mesmo em `temperature = 0`, LLMs sem máscara de *logits* podem truncar objetos ao atingir `max_tokens`, omitir escape de aspas internas ou inserir texto fora do bloco JSON.
2. **Registrar dezenas de ferramentas sobrepostas ou espelhar endpoints REST brutos diretamente nas definições de *Tool Calling*:** ferramentas com muitos parâmetros ou descrições ambíguas inflam o consumo de tokens do `system` e reduzem a acurácia de escolha da função.
3. **Posicionar o campo de decisão antes do campo de justificativa no esquema JSON:** como a geração é estritamente da esquerda para a direita, um esquema `{"decisao": "...", "raciocinio": "..."}` amostra a decisão antes de processar os passos lógicos, anulando o efeito do *Chain-of-Thought*.
4. **Forçar invocação imediata de ferramenta sem permitir raciocínio prévio em problemas compostos:** obrigar a chamada de função no primeiro turno impede o planejamento da sequência de parâmetros quando a tarefa requer análise intermediária.
