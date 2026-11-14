# 04 — Avaliação Offline, Validação e Métricas de Negócio

**Fonte(s) desta aula:**
- HUYEN, Chip. *Designing Machine Learning Systems: An Iterative Process for Production-Ready Applications*. 1ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulos 2 (*Introduction to Machine Learning Systems Design*, pp. 31–60), 4 (*Training Data*, pp. 97–138) e 6 (*Model Development and Offline Evaluation*, pp. 163–198).
- GÉRON, Aurélien. *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow*. 3ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulos 2 (*End-to-End Machine Learning Project*, pp. 39–102), 3 (*Classification*, pp. 103–130) e 4 (*Training Models*, pp. 131–174).
- BRUCE, Peter; BRUCE, Andrew. *Practical Statistics for Data Scientists: 50 Essential Concepts*. 1ª Edição. Sebastopol: O'Reilly Media, 2017. Capítulos 4 (*Regression and Prediction*, pp. 133–180) e 5 (*Classification*, pp. 181–222).

---

## 1. Problema e Definição

A avaliação *offline* verifica se um modelo generaliza fora da amostra e se suas predições geram retorno econômico positivo sem degradar subgrupos operacionais críticos. Nenhuma métrica tem significado sem uma hierarquia de **baselines**: (1) **Random Baseline** (sorteio uniforme ou empírico), (2) **Zero Rule Baseline** (`DummyClassifier`/`DummyRegressor`, predizendo sempre a classe majoritária ou a média/mediana), (3) **Simple Heuristic Baseline** (regra determinística de domínio), (4) **Human Baseline** (desempenho de especialistas humanos) e (5) **Existing Solution Baseline** (sistema legado em produção).

Para estimar o erro *out-of-sample*, a **validação cruzada** deve respeitar a estrutura geradora dos dados: `StratifiedKFold` para dados i.i.d. desbalanceados, `GroupKFold` para múltiplas observações da mesma entidade e `TimeSeriesSplit` (janela expansiva) para séries temporais. O regime de aprendizado é diagnosticado por **Curvas de Aprendizado (*Learning Curves*)**, plotando o erro de treino e de validação em função do tamanho da amostra: se ambas convergem para um erro elevado com intervalo estreito, há **subajuste (*underfitting* / alto viés)** e adicionar mais dados não ajuda (requer maior capacidade ou melhores *features*); se o erro de treino é baixo com grande lacuna (*gap*) até o erro de validação, há **sobreajuste (*overfitting* / alta variância)**, remediável por regularização, redução de complexidade ou mais amostras de treino.

Na **regressão**, a métrica reflete a norma de penalização dos resíduos: a **Raiz do Erro Quadrático Médio ($\text{RMSE} = \sqrt{\frac{1}{m}\sum_{i=1}^m (\hat{y}^{(i)} - y^{(i)})^2}$)** aplica a norma Euclidiana ($\ell_2$), penalizando grandes desvios quadraticamente; o **Erro Absoluto Médio ($\text{MAE} = \frac{1}{m}\sum_{i=1}^m |\hat{y}^{(i)} - y^{(i)}|$)** aplica a norma Manhattan ($\ell_1$), sendo robusto a *outliers*; e o **Coeficiente de Determinação ($R^2 = 1 - \frac{\sum (y^{(i)} - \hat{y}^{(i)})^2}{\sum (y^{(i)} - \bar{y})^2}$)** mede a fração da variância explicada frente à média.

Na **classificação binária**, as métricas derivam da **Matriz de Confusão** — Verdadeiros Positivos ($TP$), Falsos Positivos ($FP$), Verdadeiros Negativos ($TN$) e Falsos Negativos ($FN$) — sob um limiar $\tau$:
- **Precisão (*Precision*)**: $\frac{TP}{TP + FP}$ (fração dos preditos positivos que são positivos reais).
- **Revocação (*Recall* / Sensibilidade / TPR)**: $\frac{TP}{TP + FN}$ (fração dos positivos reais capturados).
- **Especificidade (TNR)**: $\frac{TN}{TN + FP} = 1 - \text{FPR}$, onde $\text{FPR} = \frac{FP}{TN + FP}$ é a taxa de falsos positivos.
- **$F_1$-Score**: média harmônica $\frac{2}{\frac{1}{\text{Precision}} + \frac{1}{\text{Recall}}} = \frac{TP}{TP + \frac{FN + FP}{2}}$.

