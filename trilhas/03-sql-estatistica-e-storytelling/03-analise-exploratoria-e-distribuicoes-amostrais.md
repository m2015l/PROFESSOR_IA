# 03. Análise Exploratória e Distribuições Amostrais

> **Fonte(s) desta aula:**
> - **Bruce, Peter; Bruce, Andrew.** *Practical Statistics for Data Scientists: 50 Essential Concepts* (1ª Edição, O'Reilly Media, 2017) — **Cap. 1** (*Exploratory Data Analysis*, pp. 1–46) e **Cap. 2** (*Data and Sampling Distributions*, pp. 47–84).

---

## 1. Problema e Definição

Antes de submeter dados tabulares (*rectangular data*, onde linhas representam registros/observações e colunas representam variáveis/*features*) a testes inferenciais ou algoritmos preditivos, é necessário caracterizar sua tipologia, tendência central, dispersão, assimetria e estrutura de correlação, além de quantificar a incerteza amostral associada às estimativas.

### 1.1. Taxonomia de Dados e Estimadores de Localização e Variabilidade

Os dados estruturados classificam-se em **numéricos** — subdivididos em *contínuos* (assumem qualquer valor real em um intervalo, como receita ou tempo de resposta) e *discretos* (contagens inteiras, como número de chamados) — e **categóricos** — subdivididos em *nominais* (categorias sem ordenação intrínseca), *binários* (caso especial dicotômico, $0/1$) e *ordinais* (categorias com hierarquia explícita, como escalas de avaliação de 1 a 5).

Para resumir variáveis numéricas, empregam-se estimadores de localização (posição central) e de variabilidade (dispersão):
- **Média aritmética ($\bar{x} = \frac{1}{n}\sum_{i=1}^n x_i$):** Soma dos valores dividida pelo tamanho amostral $n$. É altamente sensível a valores extremos (*outliers*).
- **Média aparada (*Trimmed Mean*):** Calculada após descartar um número fixo $p$ (ou percentual) dos menores e dos maiores valores ordenados: $\bar{x}_{\text{trim}} = \frac{1}{n - 2p}\sum_{i=p+1}^{n-p} x_{(i)}$. Elimina a influência de valores extremos mantendo informações do corpo principal da distribuição.
- **Mediana e Mediana Ponderada:** Valor central da amostra ordenada (percentil 50). Na versão ponderada, é o valor $x_{(k)}$ tal que a soma dos pesos inferiores e superiores equivale a $50\%$ do peso total. São estimadores robustos a *outliers* e assimetria severa.
- **Variância ($s^2$) e Desvio-Padrão ($s$):** Baseiam-se na soma dos quadrados dos desvios em relação à média, divididos por $n - 1$ graus de liberdade para obter uma estimativa não enviesada da variância populacional:

$$s = \sqrt{\frac{1}{n - 1}\sum_{i=1}^{n}(x_i - \bar{x})^2}$$

Como os desvios são elevados ao quadrado, $s^2$ e $s$ não são robustos a *outliers*.
- **Amplitude Interquartil ($\text{IQR} = P_{75} - P_{25}$) e Desvio Absoluto Mediano ($\text{MAD}$):** Estimadores robustos de dispersão. O $\text{MAD}$ é definido por:

$$\text{MAD} = \text{mediana}(|x_1 - m|, |x_2 - m|, \dots, |x_n - m|)$$

onde $m$ é a mediana amostral (para estimar o desvio-padrão equivalente sob distribuição normal, multiplica-se o $\text{MAD}$ por $1{,}4826$).
- **Correlação de Pearson ($r$):** Mede a associação linear entre duas variáveis contínuas $X$ e $Y$ no intervalo $[-1, 1]$:

$$r = \frac{\sum_{i=1}^n (x_i - \bar{x})(y_i - \bar{y})}{(n - 1) s_x s_y}$$

### 1.2. Distribuição Amostral, Teorema Central do Limite e Bootstrap

Na inferência estatística, distingue-se a **distribuição dos dados** (a distribuição empírica das observações individuais $x_i$ na amostra) da **distribuição amostral de uma estatística** (a distribuição que $\bar{x}$, a mediana ou outra métrica apresenta quando calculada sobre múltiplas amostras de tamanho $n$ extraídas da mesma população).

Pelo **Teorema Central do Limite (TCL)**, a distribuição amostral da média $\bar{x}$ aproxima-se de uma distribuição Normal à medida que o tamanho amostral $n$ cresce, mesmo que a população original não seja normal (desde que não apresente variância infinita ou assimetria extrema com $n$ pequeno). A variabilidade dessa distribuição amostral é medida pelo **Erro Padrão (*Standard Error*, $SE$)**:

$$SE = \frac{s}{\sqrt{n}}$$

Para estimar o erro padrão e construir intervalos de confiança de qualquer estatística (como a mediana ou a média aparada) sem depender de premissas de normalidade ou fórmulas analíticas fechadas, utiliza-se o **Bootstrap**: sorteiam-se $R$ reamostras de tamanho $n$ **com reposição** a partir da própria amostra observada, calcula-se a estatística de interesse em cada reamostra $r \in \{1, \dots, R\}$ e obtém-se a distribuição amostral empírica. O intervalo de confiança de nível $(1 - \alpha)$ pelo método percentílico corresponde diretamente aos percentis $\frac{\alpha}{2}$ e $1 - \frac{\alpha}{2}$ das $R$ estimativas.

---

## 2. Aplicação Prática

O script Python abaixo implementa a comparação entre estimadores paramétricos e robustos em dados financeiros assimétricos (com cauda longa à direita) e executa o *Bootstrap* não paramétrico para estimar o erro padrão e o intervalo de confiança de 95% da mediana e da média aparada:

```python
import numpy as np
import pandas as pd
from scipy import stats

rng = np.random.default_rng(seed=42)

# Simulação de receitas de contratos B2B (distribuição log-normal assimétrica + outliers)
receitas = np.concatenate([
    rng.lognormal(mean=8.5, sigma=0.8, size=495),
    np.array([180_000.0, 240_000.0, 310_000.0, 450_000.0, 620_000.0])
])
serie = pd.Series(receitas, name="receita_brl")

# 1. Estimadores de localização: Média vs. Média Aparada (10%) vs. Mediana
media = serie.mean()
media_aparada_10 = stats.trim_mean(serie, proportiontocut=0.10)
mediana = serie.median()

# 2. Estimadores de variabilidade: Desvio-padrão vs. IQR vs. MAD
desvio_padrao = serie.std(ddof=1)
q25, q75 = np.percentile(serie, [25, 75])
iqr = q75 - q25
mad = stats.median_abs_deviation(serie, scale=1.0)
mad_normalizado = stats.median_abs_deviation(serie, scale="normal")

print(f"Localização -> Média: {media:,.2f} | Aparada(10%): {media_aparada_10:,.2f} | Mediana: {mediana:,.2f}")
print(f"Dispersão   -> DP: {desvio_padrao:,.2f} | IQR: {iqr:,.2f} | MAD: {mad:,.2f} (Norm: {mad_normalizado:,.2f})")

# 3. Bootstrap não paramétrico (R = 10.000 reamostras com reposição)
n = len(serie)
R = 10_000
indices_boot = rng.integers(0, n, size=(R, n))
amostras_boot = serie.to_numpy()[indices_boot]

medianas_boot = np.median(amostras_boot, axis=1)
erropadrao_mediana = medianas_boot.std(ddof=1)
ic95_mediana = np.percentile(medianas_boot, [2.5, 97.5])

print(f"Mediana Bootstrap -> SE: {erropadrao_mediana:,.2f} | IC 95%: [{ic95_mediana[0]:,.2f}, {ic95_mediana[1]:,.2f}]")
```

---

## 3. Critério de Decisão

| Situação Analítica | Escolha Metodológica | Justificativa Estatística |
| :--- | :--- | :--- |
| **Resumo de variáveis com assimetria forte ou *outliers* (renda, LTV, latência de rede)** | Mediana ou Média Aparada (10%) acompanhada de $\text{IQR}$ ou $\text{MAD}$ | A média aritmética e o desvio-padrão são dominados pela cauda extrema e não representam o comportamento típico da distribuição. |
| **Visualização bivariada de grandes volumes numéricos ($N > 10.000$)** | *Hexagonal binning* (`plt.hexbin`), gráficos de contorno ou *alpha transparency* em vez de *scatterplot* simples | Em *scatterplots* densos, a sobreposição de pontos (*overplotting*) forma uma massa opaca que oculta a densidade real da distribuição conjunta. |
| **Amostragem de subgrupos minoritários relevantes** | Amostragem Estratificada (*Stratified Sampling*) em vez de amostragem aleatória simples | Garante representatividade suficiente e variância controlada em estratos de baixa frequência populacional. |
| **Modelagem de distribuições paramétricas de eventos** | **Binomial** (sucessos em $n$ tentativas), **Poisson** (contagem de eventos por unidade de tempo/espaço com taxa $\lambda$), **Exponencial** (tempo entre eventos a taxa constante $\lambda$) e **Weibull** (tempo até falha com taxa variável). | Selecionar a família paramétrica compatível com o processo gerador dos dados evita erros graves na simulação de capacidade, filas e confiabilidade. |

---

## 4. Erros Comuns

- **Confundir Desvio-Padrão ($s$) com Erro Padrão ($SE$):** O desvio-padrão mede a dispersão das observações individuais em torno da média populacional e não diminui quando aumentamos o tamanho da amostra $n$; o erro padrão ($SE = s/\sqrt{n}$) mede a precisão da média amostral e converge para zero à medida que $n \to \infty$.
- **Assumir que o *Bootstrap* corrige tamanho amostral insuficiente ou viés de seleção:** O *Bootstrap* reamostra exclusivamente a amostra observada; ele não cria dados novos nem corrige amostras não representativas (*selection bias*, *self-selection bias*). Se a amostra for muito pequena ou enviesada, o intervalo de confiança *Bootstrap* reproduzirá esse viés.
- **Interpretar um intervalo de confiança de 95% como a probabilidade de o parâmetro populacional variar:** O parâmetro populacional verdadeiro é fixo; a cobertura de 95% é uma propriedade do procedimento de construção do intervalo sobre repetidas amostras hipotéticas.
- **Ignorar a Regressão à Média (*Regression to the Mean*):** Selecionar unidades no extremo superior ou inferior de desempenho em um período $t_0$ (onde atuaram tanto capacidade real quanto ruído aleatório extremo) e atribuir seu retorno natural a valores próximos da média em $t_1$ a uma intervenção operacional aplicada entre os períodos.
- **Assumir normalidade em dados de cauda longa (*Long-Tailed Distributions*):** Retornos financeiros, volumes de vendas por SKU e tempos de sessão violam sistematicamente a distribuição Normal nos extremos; essa aderência deve ser auditada via **QQ-Plot** (*Quantile-Quantile Plot*) antes de aplicar regras baseadas em *z-scores*.
