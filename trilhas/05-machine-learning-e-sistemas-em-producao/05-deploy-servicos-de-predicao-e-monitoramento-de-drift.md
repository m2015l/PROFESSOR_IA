# 05 — Deploy, Serviços de Predição e Monitoramento de Drift

**Fonte(s) desta aula:**
- HUYEN, Chip. *Designing Machine Learning Systems: An Iterative Process for Production-Ready Applications*. 1ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulos 7 (*Model Deployment and Prediction Service*, pp. 199–245) e 8 (*Data Distribution Shifts and Monitoring*, pp. 247–272).
- GÉRON, Aurélien. *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow*. 3ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulo 2 (*End-to-End Machine Learning Project*, pp. 39–102).
- FASTAPI. *FastAPI Tutorial — User Guide*. Documentação Oficial, 2026. Disponível em: https://fastapi.tiangolo.com/tutorial/.

---

## 1. Problema e Definição

Implantar um sistema de Machine Learning em produção exige definir a arquitetura de inferência, comprimir o artefato para cumprir limites de latência e monitorar mudanças na distribuição dos dados (*data distribution shifts*). O serviço de predição opera sob dois paradigmas:
1. **Predição em Lote (*Batch Prediction*)**: Predições computadas periodicamente de forma assíncrona sobre grandes volumes usando **batch features** (extraídas de bancos e *data warehouses*) e gravadas em *caches* distribuídos (Redis/DynamoDB). Otimiza **throughput** por vetorização em lote, mas não reage ao contexto em tempo real da sessão do usuário e computa predições para entidades inativas.
2. **Predição Online (*Online Prediction*)**: Predições geradas sob demanda de forma síncrona (via HTTP REST em `FastAPI` ou gRPC) ao receber a requisição. Pode usar apenas *batch features* ou combiná-las com **streaming features** (calculadas em tempo real sobre eventos recentes, como cliques ou transações nos últimos 5 minutos). Unificar as definições entre o pipeline em lote do treino e o de *streaming* da inferência é indispensável para evitar o **train-serving skew**: divergência lógica ou matemática entre o cálculo de uma variável no treino e em produção.

Quanto ao local de execução, a inferência ocorre **na nuvem (*ML on the Cloud*)** — atualização simples e acesso a aceleradores, porém sujeita a latência de rede, custos contínuos e tráfego externo de dados — ou **na borda (*ML on the Edge*)**, executando o modelo no dispositivo do cliente (operação *offline*, zero latência de rede e privacidade local, restrita por memória, bateria e dissipação térmica). Para cumprir SLAs de latência (p95/p99 em milissegundos), aplicam-se quatro técnicas de **compressão de modelos**:
- **Fatoração de Baixo Posto (*Low-Rank Factorization*)**: substitui tensores densos por produtos de matrizes compactas (ex.: convoluções separáveis).
- **Destilação de Conhecimento (*Knowledge Distillation*)**: treina um modelo compacto (*student*) para reproduzir as probabilidades suaves (*soft targets*) de um modelo ou *ensemble* maior (*teacher*).
- **Poda (*Pruning*)**: remove nós arquiteturais ou zera parâmetros de baixa magnitude.
- **Quantização (*Quantization*)**: reduz a precisão numérica de `FP32` (32 bits — 4 bytes) para `FP16`/`BF16` (16 bits — 2 bytes) ou inteiros `INT8` (8 bits — 1 byte) via *Post-Training Quantization* ou *Quantization-Aware Training* (QAT), cortando até 75% da memória e acelerando a inferência.

Em operação, diferentemente de falhas de software tradicionais (exceções explícitas, códigos HTTP 5xx ou *timeouts*), **falhas específicas de ML são silenciosas**: o endpoint responde `200 OK` com latência normal, mas emite predições incorretas. Duas causas estruturais degradam sistemas em produção:
1. **Degenerate Feedback Loops**: ocorrem quando as predições alteram a coleta dos dados futuros usados para retreinar o próprio modelo (comum em recomendação e ranqueamento, onde itens no topo recebem mais cliques pelo **viés de posição**). São diagnosticados pela queda na diversidade das saídas e corrigidos por **aleatorização controlada** (*exploration*) e **positional features** (variáveis indicando a posição de exibição no treino, fixadas em valor neutro na inferência).
2. **Data Distribution Shifts**: divergência entre $P_{\text{train}}(X, Y)$ e $P_{\text{prod}}(X, Y)$. Como $P(X, Y) = P(Y|X)P(X) = P(X|Y)P(Y)$, dividem-se em:
   - **Covariate Shift**: a distribuição das entradas $P(X)$ muda, mas a condicional $P(Y|X)$ permanece constante.
   - **Label Shift (*Prior Probability Shift*)**: a distribuição marginal do alvo $P(Y)$ muda, mas $P(X|Y)$ permanece invariante.
   - **Concept Drift**: a distribuição das entradas $P(X)$ permanece igual, mas a relação condicional $P(Y|X)$ se altera (ex.: choque macroeconômico alterando o risco de inadimplência para o mesmo perfil).

