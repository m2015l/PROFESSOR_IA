# 01 — Anatomia de Projetos de ML e Curadoria de Dados de Treino

**Fonte(s) desta aula:**
- HUYEN, Chip. *Designing Machine Learning Systems: An Iterative Process for Production-Ready Applications*. 1ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulos 1 (*Overview of Machine Learning Systems*, pp. 1–30), 2 (*Introduction to Machine Learning Systems Design*, pp. 31–60) e 4 (*Training Data*, pp. 97–138).
- GÉRON, Aurélien. *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow*. 3ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulo 1 (*The Machine Learning Landscape*, pp. 3–38), Capítulo 2 (*End-to-End Machine Learning Project*, pp. 39–102) e Apêndice A (*Machine Learning Project Checklist*, pp. 779–784).
- SARKIS, Anthony. *Training Data for Machine Learning: Human Supervision from Annotation to Data Science*. 1ª Edição. Sebastopol: O'Reilly Media, 2023. Capítulos 1 (*Training Data Introduction*, pp. 1–30), 3 (*Schema*, pp. 67–98), 5 (*Workflow*, pp. 129–164) e 6 (*Theories, Concepts, and Maintenance*, pp. 165–202).

---

## 1. Problema e Definição

Um sistema de Machine Learning (ML) em produção não é apenas um algoritmo ajustado sobre uma tabela estática; ele é um sistema de software integrado por fontes de dados, pipelines de transformação, infraestrutura de treinamento, serviço de inferência, monitoramento e ciclos de retroalimentação (*feedback loops*). Enquanto o ambiente de pesquisa opera com conjuntos de dados estáticos, foco em acurácia máxima em *leaderboards* e alta latência tolerada, o ambiente de produção envolve múltiplos *stakeholders* com requisitos conflitantes, dados ruidosos em mutação contínua e exigências estritas de baixa latência e alto *throughput*. Todo sistema de ML em produção deve satisfazer quatro requisitos: **confiabilidade** (operar corretamente diante de falhas de hardware, software ou dados corrompidos), **escalabilidade** (crescer em capacidade computacional, tráfego e volume de artefatos), **manutenibilidade** (permitir colaboração entre engenharia de dados, ML e DevOps com reprodutibilidade de código, dados e parâmetros) e **adaptabilidade** (evoluir rapidamente frente a mudanças de distribuição e de negócio).

O ciclo iterativo inicia no **enquadramento do problema** (*problem framing*), traduzindo objetivos de negócio (aumentar receita líquida ou reduzir perdas por fraude) em objetivos matemáticos acionáveis (estimar $P(Y=1|X)$ em classificação, minimizar erro quadrático em regressão ou ordenar itens em *learning-to-rank*). A taxonomia técnica classifica os sistemas de ML por quatro critérios:
1. **Supervisão no treinamento**: supervisionado (rótulos explícitos), não supervisionado (clusterização, redução de dimensionalidade e detecção de anomalias), semissupervisionado, autossupervisionado (*self-supervised*) e aprendizado por reforço.
2. **Aprendizado incremental**: em lote (*batch/offline learning*, treinado sobre dados acumulados e implantado como artefato fixo) versus incremental (*online/out-of-core learning*, atualizado continuamente por *mini-batches*).
3. **Generalização**: baseado em instâncias (similaridade geométrica) versus baseado em modelos (estimação de parâmetros $\theta$ que minimizam uma perda $\mathcal{L}$).
4. **Cardinalidade de objetivos**: perda única versus desacoplamento em múltiplos modelos especializados (ex.: um modelo estimando probabilidade de clique e outro estimando conversão financeira, combinados no serviço de inferência).

Na engenharia de dados de treinamento centrada em dados (*Data-Centric AI*), o comportamento do modelo é determinado pela amostragem e pela supervisão codificada nos dados. O **esquema de anotação** (*annotation schema*) define classes, atributos e relações espaciais ou temporais, exigindo alinhamento estrito na cadeia `problema de negócio -> esquema -> dados brutos -> instruções de anotação`. Na seleção de registros, distingue-se **amostragem não probabilística** (conveniência, *snowball*, julgamento ou cota — sujeitas a viés de seleção) de **amostragem probabilística**: aleatória simples, **estratificada** (particiona a população em estratos mutuamente exclusivos garantindo representatividade de subgrupos), ponderada, **Reservoir Sampling** (seleciona $k$ amostras uniformemente de um fluxo contínuo de tamanho desconhecido substituindo elementos com probabilidade $k/n$ no $n$-ésimo item) e **Importance Sampling** (amostra de $q(x)$ reponderando por $p(x)/q(x)$).