Variar $\tau$ impõe o **trade-off Precisão-Revocação**, expresso pela **Curva ROC** ($\text{TPR}$ versus $\text{FPR}$) e pela **Curva Precision-Recall (PR)**. Sob desbalanceamento severo ($TN \gg FP$), a $\text{FPR}$ permanece baixa mesmo com muitos falsos positivos, tornando a **ROC AUC otimista demais**; nesses cenários, exige-se a **Curva PR (PR-AUC / Average Precision)**. Para conectar probabilidades a **métricas financeiras de negócio**, usam-se **Curvas de Lift / Cumulative Gains** e a **Maximização do Retorno Financeiro Esperado**, selecionando $\tau^*$ que maximiza $\sum_{i} \mathbb{I}(\hat{p}^{(i)} \ge \tau) \cdot [\hat{p}^{(i)} V_{TP} + (1 - \hat{p}^{(i)}) C_{FP}]$. Essa equação exige probabilidades reais auditadas por **Curvas de Calibração**: como árvores, *boosting* e Naive Bayes distorcem probabilidades, aplica-se **Platt Scaling** (sigmoide) ou **Regressão Isotônica** (`CalibratedClassifierCV`).

Por fim, antes do deploy, executam-se duas validações estruturais:
1. **Testes Comportamentais**: **Perturbação** (robustez a ruído), **Invariância** (alterar atributos protegidos como gênero ou formatação não deve mudar a predição) e **Expectativa Direcional** (variações monotônicas, como elevar o endividamento mantendo demais variáveis fixas, devem mover a predição na direção esperada).
2. **Avaliação Baseada em Fatias (*Slice-Based Evaluation*)**: Métricas globais ocultam falhas em subgrupos críticos e expõem ao **Paradoxo de Simpson** (um modelo supera outro no agregado global, mas perde em cada subgrupo analisado separadamente).

---

## 2. Aplicação Prática

O código a seguir calibra probabilidades via *Platt Scaling* (`CalibratedClassifierCV`), seleciona o limiar ótimo $\tau^*$ maximizando o retorno líquido em uma matriz de custos e benefícios, executa auditoria por fatias (*slice-based evaluation*) e aplica um teste comportamental de expectativa direcional.

```python
import numpy as np
import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.datasets import make_classification
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import average_precision_score, brier_score_loss, f1_score
from sklearn.model_selection import train_test_split

# 1. Concessão de crédito com classe positiva desbalanceada (8% inadimplência)
X, y = make_classification(
    n_samples=6000, n_features=8, n_informative=6, n_redundant=1,
    weights=[0.92, 0.08], flip_y=0.02, random_state=42
)
df = pd.DataFrame(X, columns=[f"feat_{i}" for i in range(8)])
rng = np.random.default_rng(42)
df["canal"] = rng.choice(["mobile_app", "web_desktop", "parceiro_api"], size=len(df), p=[0.60, 0.30, 0.10])
df["comprometimento_renda"] = np.clip(df["feat_0"] * 0.15 + 0.35, 0.05, 0.95)

X_train, X_val, y_train, y_val = train_test_split(df, y, test_size=0.25, stratify=y, random_state=42)
cols_num = [f"feat_{i}" for i in range(8)] + ["comprometimento_renda"]

# 2. Zero-Rule Baseline e Calibração de Probabilidades (Platt Scaling / Sigmoid)
zero_rule = DummyClassifier(strategy="prior").fit(X_train[cols_num], y_train)
modelo_cal = CalibratedClassifierCV(
    estimator=HistGradientBoostingClassifier(max_iter=150, random_state=42), method="sigmoid", cv=5
).fit(X_train[cols_num], y_train)

probs_val = modelo_cal.predict_proba(X_val[cols_num])[:, 1]
pr_zero = average_precision_score(y_val, zero_rule.predict_proba(X_val[cols_num])[:, 1])
pr_mod = average_precision_score(y_val, probs_val)
brier = brier_score_loss(y_val, probs_val)

# 3. Otimização do Limiar de Decisão por Matriz de Custo-Benefício Financeiro
GANHO_TP, CUSTO_FP, CUSTO_FN = 800.0, -120.0, -800.0
limiares = np.linspace(0.05, 0.90, 86)
retornos = []
for tau in limiares:
    preds = (probs_val >= tau).astype(int)
    tp = np.sum((preds == 1) & (y_val == 1))
    fp = np.sum((preds == 1) & (y_val == 0))
    fn = np.sum((preds == 0) & (y_val == 1))
    retornos.append((tp * GANHO_TP) + (fp * CUSTO_FP) + (fn * CUSTO_FN))

tau_otimo = limiares[int(np.argmax(retornos))]
lucro_max = float(np.max(retornos))

# 4. Avaliação Baseada em Fatias (Slice-Based Evaluation por canal)
X_eval = X_val.assign(y_true=y_val, y_prob=probs_val, y_pred=(probs_val >= tau_otimo).astype(int))
slices = {
    c: {"n": len(g), "PR_AUC": round(average_precision_score(g["y_true"], g["y_prob"]), 4),
        "F1": round(f1_score(g["y_true"], g["y_pred"], zero_division=0), 4)}
    for c, g in X_eval.groupby("canal")
}

# 5. Teste de Expectativa Direcional: elevar comprometimento_renda não deve reduzir risco médio
base_t = X_val[cols_num].iloc[:200].copy()
pert_t = base_t.assign(comprometimento_renda=np.clip(base_t["comprometimento_renda"] + 0.25, 0.0, 1.0))
delta_risco = float(np.mean(modelo_cal.predict_proba(pert_t)[:, 1] - modelo_cal.predict_proba(base_t)[:, 1]))

print(f"PR-AUC ZeroRule: {pr_zero:.4f} | Calibrado: {pr_mod:.4f} | Brier: {brier:.4f}")
print(f"Limiar Ótimo: tau* = {tau_otimo:.2f} -> Retorno: R$ {lucro_max:,.2f}")
print(f"Slices: {slices} | Delta Risco Direcional: {delta_risco:+.4f}")
```

