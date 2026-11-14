# Aula 04 — Avaliação Sistemática, Guardrails e Otimização de Inferência

**Fonte(s) desta aula:**
- HUYEN, Chip. *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Caps. 3–4 (pp. 113–210), Cap. 5 (pp. 235–251), Cap. 7 (pp. 307–362) e Cap. 9 (pp. 405–448).
- BERRYMAN, John; ZIEGLER, Albert. *Prompt Engineering for LLMs*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Cap. 7 (pp. 158–166) e Cap. 10 (pp. 223–244).
- ALAMMAR, Jay; GROOTENDORST, Maarten. *Hands-On Large Language Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Cap. 7 (pp. 200–202) e Cap. 12 (pp. 355–389).

---

## 1. Problema e Definição

O desenvolvimento de sistemas baseados em modelos de fundação é orientado por avaliação (*evaluation-driven development*). Como LLMs geram saídas abertas onde múltiplas respostas distintas são válidas e erros factuais ocorrem em textos gramaticalmente fluentes, a avaliação combina quatro famílias de métricas:

1. **Métricas Intrínsecas de Modelagem de Linguagem:** dada a distribuição real dos dados $P$ e a aprendida pelo modelo $Q$, a **Entropia Cruzada (*Cross-Entropy*)** mede a dificuldade média de predição do próximo token:
   $$H(P, Q) = H(P) + D_{\text{KL}}(P \parallel Q) = -\frac{1}{T}\sum_{t=1}^{T} \log Q(x_t \mid x_{<t})$$
   Para comparar tokenizadores distintos, normaliza-se em **Bits-per-Character (BPC)** ou **Bits-per-Byte (BPB)**. A **Perplexidade ($\text{PPL}$)** é a exponencial da entropia cruzada ($\text{PPL}(P, Q) = 2^{H(P,Q)}$ em bits ou $\exp(H(P,Q))$ em *nats*), medindo a incerteza média por posição. Pós-treinamento (SFT/RLHF) e quantização podem elevar a perplexidade por alterarem a entropia da distribuição.
2. **Avaliação Exata, Funcional e de Similaridade:** em código ou SQL, mede-se a **corretude funcional** (*execution accuracy* / testes unitários `pass@k` e tempo de execução). Contra referências, métricas lexicais (*exact/partial match*, BLEU, ROUGE) medem sobreposição superficial, enquanto a **similaridade semântica** (BERTScore, similaridade de cosseno entre *embeddings*) mede proximidade vetorial. A **consistência factual local** (aderência ao contexto) é avaliada via **Implicação Textual (*Textual Entailment* / NLI)** com classificadores dedicados (`DeBERTa-v3` treinado em MNLI/FEVER/ANLI, classificando pares premissa-hipótese em *entailment*, *contradiction* ou *neutral*) ou decomposição em fatos atômicos verificáveis (**SAFE**).
3. **AI-as-a-Judge e Avaliação SOMA:** utiliza um LLM avaliador sob rubrica explícita, operando de modo **pontual (*pointwise*)** ou **comparativo (*pairwise*)** — base de rankings **Elo** / Bradley-Terry. Para tornar avaliações pontuais consistentes, Berryman e Ziegler (2024) definem o protocolo **SOMA (*Specific questions, Ordinal scaled answers, Multi-aspect coverage*)**: decompor o julgamento em critérios específicos (Relevância, Veracidade, Completude — RTC), usar escalas ordinais discretas curtas ($1$ a $5$ com exemplos por nível), declarar a rubrica antes do texto avaliado e omitir que a resposta foi gerada pelo próprio modelo. Juízes de IA sofrem de três vieses principais (Huyen, 2025): **autopreferência (*self-bias*)**, **primeira posição (*first-position bias*)** e **verbosidade (*verbosity bias*)**.
4. **Suítes de Exemplos Offline vs. Avaliação Online:** inicia-se com suítes enxutas ($5$–$20$ casos versionados), expande-se para *harnesses* automatizados com centenas de casos (minerados de histórico, sintéticos por combinação fatorial ou *canned conversations*) e complementa-se com telemetria online (taxas de aceitação e testes A/B).

