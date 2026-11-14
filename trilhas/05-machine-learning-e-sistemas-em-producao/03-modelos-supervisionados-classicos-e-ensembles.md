# 03 — Modelos Supervisionados Clássicos e Ensembles

**Fonte(s) desta aula:**
- GÉRON, Aurélien. *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow*. 3ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulos 4 (*Training Models*, pp. 131–174), 5 (*Support Vector Machines*, pp. 175–194), 6 (*Decision Trees*, pp. 195–210) e 7 (*Ensemble Learning and Random Forests*, pp. 211–236).
- BRUCE, Peter; BRUCE, Andrew. *Practical Statistics for Data Scientists: 50 Essential Concepts*. 1ª Edição. Sebastopol: O'Reilly Media, 2017. Capítulos 4 (*Regression and Prediction*, pp. 133–180), 5 (*Classification*, pp. 181–222) e 6 (*Statistical Machine Learning*, pp. 223–258).
- HUYEN, Chip. *Designing Machine Learning Systems: An Iterative Process for Production-Ready Applications*. 1ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulo 6 (*Model Development and Offline Evaluation*, pp. 163–198).

---

## 1. Problema e Definição

Selecionar e treinar um modelo supervisionado exige equilibrar viés (*bias*), variância (*variance*), custo computacional e premissas sobre o espaço de *features*. Na **Regressão Linear Múltipla**, modela-se a resposta contínua como $\hat{y} = \theta_0 + \sum_{j=1}^p \theta_j x_j = \mathbf{x}^T \boldsymbol{\theta}$, estimando $\hat{\boldsymbol{\theta}}$ via Mínimos Quadrados Ordinários (**OLS**) para minimizar a soma dos quadrados dos resíduos $\text{RSS} = \sum_{i=1}^m (y^{(i)} - \hat{y}^{(i)})^2$ (ou $\text{MSE} = \frac{1}{m}\text{RSS}$). Existem dois métodos numéricos de estimação:
1. **Solução analítica fechada**: a Equação Normal $\hat{\boldsymbol{\theta}} = (\mathbf{X}^T\mathbf{X})^{-1}\mathbf{X}^T\mathbf{y}$ ou a pseudo-inversa via Decomposição em Valores Singulares (**SVD**, usada por `LinearRegression`), que escala linearmente com $m$ ($O(m)$), mas entre $O(p^{2.4})$ e $O(p^3)$ com o número de variáveis $p$.
2. **Descida de Gradiente (*Gradient Descent*)**: atualização iterativa $\boldsymbol{\theta}^{(\text{next})} = \boldsymbol{\theta} - \eta \nabla_{\boldsymbol{\theta}}\text{MSE}(\boldsymbol{\theta})$ nas variantes *Batch* (todas as $m$ amostras por passo), *Stochastic* (`SGDRegressor`, 1 amostra por passo com decaimento da taxa $\eta$) ou *Mini-batch*.

O diagnóstico estatístico linear avalia **multicolinearidade** (preditores correlacionados que inflam a variância de $\hat{\boldsymbol{\theta}}$), **variáveis de confusão** (*confounding variables*, omissões que enviesam coeficientes), **heterocedasticidade** (variância não constante dos erros), **resíduos parciais** (não linearidades tratáveis por polinômios, *splines* ou **GAMs**) e **observações influentes**, medidas pela **alavancagem** (*hat-value* $h_i$) e pela **distância de Cook** (crítica se $> 4/(m - p - 1)$). Para controlar a variância sem seleção discreta (*stepwise* via AIC), aplica-se **regularização**: **Ridge ($\ell_2$)** soma $\frac{\alpha}{2}\sum_{j=1}^p \theta_j^2$ à perda; **Lasso ($\ell_1$)** soma $\alpha \sum_{j=1}^p |\theta_j|$, zerando pesos irrelevantes e gerando esparsidade; e **Elastic Net** combina ambas por $r \in [0, 1]$: $\mathcal{L}(\boldsymbol{\theta}) = \text{MSE}(\boldsymbol{\theta}) + r\alpha\sum_{j=1}^p |\theta_j| + \frac{1-r}{2}\alpha\sum_{j=1}^p \theta_j^2$, preferida sobre o Lasso puro quando $p > m$ ou sob colinearidade.