Quanto aos rótulos, distinguem-se **rótulos naturais** (extraídos de eventos reais como cliques ou compras, dependentes do comprimento do *feedback loop* temporal) e **anotação manual**. Combinar múltiplas fontes ou anotadores gera **multiplicidade de rótulos**, exigindo rastreamento de **linhagem de dados** (*data lineage*) por amostra para auditar vieses. A garantia de qualidade (QA) na anotação humana utiliza **conjuntos Gold Standard** (exemplos validados por especialistas inseridos ocultamente para medir a acurácia de cada anotador) e **ciclos de revisão estruturados** (*review loops* em grafo acíclico dirigido), superiores ao consenso cego sob instruções ambíguas. Diante de escassez de rótulos, aplicam-se: **supervisão fraca** (*weak supervision* com funções de rotulagem programática — *Labeling Functions* — baseadas em heurísticas e expressões regulares cujos conflitos são desruidados), **semissupervisão**, **Transfer Learning** e **Active Learning** (anotação prioritária das instâncias de maior incerteza na fronteira de decisão ou maior discordância em *Query-by-Committee*). Por fim, o **desbalanceamento de classes** é mitigado por métricas sensíveis à classe rara, reamostragem no treino (*Tomek links* ou SMOTE) ou ajuste na função de perda (**Cost-Sensitive Learning** com matriz $C_{ij}$, **Class-Balanced Loss** ponderada por $(1-\beta)/(1-\beta^n)$ e **Focal Loss** $(1-p_t)^\gamma \log(p_t)$).

---

## 2. Aplicação Prática

O código a seguir executa: (1) particionamento de treino e teste via **amostragem estratificada** (`StratifiedShuffleSplit`) sobre um atributo contínuo discretizado, e (2) combinação de **funções de rotulagem programática** (*weak supervision*) auditadas contra um subconjunto *Gold Standard* e cálculo de pesos para aprendizado sensível ao custo.

```python
import numpy as np
import pandas as pd
from sklearn.metrics import accuracy_score, cohen_kappa_score
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.utils.class_weight import compute_class_weight

# 1. Criação de conjunto de teste isolado via Amostragem Estratificada
rng = np.random.default_rng(seed=42)
n = 2000
df = pd.DataFrame({
    "valor": rng.lognormal(mean=4.5, sigma=1.1, size=n),
    "falhas_24h": rng.poisson(lam=0.4, size=n),
    "pais_divergente": rng.binomial(n=1, p=0.08, size=n),
    "dispositivo_novo": rng.binomial(n=1, p=0.15, size=n),
})
df["estrato"] = pd.cut(df["valor"], bins=[0.0, 50.0, 150.0, 400.0, 1000.0, np.inf], labels=[1, 2, 3, 4, 5])

splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.20, random_state=42)
for train_idx, test_idx in splitter.split(df, df["estrato"]):
    train_df = df.iloc[train_idx].drop(columns=["estrato"]).copy()
    test_df = df.iloc[test_idx].drop(columns=["estrato"]).copy()

# 2. Supervisão Fraca (Labeling Functions): 1=Fraude, 0=Legítima, -1=Abstenção
ABSTENCAO = -1

def lf_internacional_alto_valor(r: pd.Series) -> int:
    return 1 if (r["valor"] > 500.0 and r["pais_divergente"] == 1) else ABSTENCAO

def lf_falhas_dispositivo(r: pd.Series) -> int:
    if r["falhas_24h"] >= 2 and r["dispositivo_novo"] == 1:
        return 1
    if r["falhas_24h"] == 0 and r["dispositivo_novo"] == 0 and r["valor"] < 120.0:
        return 0
    return ABSTENCAO

def lf_recorrente_baixo_risco(r: pd.Series) -> int:
    return 0 if (r["pais_divergente"] == 0 and r["falhas_24h"] == 0 and r["valor"] < 300.0) else ABSTENCAO

lfs = [lf_internacional_alto_valor, lf_falhas_dispositivo, lf_recorrente_baixo_risco]
votos_mat = np.column_stack([train_df.apply(lf, axis=1).to_numpy() for lf in lfs])

rotulos, mask_cobertura = [], []
for votos in votos_mat:
    validos = votos[votos != ABSTENCAO]
    rotulos.append(int(np.mean(validos) >= 0.5) if len(validos) > 0 else ABSTENCAO)
    mask_cobertura.append(len(validos) > 0)

train_df["rotulo_lf"] = rotulos
df_rotulado = train_df[mask_cobertura].copy()

# 3. Controle de Qualidade (QA) contra subconjunto Gold Standard validado por especialistas
gold_sub = df_rotulado.iloc[:100]
gold_true = ((gold_sub["valor"] > 450.0) & (gold_sub["pais_divergente"] == 1) | (gold_sub["falhas_24h"] >= 2)).astype(int)
acc_qa = accuracy_score(gold_true, gold_sub["rotulo_lf"])
kappa_qa = cohen_kappa_score(gold_true, gold_sub["rotulo_lf"])

# 4. Pesos balanceados para Cost-Sensitive Learning
classes = np.unique(df_rotulado["rotulo_lf"])
pesos = compute_class_weight("balanced", classes=classes, y=df_rotulado["rotulo_lf"].to_numpy())
print(f"Cobertura LFs: {len(df_rotulado)/len(train_df):.2%} | QA Acc: {acc_qa:.4f} | Kappa: {kappa_qa:.4f}")
print(f"Pesos de classe: {dict(zip(classes, np.round(pesos, 4)))}")
```