A detecção estatística compara a distribuição de referência (treino) com janelas temporais de produção (deslizantes ou cumulativas) via teste não paramétrico de **Kolmogorov-Smirnov (KS)** ou **Population Stability Index (PSI)**, estruturando o monitoramento em quatro camadas: métricas operacionais (latência p50/p95/p99, CPU/RAM), validação de esquema e *features*, distribuição das predições $\hat{Y}$ e acurácia após chegada dos rótulos reais (*ground truth*).

---

## 2. Aplicação Prática

O código a seguir implementa um serviço de predição *online* com `FastAPI` e `Pydantic` (conforme o *FastAPI Tutorial*), carregando um `Pipeline` completo no gerenciador `lifespan` (evitando *train-serving skew* e leitura de disco por requisição), validando contratos de entrada/saída e expondo auditoria de *Covariate Shift* via **Kolmogorov-Smirnov (`ks_2samp`)** e **PSI**.

```python
from contextlib import asynccontextmanager
from time import perf_counter
from typing import Dict, List
import numpy as np
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from scipy.stats import ks_2samp
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

class TransacaoInput(BaseModel):
    transacao_id: str = Field(..., min_length=3)
    valor_transacao: float = Field(..., gt=0.0, le=1_000_000.0)
    tentativas_1h: int = Field(..., ge=0, le=500)
    idade_conta_dias: float = Field(..., ge=0.0)

class PredicaoOutput(BaseModel):
    transacao_id: str
    probabilidade_fraude: float
    decisao_bloqueio: bool
    versao_modelo: str
    latencia_ms: float

class RelatorioDriftOutput(BaseModel):
    amostras_janela: int
    ks_statistic: float
    ks_p_value: float
    psi_valor: float
    alerta_covariate_shift: bool

def calcular_psi(ref: np.ndarray, atual: np.ndarray, bins: int = 10) -> float:
    limites = np.percentile(ref, np.linspace(0, 100, bins + 1))
    limites[0], limites[-1] = -np.inf, np.inf
    p_ref = np.clip(np.histogram(ref, bins=limites)[0] / len(ref), 1e-4, 1.0)
    p_atu = np.clip(np.histogram(atual, bins=limites)[0] / len(atual), 1e-4, 1.0)
    return float(np.sum((p_atu - p_ref) * np.log(p_atu / p_ref)))

ESTADO: Dict[str, object] = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    rng = np.random.default_rng(42)
    X_ref = np.column_stack([
        rng.lognormal(4.2, 0.8, 2000), rng.poisson(0.5, 2000), rng.uniform(10.0, 1200.0, 2000)
    ])
    y_ref = ((X_ref[:, 0] > 180.0) & (X_ref[:, 1] >= 2)).astype(int)
    pipe = Pipeline([
        ("imp", SimpleImputer(strategy="median")),
        ("scaler", StandardScaler()),
        ("clf", HistGradientBoostingClassifier(max_iter=100, random_state=42)),
    ]).fit(X_ref, y_ref)

    ESTADO.update({"pipe": pipe, "versao": "v1.4.0", "tau": 0.35, "ref_val": X_ref[:, 0], "janela": []})
    yield
    ESTADO.clear()

app = FastAPI(title="Prediction & Drift Service", lifespan=lifespan)

@app.post("/v1/predict", response_model=PredicaoOutput)
def prever(payload: TransacaoInput) -> PredicaoOutput:
    t0 = perf_counter()
    pipe: Pipeline = ESTADO["pipe"]  # type: ignore[assignment]
    x = np.array([[payload.valor_transacao, float(payload.tentativas_1h), payload.idade_conta_dias]])
    prob = float(pipe.predict_proba(x)[0, 1])

    janela: List[float] = ESTADO["janela"]  # type: ignore[assignment]
    janela.append(payload.valor_transacao)
    if len(janela) > 1000:
        janela.pop(0)

    return PredicaoOutput(
        transacao_id=payload.transacao_id,
        probabilidade_fraude=round(prob, 4),
        decisao_bloqueio=prob >= float(ESTADO["tau"]),  # type: ignore[arg-type]
        versao_modelo=str(ESTADO["versao"]),
        latencia_ms=round((perf_counter() - t0) * 1000.0, 3),
    )

@app.get("/v1/monitoring/drift", response_model=RelatorioDriftOutput)
def auditar_drift() -> RelatorioDriftOutput:
    janela: List[float] = ESTADO["janela"]  # type: ignore[assignment]
    if len(janela) < 30:
        raise HTTPException(status_code=400, detail="Mínimo de 30 amostras requerido.")
    ref, atual = np.asarray(ESTADO["ref_val"], dtype=float), np.asarray(janela, dtype=float)
    ks_stat, ks_pval = ks_2samp(ref, atual)
    psi = calcular_psi(ref, atual)
    return RelatorioDriftOutput(
        amostras_janela=len(atual), ks_statistic=round(float(ks_stat), 4),
        ks_p_value=round(float(ks_pval), 6), psi_valor=round(psi, 4),
        alerta_covariate_shift=bool((ks_pval < 0.01) and (psi >= 0.20)),
    )
```