Na **classificação supervisionada**, destacam-se quatro famílias clássicas:
- **Naive Bayes e Análise Discriminante Linear (LDA)**: O Naive Bayes assume independência condicional entre preditores dada a classe; a LDA estima a matriz de covariância conjunta assumindo normalidade multivariada e homocedasticidade, maximizando a razão entre variância entre classes e intra-classe.
- **Regressão Logística e Softmax**: Modela o *log-odds* (*logit*) como $\log\left(\frac{p}{1-p}\right) = \mathbf{x}^T\boldsymbol{\theta}$, resultando em $\hat{p} = \sigma(\mathbf{x}^T\boldsymbol{\theta}) = \frac{1}{1 + \exp(-\mathbf{x}^T\boldsymbol{\theta})}$, estimada por **Máxima Verossimilhança (MLE)** minimizando a perda de entropia cruzada (*log loss*), estendida para multiclasse via **Softmax**.
- **Support Vector Machines (SVM)**: Busca o hiperplano de margem máxima com margem suave controlada por $C$ (menor $C$ alarga a margem e regulariza mais) e trata não linearidades via *kernels* polinomial ou RBF Gaussiano $\phi_\gamma(\mathbf{x}, \boldsymbol{\ell}) = \exp(-\gamma \|\mathbf{x} - \boldsymbol{\ell}\|^2)$.
- **K-Nearest Neighbors (KNN)**: Decide pela vizinhança segundo distância Euclidiana, Manhattan ou de **Mahalanobis** (que corrige correlações usando a matriz de covariância).

As **Árvores de Decisão** usam o algoritmo **CART**, particionando o espaço binária e recursivamente de forma gulosa (*greedy*): em cada nó, escolhe o par $(k, t_k)$ de variável $k$ e limiar $t_k$ que minimiza $J(k, t_k) = \frac{m_{\text{left}}}{m}G_{\text{left}} + \frac{m_{\text{right}}}{m}G_{\text{right}}$. Na classificação, a impureza $G$ usa o **índice de Gini** $G_i = 1 - \sum_{k=1}^K p_{i,k}^2$ ou a **entropia** $H_i = -\sum_{k=1, p_{i,k}\neq 0}^K p_{i,k}\log_2(p_{i,k})$; na regressão, usa o **MSE** intra-nó. Árvores dispensam escalonamento, mas geram cortes ortogonais aos eixos e possuem alta variância se não regularizadas via `max_depth`, `min_samples_split`, `min_samples_leaf` ou poda (`ccp_alpha`).

Os métodos de **Ensemble** combinam múltiplos estimadores em três arquiteturas:
1. **Bagging, Pasting e Random Forests (Redução de Variância em Paralelo)**: O *Bagging* amostra o treino **com reposição** (*bootstrap*, usando $\approx 63{,}2\%$ dos dados por árvore e reservando os $\approx 36{,}8\%$ restantes para avaliação **Out-of-Bag — OOB**), enquanto o *Pasting* amostra **sem reposição**. As **Random Forests** sorteiam também um subconjunto de $k \approx \sqrt{p}$ variáveis em cada nó, descorrelacionando as árvores; as **Extra-Trees** sorteiam limiares aleatórios. A importância de variáveis deve ser medida por **Permutação** (em dados OOB ou validação) em vez de apenas decréscimo de Gini.
2. **Boosting (Redução de Viés Sequencial)**: O **AdaBoost** repondera instâncias erradas, enquanto o **Gradient Boosting** ajusta cada nova árvore sobre os **pseudo-resíduos** (gradiente negativo da perda) acumulados. Em produção dominam o **Stochastic Gradient Boosting / XGBoost** e o `HistGradientBoosting` (discretização em 256 *bins* com complexidade $O(p \cdot b)$ e suporte nativo a `NaN`), controlados por `learning_rate` (`eta`), `subsample`, `colsample_bytree` e regularização $\ell_1$ (`alpha`) e $\ell_2$ (`lambda`).
3. **Stacking**: Treina um **meta-estimador (*blender*)** sobre as predições *out-of-fold* geradas via validação cruzada pelos modelos de primeiro nível.

---

## 2. Aplicação Prática

O código a seguir compara e combina Regressão Logística regularizada com *Elastic Net*, `RandomForestClassifier` com validação *Out-of-Bag* (`oob_score=True`), `HistGradientBoostingClassifier` regularizado e `StackingClassifier` (*out-of-fold*), extraindo a importância por permutação no conjunto de teste.