---

## 3. Critério de Decisão

A seleção das métricas e procedimentos de validação deve refletir a assimetria de custos do negócio e a prevalência real da classe alvo:

| Contexto de Avaliação | Métrica Inadequada (Evitar) | Métrica e Procedimento Recomendados |
| :--- | :--- | :--- |
| **Classificação com Desbalanceamento Severo ($< 5\%$ positivos)** | Acurácia global e ROC AUC isolada (infladas pelo alto volume de Verdadeiros Negativos $TN$). | **PR-AUC (*Average Precision*)**, *Recall@Precision=k%* e Curva de *Lift* nos decis superiores. |
| **Decisão Automatizada Baseada em Valor Monetário** | Limiar padrão fixo $\tau = 0{,}50$ sobre *scores* não calibrados. | Calibrar probabilidades com `CalibratedClassifierCV` (monitorando *Brier Score*) e escolher $\tau^*$ que maximiza a utilidade financeira $U(\tau)$. |
| **Regressão com Erros Extremos Críticos vs. Outliers** | Usar $R^2$ isolado sem medir o erro na unidade física da resposta. | Usar **RMSE** quando grandes desvios têm custo quadrático; usar **MAE** ou perda de Huber quando *outliers* anômalos não devem dominar o gradiente. |
| **Aprovação para Deploy (Go/No-Go Gate)** | Comparar apenas a média agregada global entre o candidato e o modelo atual. | Exigir aprovação simultânea em (1) métrica global, (2) **Slice-Based Evaluation** em subgrupos críticos e (3) testes de invariância e expectativa direcional. |

---

## 4. Erros Comuns

- **Adotar o limiar padrão $\tau = 0{,}50$ do método `.predict()` sob custos assimétricos ou desbalanceamento**: O custo de um Falso Negativo raramente iguala o de um Falso Positivo; fixar $\tau = 0{,}50$ ignora a matriz financeira e a prevalência real.
- **Usar `.predict_proba()` de árvores, Random Forests, Gradient Boosting ou Naive Bayes como probabilidade real sem calibração**: Modelos de árvores e Naive Bayes distorcem as probabilidades em direção a patamares intermediários ou extremos (0 e 1); usá-las em cálculos de valor esperado exige calibração prévia em partição disjunta.
- **Aprovar modelos apenas pela métrica global agregada (Paradoxo de Simpson e cegueira a fatias)**: Um modelo pode subir o F1 global melhorando na fatia majoritária de baixo valor enquanto degrada severamente clientes corporativos ou um canal específico.
- **Escolher hiperparâmetros e limiar $\tau^*$ sobre o conjunto de teste final**: Otimizar o ponto de corte na curva PR usando o conjunto de teste vaza informação para a operação; calibração e seleção de limiar devem ocorrer exclusivamente no conjunto de validação.