---

## 3. Critério de Decisão

A escolha da arquitetura de inferência, compressão e monitoramento segue critérios de engenharia de sistemas:

| Decisão de Arquitetura em Produção | Condição Operacional / Requisito de SLA | Solução Técnica Recomendada |
| :--- | :--- | :--- |
| **Paradigma de Inferência (Batch vs. Online)** | Escores estáticos diários pré-computáveis vs. decisão dependente do contexto imediato da sessão atual. | Usar **Predição em Lote** gravada em banco chave-valor para demandas estáticas; usar **Predição Online (FastAPI/gRPC)** com *batch* e *streaming features* para decisões sensíveis ao contexto imediato. |
| **Compressão e Aceleração de Inferência** | Latência p99 excede o SLA ou memória do contêiner/dispositivo de borda é restrita. | Aplicar **Quantização (`FP16` ou `INT8`)** para redução imediata de memória e latência; combinar com **Knowledge Distillation** treinando um modelo *student* compacto. |
| **Diagnóstico e Resposta a Distribution Shifts** | Detecção de **Covariate Shift** ($P(X)$ mudou, $P(Y|X)$ estável) vs. **Concept Drift** ($P(Y|X)$ mudou). | Em *Covariate Shift*, retreinar reponderando amostras (*Importance Weighting*); em *Concept Drift*, retreinar com janela temporal curta priorizando dados recentes e atualizar *features*. |
| **Mitigação de Degenerate Feedback Loops** | Sistema de recomendação ou ranqueamento cujas saídas determinam quais itens recebem cliques futuros. | Reservar tráfego (ex.: $1\%$ a $5\%$) para exploração aleatória e incluir **positional features** no treino para separar relevância intrínseca do viés de posição. |

---

## 4. Erros Comuns

- **Reimplementar a extração de *features* em scripts separados entre o treino e a inferência (*Train-Serving Skew*)**: Reescrever transformações manualmente no servidor HTTP gera divergências de arredondamento e tratamento de `NaN` que degradam a acurácia em produção; o artefato serializado deve conter o `Pipeline` completo junto com o modelo.
- **Carregar o modelo do disco a cada requisição HTTP na rota do FastAPI**: Executar `joblib.load` na rota bloqueia o processo, multiplica a latência e esgota a memória sob concorrência; o carregamento deve ocorrer uma única vez no `lifespan`.
- **Monitorar apenas infraestrutura (CPU, RAM, HTTP 200 e latência) assumindo que o modelo está saudável**: Uma falha *upstream* que envie zeros ou unidades trocadas mantém o endpoint respondendo `200 OK` rapidamente enquanto emite predições inválidas; é obrigatório validar limites de esquema e monitorar as distribuições de $X$ e $\hat{Y}$.
- **Usar o teste KS em grandes amostras sem avaliar magnitude de efeito (PSI) nem tamanho da janela**: Com dezenas de milhares de eventos, o p-valor do teste KS dispara alertas por variações irrelevantes (*fadiga de alertas*), enquanto janelas cumulativas longas mascaram mudanças súbitas recentes.
