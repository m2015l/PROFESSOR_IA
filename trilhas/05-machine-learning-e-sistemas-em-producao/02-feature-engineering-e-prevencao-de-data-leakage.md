# 02 — Feature Engineering e Prevenção de Data Leakage

**Fonte(s) desta aula:**
- HUYEN, Chip. *Designing Machine Learning Systems: An Iterative Process for Production-Ready Applications*. 1ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulo 5 (*Feature Engineering*, pp. 139–161).
- GÉRON, Aurélien. *Hands-On Machine Learning with Scikit-Learn, Keras, and TensorFlow*. 3ª Edição. Sebastopol: O'Reilly Media, 2022. Capítulo 2 (*End-to-End Machine Learning Project*, pp. 39–102) e Capítulo 8 (*Dimensionality Reduction*, pp. 237–258).
- BRUCE, Peter; BRUCE, Andrew. *Practical Statistics for Data Scientists: 50 Essential Concepts*. 1ª Edição. Sebastopol: O'Reilly Media, 2017. Capítulo 4 (*Regression and Prediction*, pp. 133–180) e Capítulo 6 (*Statistical Machine Learning*, pp. 223–258).

---

## 1. Problema e Definição

Embora redes neurais profundas extraiam representações de texto e imagem, a maioria dos sistemas corporativos em produção processa dados tabulares e transacionais heterogêneos, nos quais a qualidade das variáveis engenheiradas (*engineered features*) determina a capacidade preditiva e a estabilidade operacional. O processo de **Feature Engineering** converte registros brutos em vetores numéricos informativos, tratando valores ausentes, escalas discrepantes, assimetrias, categorias de alta cardinalidade e interações não lineares, garantindo ausência absoluta de vazamento de dados (*data leakage*).

O primeiro problema estrutural em bases reais é a presença de **valores ausentes**, divididos em três mecanismos estatísticos:
1. **MCAR (*Missing Completely at Random*)**: A probabilidade de ausência é uniforme e independente de qualquer variável observada ou oculta. Embora excluir linhas (*row deletion*) não introduza viés sob MCAR, reduz a amostra e é inviável em inferência *online* (onde o serviço não pode recusar predições).
2. **MAR (*Missing at Random*)**: A ausência depende exclusivamente de outras variáveis observadas (ex.: omissão de renda correlacionada com faixa etária declarada).
3. **MNAR (*Missing Not at Random*)**: O próprio valor não observado causa a ausência (ex.: contribuintes de alta renda omitindo intencionalmente o salário). Sob MAR e MNAR, a ausência carrega sinal preditivo: excluir linhas ou colunas enviesa o modelo, e imputar apenas por média ou mediana (`SimpleImputer`) oculta que o dado estava ausente, exigindo a criação de um **indicador binário de ausência** (`add_indicator=True`).

Para variáveis numéricas contínuas, modelos baseados em gradiente (Regressão Linear/Logística, Redes Neurais), distância geométrica (KNN, *K-Means*) e projeção de variância (PCA, SVM) são sensíveis à escala dos atributos. O **escalonamento Min-Max** reescala o atributo para $[a, b]$ (como $[0, 1]$ ou $[-1, 1]$) segundo $\tilde{x} = a + \frac{(x - \min(x))(b - a)}{\max(x) - \min(x)}$, sendo vulnerável a *outliers* que comprimem as observações normais. A **padronização (*Standardization / z-score*)** calcula $\hat{x} = \frac{x - \mu}{\sigma}$ com média zero e variância unitária, sendo mais robusta a extremos. Em distribuições assimétricas de cauda longa (*skewed*), aplica-se **transformação logarítmica** ($\log(1+x)$) antes da padronização. A **discretização** (*quantization / binning*) agrupa variáveis contínuas em quantis ou faixas para capturar respostas não monotônicas em modelos lineares; alternativamente, o **KNN pode atuar como gerador de features locais** (*KNN as a feature engine*), estimando a média do alvo nos $k$ vizinhos mais próximos (ex.: preço de imóveis adjacentes) como variável de entrada para o preditor principal.