```python
import numpy as np
from sklearn.datasets import make_classification
from sklearn.ensemble import HistGradientBoostingClassifier, RandomForestClassifier, StackingClassifier
from sklearn.inspection import permutation_importance
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold, train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

X, y = make_classification(
    n_samples=3000, n_features=20, n_informative=10, n_redundant=6,
    n_clusters_per_class=2, flip_y=0.04, weights=[0.75, 0.25], random_state=42
)
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, stratify=y, random_state=42)

# 1. Modelo Linear com penalização Elastic Net (L1 + L2)
pipe_enet = make_pipeline(
    StandardScaler(),
    LogisticRegression(penalty="elasticnet", solver="saga", l1_ratio=0.5, C=0.5, max_iter=2000, random_state=42),
)

# 2. Random Forest com estimativa Out-of-Bag (OOB)
rf_clf = RandomForestClassifier(
    n_estimators=300, max_features="sqrt", min_samples_leaf=5, oob_score=True, n_jobs=-1, random_state=42
).fit(X_train, y_train)

# 3. Histogram-Based Gradient Boosting com regularização L2 e Early Stopping
hgb_clf = HistGradientBoostingClassifier(
    max_iter=300, learning_rate=0.05, max_leaf_nodes=31,
    min_samples_leaf=20, l2_regularization=1.5, early_stopping=True, random_state=42
)

# 4. Stacking Ensemble com predições out-of-fold via StratifiedKFold
stacking_clf = StackingClassifier(
    estimators=[("enet", pipe_enet), ("rf", rf_clf), ("hgb", hgb_clf)],
    final_estimator=LogisticRegression(C=1.0),
    cv=StratifiedKFold(n_splits=5, shuffle=True, random_state=42),
    stack_method="predict_proba",
    n_jobs=-1,
).fit(X_train, y_train)

for nome, mod in [("RandomForest", rf_clf), ("StackingEnsemble", stacking_clf)]:
    probs = mod.predict_proba(X_test)[:, 1]
    print(f"{nome:18s} -> Test ROC AUC: {roc_auc_score(y_test, probs):.4f} | Log-Loss: {log_loss(y_test, probs):.4f}")

print(f"RandomForest OOB Score: {rf_clf.oob_score_:.4f}")
perm = permutation_importance(stacking_clf, X_test, y_test, scoring="roc_auc", n_repeats=10, random_state=42, n_jobs=-1)
print("Top 3 variáveis por Permutation Importance:", np.argsort(perm.importances_mean)[::-1][:3].tolist())
```

---

## 3. Critério de Decisão

A escolha da arquitetura deve evoluir do estimador linear interpretável para *ensembles* apenas quando o ganho fora da amostra justificar a complexidade adicional:

| Família de Algoritmos | Quando Utilizar (Cenário Ideal) | Hiperparâmetros Críticos de Controle |
| :--- | :--- | :--- |
| **Modelos Lineares Regularizados (Ridge, Lasso, Elastic Net, Logística)** | Relações lineares, alta dimensionalidade esparsa ($p \gg m$), exigência de interpretabilidade de coeficientes $\theta_j$, extrapolação monotônica ou *baseline*. | Penalização ($\alpha$ ou $C = 1/\alpha$) e razão $\ell_1/\ell_2$ (`l1_ratio` $r$). Exige escalonamento prévio obrigatório. |
| **Random Forests e Extra-Trees (Bagging)** | Dados tabulares não lineares e ruidosos onde se busca robustez imediata contra *overfitting* e paralelização simples. | `n_estimators`, `max_features` ($\sqrt{p}$), `max_depth` e `min_samples_leaf`. |
| **Gradient Boosting (XGBoost, LightGBM, `HistGradientBoosting`)** | Dados tabulares heterogêneos ($m > 10^4$ com `HistGradientBoosting`) onde a prioridade é maximizar acurácia preditiva capturando interações complexas. | Par `learning_rate` ($\eta$) e `max_iter` (com *early stopping*), `subsample`, `max_leaf_nodes` e regularizações `alpha` ($\ell_1$) / `lambda` ($\ell_2$). |
| **Stacking / Blending** | Refinamento combinando modelos de naturezas distintas (linear + floresta + *boosting*) cujos erros são pouco correlacionados. | Diversidade entre estimadores base e regularização do `final_estimator` ajustado sobre predições *out-of-fold*. |

---

## 4. Erros Comuns

- **Treinar modelos penalizados (Ridge, Lasso, Elastic Net, SVM) ou KNN sem padronizar as variáveis**: Como as penalidades $\ell_1$ e $\ell_2$ incidem sobre a magnitude numérica dos coeficientes $\theta_j$, variáveis em escalas menores recebem coeficientes maiores e são penalizadas de forma arbitrária sem `StandardScaler`.
- **Usar árvores ou *ensembles* de árvores (Random Forest / Gradient Boosting) para extrapolar fora do domínio histórico**: Árvores retornam nas folhas a média local das amostras de treino; para qualquer entrada acima do máximo ou abaixo do mínimo visto no treino, predizem uma constante e são incapazes de extrapolar tendências.
- **Aumentar `n_estimators` em *Gradient Boosting* sem *early stopping* nem regularização**: Diferente de *Random Forests*, adicionar árvores sequenciais no *Gradient Boosting* continua reduzindo o erro de treino até memorizar o ruído se não houver controle conjunto de `learning_rate` e parada antecipada.
- **Ajustar o meta-modelo de um *Stacking* sobre predições de treino direto (*in-fold*)**: Treinar o *blender* diretamente sobre `base_model.predict_proba(X_train)` atribui peso máximo ao modelo mais sobreajustado; as entradas do meta-estimador devem ser geradas via `cross_val_predict` (*out-of-fold*).