---

## 3. Critério de Decisão

Antes de construir um sistema de ML, avalie sua viabilidade técnica e econômica:
- **Não utilize Machine Learning** quando regras determinísticas ou consultas SQL resolverem o problema exatamente, quando o custo de infraestrutura superar o ganho financeiro incremental sobre uma heurística simples, quando atributos preditivos não estiverem disponíveis na inferência ou quando erros pontuais causarem danos inaceitáveis sem contenção determinística.
- **Utilize Machine Learning** quando o problema envolver padrões complexos de alta dimensionalidade impossíveis de codificar manualmente, quando a distribuição mudar continuamente exigindo adaptação (fraude, recomendação, precificação dinâmica) e quando houver dados representativos e escala de inferência que justifique o investimento.

| Dimensão de Curadoria | Cenário Operacional | Decisão Técnica Recomendada |
| :--- | :--- | :--- |
| **Particionamento e Amostragem** | População com subgrupos críticos ou classes raras; ou fluxo contínuo sem tamanho fixo. | Usar **amostragem estratificada** (`StratifiedShuffleSplit`) em bases finitas e **Reservoir Sampling** em *streams*. Nunca usar amostragem por conveniência. |
| **Estratégia de Rotulagem** | Dados brutos abundantes, ausência de rótulos naturais imediatos e alto custo de anotação manual. | Combinar **Supervisão Fraca** (*Labeling Functions* versionadas) para escala inicial com **Active Learning** e revisão humana sobre subconjunto *Gold Standard*. |
| **Desbalanceamento Severo** | Classe positiva rara ($< 1\%$) onde *undersampling* descartaria informação crítica da classe majoritária. | Manter a distribuição real na validação/teste e treinar com **Cost-Sensitive Learning**, **Class-Balanced Loss** ou **Focal Loss**. |

---

## 4. Erros Comuns

- **Explorar a base completa antes de separar o conjunto de teste (*Data Snooping Bias*)**: Analisar correlações e selecionar modelos inspecionando 100% dos dados sobreajusta escolhas arquiteturais às amostras do teste. O teste deve ser isolado imediatamente após a ingestão bruta.
- **Escalar anotação manual sem validar o esquema em lote piloto**: Disparar milhares de tarefas sem validar o alinhamento `problema -> esquema -> dados brutos -> instruções` gera rótulos inconsistentes que inviabilizam o aprendizado.
- **Confiar em consenso majoritário sem *Gold Standard* nem linhagem de dados**: Instruções ambíguas levam múltiplos anotadores ao mesmo erro sistemático; além disso, fundir fontes sem coluna de linhagem (*data lineage*) impede expurgar lotes defeituosos.
- **Aplicar *oversampling* (SMOTE) ou *undersampling* na validação ou no teste**: Alterar a proporção de classes fora do treino distorce as probabilidades a priori $P(Y)$, invalida a calibração e gera métricas artificiais que colapsam em produção.