Quando o prompting atinge seu limite, a escolha entre **RAG** e **Finetuning** depende do modo de falha (Ovadia et al., 2024; Huyen, 2025): **falhas de informação** (dados privados ou recentes) requerem **RAG**; **falhas de comportamento** (formato proprietário, estilo ou redução de *few-shot*) requerem **Finetuning** (*"RAG é para fatos; Finetuning é para forma"*). Enquanto o ajuste completo em FP16 exige memória para pesos, gradientes e estados do Adam ($8N$ bytes mais ativações), o **PEFT** via **LoRA (*Low-Rank Adaptation*, Hu et al., 2021)** congela $W \in \mathbb{R}^{n \times m}$ e treina apenas matrizes de posto baixo $A \in \mathbb{R}^{n \times r}$ e $B \in \mathbb{R}^{r \times m}$ ($r \ll \min(n,m)$):
$$W' = W + \frac{\alpha}{r} A B$$
Na inferência, $AB$ é somado a $W$ com **zero latência extra**. O **QLoRA** (Dettmers et al., 2023) quantiza o modelo base em 4 bits (`NF4`) mantendo adaptadores em `BF16`.

Em **Engenharia de Prompts Defensiva**, sistemas enfrentam **Prompt Extraction**, **Jailbreaking** e **Prompt Injection Direto ou Indireto** (instruções hostis embutidas em dados recuperados). Mitiga-se o risco com **Guardrails** de entrada (filtros de PII, detectores de injeção, isolamento de dados), de modelo (hierarquia de instruções, privilégio mínimo e confirmação humana para ações críticas) e de saída (moderadores como Llama Guard, validadores sintáticos e NLI), calibrando **Taxa de Violação (*Violation Rate*)** versus **Taxa de Falsa Recusa (*False Refusal Rate*)**.

Por fim, a **Otimização de Inferência** atua sobre as duas fases de execução Transformer:
- **Fase de *Prefill*:** processa os tokens de entrada em paralelo populando o KV Cache inicial; é **compute-bound** e define o **TTFT (*Time to First Token*)**.
- **Fase de *Decode*:** gera um token por vez transferindo todos os pesos da memória HBM para as unidades de cálculo; é **memory bandwidth-bound** e define o **TPOT (*Time Per Output Token*)**. A latência total é $\text{TTFT} + \text{TPOT} \times N_{\text{out}}$.
Mede-se a eficiência por **Goodput** (requisições/s que cumprem os SLOs de TTFT e TPOT nos percentis `p50`, `p90` e `p99`), **MFU (*Model FLOP/s Utilization*)** e **MBU (*Model Bandwidth Utilization*)**:
$$\text{MBU} = \frac{N_{\text{params}} \times \text{bytes/param} \times \text{tokens/s}}{\text{Largura de Banda Teórica da GPU}}$$
A memória bruta do **KV Cache** é calculada por:
$$\text{Memória}_{\text{KV}} = 2 \times B \times S \times L \times H \times M$$
onde $B$ é o *batch size*, $S$ o comprimento da sequência, $L$ as camadas, $H$ a dimensão oculta e $M$ os bytes por valor. As otimizações centrais incluem: **Quantização** (FP16/BF16 $\to$ INT8/FP8/INT4), **Speculative Decoding** (modelo *draft* menor propõe $K$ tokens validados em paralelo pelo modelo alvo sem perda de qualidade), **PagedAttention** (KV Cache em páginas não contíguas no vLLM), **Continuous Batching** (substituição imediata de requisições concluídas no lote), **Desagregação Prefill/Decode** e **Prompt Caching** (reuso do KV Cache de prefixos estáticos).

---

## 2. Aplicação Prática

O código a seguir calcula o dimensionamento de memória de inferência (pesos, KV Cache e MBU) e executa avaliação comparativa **AI-as-a-Judge** com inversão de ordem (*position swap*) para neutralizar o viés de primeira posição.