A **codificação de variáveis categóricas** em produção enfrenta multicolinearidade e mutabilidade de categorias (*alta cardinalidade*). Na regressão linear com intercepto $\beta_0$, converter $P$ categorias em $P$ colunas binárias via *One-Hot Encoding* cria colinearidade exata ($\sum_{j=1}^P d_j = 1$), exigindo representação com $P-1$ colunas (`drop='first'`). Em sistemas onde novas categorias surgem continuamente (IDs de lojas, marcas, domínios), vocabulários estáticos falham ou saturam a categoria `<UNKNOWN>`. A solução escalável é o **Feature Hashing (*hashing trick*)**, que aplica uma função de *hash* determinística para projetar a string diretamente em um espaço fixo de $m$ índices ($2^{12}$ a $2^{20}$ *buckets*), sem dicionário em memória e com impacto mínimo de colisões. O **cruzamento de atributos (*Feature Crossing*)** combina duas ou mais variáveis (`PolynomialFeatures` ou interações $X_1 \cdot X_2$) para capturar relações não lineares.

Acima de qualquer transformação, a maior ameaça em produção é o **Data Leakage**: contaminação dos atributos de treino ou validação por informações do alvo ou do futuro, indisponíveis no instante real da inferência. Suas cinco causas principais são:
1. **Particionamento aleatório de dados temporais**: dividir séries temporais aleatoriamente em vez de por corte temporal (`TimeSeriesSplit`), vazando tendências futuras para o passado.
2. **Escalonamento, imputação ou seleção de variáveis antes do *split***: ajustar `StandardScaler`, `SimpleImputer` ou `PCA` na base inteira antes de separar treino e validação, vazando estatísticas globais.
3. **Duplicatas entre treino e teste**: falhar em desduplicar registros antes do particionamento ou aplicar *oversampling* antes da divisão.
4. **Vazamento de grupo (*Group Leakage*)**: alocar observações da mesma entidade física (exames do mesmo paciente ou transações do mesmo cliente) em treino e validação simultaneamente sem `GroupKFold`.
5. **Vazamento do processo de geração de dados**: incluir metadados gerados após o evento alvo (ex.: código de setor de cobrança preenchido apenas após confirmação de atraso).

---

## 2. Aplicação Prática

O código a seguir implementa um pipeline determinístico no `scikit-learn` (`Pipeline`, `ColumnTransformer`, `FunctionTransformer` e `FeatureHasher`) com imputação e indicador de ausência, transformação logarítmica, padronização *z-score*, *feature crossing* e *Feature Hashing* para alta cardinalidade, validado por `GroupKFold` contra *data leakage*.

```python
import numpy as np
import pandas as pd
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.compose import ColumnTransformer
from sklearn.feature_extraction import FeatureHasher
from sklearn.impute import SimpleImputer
from sklearn.linear_model import RidgeClassifier
from sklearn.model_selection import GroupKFold, cross_val_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import FunctionTransformer, OneHotEncoder, PolynomialFeatures, StandardScaler

class HighCardinalityHasher(BaseEstimator, TransformerMixin):
    def __init__(self, n_features: int = 32):
        self.n_features = n_features

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        col = pd.Series(X.iloc[:, 0] if isinstance(X, pd.DataFrame) else X[:, 0]).fillna("MISSING").astype(str)
        tokens = [[val] for val in col]
        return FeatureHasher(n_features=self.n_features, input_type="string").transform(tokens).toarray()

# 1. Dados transacionais com ausência MNAR, assimetria e múltiplas compras por cliente_id
rng = np.random.default_rng(42)
n = 1500
df = pd.DataFrame({
    "cliente_id": rng.integers(100, 350, size=n),
    "valor_pedido": rng.lognormal(mean=4.0, sigma=1.2, size=n),
    "renda_declarada": rng.normal(loc=5500.0, scale=1800.0, size=n),
    "canal": rng.choice(["organico", "busca_paga", "afiliado", "direto"], size=n),
    "merchant_id": [f"m_{i}" for i in rng.integers(1, 800, size=n)],
})
df.loc[(df["renda_declarada"] > 7000.0) & (rng.random(n) < 0.65), "renda_declarada"] = np.nan

y = ((np.log1p(df["valor_pedido"]) > 4.8) & (df["renda_declarada"].isna() | (df["renda_declarada"] < 4200.0))).astype(int).to_numpy()
X = df.drop(columns=["cliente_id"])
grupos = df["cliente_id"].to_numpy()

# 2. Sub-pipelines especializados por tipo estatístico de coluna
pipe_skew = Pipeline([
    ("imp", SimpleImputer(strategy="median", add_indicator=True)),
    ("log", FunctionTransformer(np.log1p, validate=True)),
    ("scaler", StandardScaler()),
])
pipe_cross = Pipeline([
    ("imp", SimpleImputer(strategy="median", add_indicator=True)),
    ("cross", PolynomialFeatures(degree=2, interaction_only=True, include_bias=False)),
    ("scaler", StandardScaler()),
])
pipe_cat_low = Pipeline([
    ("imp", SimpleImputer(strategy="most_frequent")),
    ("ohe", OneHotEncoder(drop="first", handle_unknown="ignore", sparse_output=False)),
])

preprocessador = ColumnTransformer([
    ("skew", pipe_skew, ["valor_pedido"]),
    ("cross", pipe_cross, ["valor_pedido", "renda_declarada"]),
    ("cat_low", pipe_cat_low, ["canal"]),
    ("cat_high", HighCardinalityHasher(n_features=32), ["merchant_id"]),
])

pipeline_ml = Pipeline([
    ("prep", preprocessador),
    ("clf", RidgeClassifier(alpha=1.0, class_weight="balanced")),
])

# 3. Validação GroupKFold: nenhum cliente aparece simultaneamente em treino e validação
scores = cross_val_score(pipeline_ml, X, y, groups=grupos, cv=GroupKFold(n_splits=5), scoring="roc_auc")
print(f"ROC AUC médio (GroupKFold sem data leakage): {scores.mean():.4f} +/- {scores.std():.4f}")
```