```python
from typing import Callable

def dimensionar_memoria_e_mbu(
    params_bi: float, bytes_param: float, batch: int, seq_len: int,
    camadas: int, dim_oculta: int, tokens_s: float, banda_gpu_gb_s: float,
) -> dict[str, float]:
    n_params = params_bi * 1e9
    pesos_gb = (n_params * bytes_param) / 1e9
    # KV Cache (AI Engineering, Cap. 9): 2 * B * S * L * H * M
    kv_gb = (2 * batch * seq_len * camadas * dim_oculta * bytes_param) / 1e9
    banda_usada = (n_params * bytes_param * tokens_s) / 1e9
    return {
        "pesos_gb": round(pesos_gb, 2),
        "kv_cache_gb": round(kv_gb, 2),
        "total_gb": round(pesos_gb + kv_gb, 2),
        "mbu_pct": round((banda_usada / banda_gpu_gb_s) * 100.0, 2),
    }

def juiz_comparativo_sem_vies_posicao(
    pergunta: str, resp_a: str, resp_b: str, avaliador_fn: Callable[[str, str, str], str]
) -> str:
    """Inverte (A, B) e (B, A) para eliminar o first-position bias."""
    v1 = avaliador_fn(pergunta, resp_a, resp_b)
    v2 = avaliador_fn(pergunta, resp_b, resp_a)
    if v1 == "PRIMEIRA" and v2 == "SEGUNDA":
        return "VENCEDOR_A"
    if v1 == "SEGUNDA" and v2 == "PRIMEIRA":
        return "VENCEDOR_B"
    return "EMPATE_OU_VIES_DE_POSICAO"

# Llama-2-13B em FP16 (2 bytes), batch=32, seq=2048, L=40, H=5120 em A100 (2000 GB/s)
print(dimensionar_memoria_e_mbu(13.0, 2.0, 32, 2048, 40, 5120, 50.0, 2000.0))
```

---

## 3. Critério de Decisão

| Desafio de Engenharia | Solução Recomendada | Justificativa Técnica |
| :--- | :--- | :--- |
| **Alucinação sobre dados privados ou fatos posteriores ao corte de treino** | **RAG** + verificação NLI de consistência factual local | Injeta evidências atualizadas no contexto sem degradar capacidades gerais do modelo, superando o *finetuning* em precisão factual. |
| **Falha em aderir a formato/estilo proprietário ou alto custo de *few-shot*** | **PEFT com LoRA / QLoRA** (ou *Distillation*) | Adapta formato e distribuição prévia com centenas a poucos milhares de exemplos sem adicionar latência após a fusão de $A$ e $B$. |
| **TPOT elevado na fase *decode* em modelo grande com FLOPs ociosos** | **Quantização (INT8/INT4)** + **Speculative Decoding** | Reduzir bytes por parâmetro acelera a leitura da HBM (*bandwidth-bound*) e o *Speculative Decoding* valida múltiplos tokens em paralelo. |
| **Alto TTFT e custo em prompts com instruções de sistema e exemplos fixos** | **Prompt Caching** com prefixo estático imutável | Reutiliza os tensores $\mathbf{K}$ e $\mathbf{V}$ do prefixo entre chamadas, evitando o recálculo da fase de *prefill* para os tokens estáticos. |

---

## 4. Erros Comuns

1. **Posicionar variáveis dinâmicas ou timestamps no início do prompt de sistema:** como o **Prompt Caching** exige correspondência exata de prefixo no KV Cache, alterações nos primeiros tokens invalidam o cache restante; dados variáveis devem ficar ao final.
2. **Usar AI-as-a-Judge sem versionar o prompt, sem inverter a ordem em comparações pareadas e com escalas contínuas:** LLMs juízes têm baixa calibração em escalas contínuas ($0$–$100$) e forte viés de posição e verbosidade; alterar o juiz invalida a série histórica.
3. **Iniciar pelo *finetuning* antes de construir um pipeline de avaliação e esgotar o prompting:** o ajuste fino sem linha de base eleva custos, pode degradar tarefas adjacentes (*alignment tax*) e não corrige lacunas de fatos dinâmicos.
4. **Converter pesos `BF16` nativos para `FP16` sem checar a faixa dinâmica:** o `FP16` possui $5$ bits de expoente contra $8$ do `BF16`, causando *overflow* para infinito (`INF`) em ativações de alta magnitude.