---

## 3. Critério de Decisão

Para selecionar transformações e arquiteturas de *features* em produção, avalie **importância preditiva** (ganho por permutação ou valores SHAP) e **cobertura/generalização** (fração das instâncias reais em que a variável está presente e sua estabilidade temporal):

| Desafio de Engenharia de Features | Condição Técnica / Restrição | Transformação e Arquitetura Recomendada |
| :--- | :--- | :--- |
| **Valores Ausentes Não Aleatórios (MAR / MNAR)** | A probabilidade de omissão depende de outras variáveis ou do próprio valor omitido; inferência *online* proibida de recusar requisições. | Imputar com mediana ajustada **apenas no treino** combinada com **indicador binário de ausência** (`add_indicator=True`). Nunca descartar linhas em inferência. |
| **Escalonamento Numérico** | Distribuição simétrica vs. distribuição com cauda longa positiva (*right-skewed*) e *outliers*. | Usar `StandardScaler` (*z-score*) como padrão; aplicar `np.log1p` antes da padronização em caudas longas. Evitar `MinMaxScaler` na presença de *outliers*. |
| **Variáveis Categóricas em Produção** | Baixa cardinalidade e vocabulário fixo vs. alta cardinalidade ($> 10^2$ níveis) ou surgimento contínuo de novos IDs. | Usar `OneHotEncoder(drop='first')` em modelos lineares para vocabulário fixo; usar **Feature Hashing** (`FeatureHasher`) para alta cardinalidade ou vocabulário dinâmico. |
| **Prevenção de Data Leakage** | Dados temporais e/ou múltiplas observações por entidade física (cliente, paciente, dispositivo). | Particionar por janela temporal (`TimeSeriesSplit`) e isolar entidades via `GroupKFold`; encapsular todos os transformadores em um `Pipeline` ajustado exclusivamente no treino. |

---

## 4. Erros Comuns

- **Executar `fit_transform()` de escalonadores, imputadores ou PCA na base completa antes do `train_test_split`**: Calcular média, desvio-padrão ou mediana usando amostras do conjunto de validação/teste vaza informação futura e invalida a métrica *offline*.
- **Imputar valores ausentes MNAR pela média sem preservar a flag de ausência**: Quando a omissão é causada pelo estado do indivíduo ou falha específica, substituir o `NaN` sem indicador binário apaga um sinal preditivo crítico e distorce a variância.
- **Incluir *features* de baixíssima cobertura ou geradas pós-evento**: Variáveis presentes em menos de 1% das linhas ou preenchidas por sistemas *downstream* após a confirmação do rótulo geram sobreajuste severo em validação e falha imediata em produção.
- **Aplicar *One-Hot Encoding* completo ($P$ colunas) em modelos lineares não regularizados ou em alta cardinalidade**: Em modelos lineares com intercepto, $P$ colunas geram colinearidade perfeita; em alta cardinalidade em produção, o *One-Hot Encoding* falha diante de categorias inéditas ou esgota a memória do serviço.
