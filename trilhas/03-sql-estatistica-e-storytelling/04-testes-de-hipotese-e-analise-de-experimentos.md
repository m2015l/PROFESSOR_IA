# 04. Testes de Hipótese e Análise de Experimentos

> **Fonte(s) desta aula:**
> - **Bruce, Peter; Bruce, Andrew.** *Practical Statistics for Data Scientists: 50 Essential Concepts* (1ª Edição, O'Reilly Media, 2017) — **Cap. 3** (*Statistical Experiments and Significance Testing*, pp. 85–131).
> - **Tanimura, Cathy.** *SQL for Data Analysis: Advanced Techniques for Transforming Data into Insights* (1ª Edição, O'Reilly Media, 2021) — **Cap. 7** (*Experiment Analysis*, pp. 267–286).

---

## 1. Problema e Definição

Quando uma equipe altera um fluxo de produto, algoritmo de recomendação ou política comercial, observar uma diferença bruta nas métricas entre o grupo exposto e o não exposto não basta para comprovar causalidade: a diferença pode decorrer da variabilidade aleatória entre amostras. O **experimento controlado randomizado (Teste A/B)** isola o efeito causal da intervenção dividindo aleatoriamente unidades elegíveis (usuários, sessões, pedidos) entre o grupo de **Controle ($A$)** e um ou mais grupos de **Tratamento ($B$)**.

A estrutura formal de decisão estatística compreende:
1. **Hipótese Nula ($H_0$) e Hipótese Alternativa ($H_1$):** $H_0$ postula que não há diferença real entre os parâmetros populacionais dos grupos ($\mu_B - \mu_A = 0$ ou $p_B - p_A = 0$) e que qualquer variação observada resulta do acaso. $H_1$ postula a existência de efeito real (podendo ser *unilateral*, quando se testa apenas uma direção, ou *bilateral / two-tailed*, que protege contra desvios em ambas as direções e constitui o padrão conservador em experimentos de negócio).
2. **Métrica de Sucesso Primária e *Guardrail Metrics*:** A métrica primária reflete o objetivo direto da hipótese (ex.: taxa de conversão ou receita média por usuário), enquanto as *guardrail metrics* monitoram efeitos colaterais indesejados (ex.: latência de página, taxa de cancelamento ou reclamações de suporte).
3. **Valor-$p$ (*p-value*) e Princípios da ASA (*American Statistical Association*):** Dado um modelo estatístico sob $H_0$, o *p-value* é a probabilidade de obter um resultado igual ou mais extremo do que a estatística observada nos dados. Conforme as diretrizes da ASA: o *p-value* **não** é a probabilidade de $H_0$ ser verdadeira, **não** mede a probabilidade de os dados terem sido produzidos apenas pelo acaso, e **não** mede a magnitude nem a relevância prática/econômica de um efeito.
4. **Erros de Decisão, Poder Estatístico e Tamanho Amostral:**
   - **Erro Tipo I (Falso Positivo, taxa $\alpha$):** Rejeitar $H_0$ quando $H_0$ é verdadeira (tipicamente fixa-se o nível de significância em $\alpha = 0{,}05$ ou $0{,}01$).
   - **Erro Tipo II (Falso Negativo, taxa $\beta$):** Não rejeitar $H_0$ quando $H_1$ é verdadeira (um efeito real existe, mas o experimento falha em detectá-lo).
   - **Poder Estatístico ($1 - \beta$):** Probabilidade de detectar um efeito real de magnitude mínima especificada (**MDE — *Minimum Detectable Effect***), convencionalmente fixado em $80\%$ ou $90\%$.
   - Quatro grandezas são interdependentes: tamanho da amostra ($n$), magnitude do efeito (MDE), variância da métrica ($\sigma^2$), nível de significância ($\alpha$) e poder ($1 - \beta$). Para uma métrica contínua em dois grupos de mesmo tamanho $n$ (teste bilateral), a aproximação analítica para o tamanho amostral por variante é:

$$n \approx \frac{2\sigma^2 (z_{1 - \alpha/2} + z_{1 - \beta})^2}{\text{MDE}^2}$$

onde $z_{1 - \alpha/2}$ e $z_{1 - \beta}$ são os quantis da distribuição Normal padrão (para $\alpha = 0{,}05$ e poder de $80\%$, $(1{,}96 + 0{,}84)^2 \approx 7{,}85$).

---

## 2. Aplicação Prática

### 2.1. Extração SQL da Coorte Experimental com Janela Temporal Fixa

Na camada de banco de dados, todas as unidades alocadas no experimento (`exp_assignment`) devem ser mantidas no denominador via `LEFT JOIN` com a tabela de eventos, convertendo ausências de compra em zero (`COALESCE(..., 0)`) e restringindo os eventos a uma janela temporal fixa (*time box*, ex.: 7 dias após a entrada no experimento):

```sql
WITH metricas_por_usuario AS (
    SELECT
        a.user_id,
        a.variant,
        MAX(CASE WHEN o.order_id IS NOT NULL THEN 1 ELSE 0 END) AS converteu_7d,
        COALESCE(SUM(o.amount), 0.0) AS gasto_7d
    FROM exp_assignment a
    LEFT JOIN orders o
        ON a.user_id = o.user_id
       AND o.order_ts >= a.assigned_ts
       AND o.order_ts < a.assigned_ts + INTERVAL '7 days'
    WHERE a.exp_name = 'checkout_simplificado_v2'
      AND a.assigned_ts BETWEEN '2025-03-01' AND '2025-03-14'
    GROUP BY a.user_id, a.variant
)
SELECT
    variant,
    COUNT(*) AS total_usuarios,
    SUM(converteu_7d) AS total_conversoes,
    ROUND(AVG(converteu_7d::NUMERIC), 4) AS taxa_conversao,
    ROUND(AVG(gasto_7d), 2) AS media_gasto,
    ROUND(STDDEV_SAMP(gasto_7d), 2) AS dp_gasto
FROM metricas_por_usuario
GROUP BY variant;
```

### 2.2. Dimensionamento Amostral, Teste de Permutação, Welch e Qui-Quadrado em Python

```python
import numpy as np
from scipy import stats
from statsmodels.stats.power import NormalIndPower
from statsmodels.stats.proportion import proportion_effectsize
from statsmodels.stats.multitest import multipletests

# 1. Dimensionamento de amostra a priori (Conversão base = 10%, MDE absoluto = +1.5 p.p.)
h_effect = proportion_effectsize(0.115, 0.100)
analise_poder = NormalIndPower()
n_por_grupo = np.ceil(
    analise_poder.solve_power(effect_size=h_effect, alpha=0.05, power=0.80, ratio=1.0, alternative="two-sided")
)
print(f"Tamanho amostral mínimo por variante: {int(n_por_grupo):,} usuários")

# 2. Teste Qui-Quadrado de Independência para conversão binária (Tabela de Contingência 2x2)
# Formato: [[convertidos_A, nao_convertidos_A], [convertidos_B, nao_convertidos_B]]
tabela_contingencia = np.array([[880, 7920], [1025, 7775]])
chi2_stat, p_val_chi2, dof, _ = stats.chi2_contingency(tabela_contingencia, correction=False)
print(f"Qui-Quadrado: stat={chi2_stat:.4f}, p-value={p_val_chi2:.5f}")

# 3. Teste t de Welch e Teste de Permutação Exata/Monte Carlo para métrica contínua (Receita)
rng = np.random.default_rng(42)
gasto_controle = np.concatenate([np.zeros(7920), rng.gamma(shape=2.0, scale=45.0, size=880)])
gasto_tratamento = np.concatenate([np.zeros(7775), rng.gamma(shape=2.1, scale=46.5, size=1025)])

t_stat, p_val_welch = stats.ttest_ind(gasto_tratamento, gasto_controle, equal_var=False)
res_perm = stats.permutation_test(
    (gasto_tratamento, gasto_controle),
    statistic=lambda x, y, axis: np.mean(x, axis=axis) - np.mean(y, axis=axis),
    permutation_type="independent",
    n_resamples=5000,
     vectorized=True,
    random_state=42
)
print(f"Diferença de médias: R$ {gasto_tratamento.mean() - gasto_controle.mean():.2f}")
print(f"Welch p-value: {p_val_welch:.5f} | Permutação p-value: {res_perm.pvalue:.5f}")

# 4. Correção para múltiplos testes (Bonferroni e Benjamini-Hochberg / FDR)
p_valores_multiplos = [p_val_chi2, p_val_welch, 0.038, 0.210]
_, p_corr_bonf, _, _ = multipletests(p_valores_multiplos, alpha=0.05, method="bonferroni")
_, p_corr_fdr, _, _ = multipletests(p_valores_multiplos, alpha=0.05, method="fdr_bh")
print(f"P-valores corrigidos (FDR): {np.round(p_corr_fdr, 5)}")
```

---

## 3. Critério de Decisão

| Cenário Experimental | Método Recomendado | Critério Técnico |
| :--- | :--- | :--- |
| **Métrica binária (conversão, clique) com contagens esperadas $\ge 5$ em todas as células** | Teste Qui-Quadrado de Independência ou Teste $z$ de duas proporções | Para contagens muito pequenas (células esperadas $< 5$), substitua pelo **Teste Exato de Fisher** (`scipy.stats.fisher_exact`). |
| **Métrica contínua entre 2 grupos com variâncias distintas ou assimetria** | Teste $t$ de Welch (`equal_var=False`) ou Teste de Permutação (Reamostragem sem reposição) | O teste de permutação embaralha os rótulos de grupo sem assumir normalidade; em amostras muito grandes, o teste $t$ de Welch converge assintoticamente pelo TCL. |
| **Comparação simultânea de $K \ge 3$ variantes ou múltiplos cortes de segmentação** | ANOVA (*F-statistic*) ou testes par-a-par com correção de **Bonferroni** ($\alpha / m$) ou **FDR** (Benjamini-Hochberg) | Realizar $m$ testes independentes a $\alpha = 0{,}05$ eleva a probabilidade de ao menos um falso positivo para $1 - (1 - 0{,}05)^m$. |
| **Otimização contínua de recompensa durante o experimento vs. Inferência causal estática** | Algoritmos **Multi-Arm Bandit** ($\epsilon$-*greedy*, *Thompson Sampling*) vs. Teste A/B clássico de horizonte fixo | *Bandits* realocam tráfego dinamicamente para as variantes de melhor desempenho, reduzindo o custo de oportunidade, mas dificultam inferências não enviesadas sobre subpopulações. |
| **Impossibilidade de randomização individual (mudança regulatória ou lançamento global)** | **Quase-experimentos**: *Difference-in-Differences*, Pareamento ou *Regression Discontinuity Design* (RDD) em torno de um limiar contínuo | Simples comparações *pré/pós* confundem o efeito da mudança com sazonalidade e choques macroeconômicos externos. |

---

## 4. Erros Comuns

- **Interrupção precoce por monitoramento contínuo (*Peeking* / *Data Snooping*):** Inspecionar o *p-value* diariamente e encerrar o experimento assim que $p < 0{,}05$ infla drasticamente a taxa real de Erro Tipo I. O experimento deve rodar até atingir o tamanho amostral $n$ e o ciclo temporal (ex.: múltiplos inteiros de 7 dias) definidos a priori, ou utilizar testes sequenciais formais (*Always Valid p-values*).
- **Omissão dos usuários não convertidos no denominador SQL (`INNER JOIN` em vez de `LEFT JOIN`):** Unir a tabela de alocação de variantes com a tabela de pedidos usando `INNER JOIN` calcula apenas o ticket médio dos compradores (`AVG(amount)` entre quem comprou), descartando o efeito da variante sobre a decisão de comprar ou não.
- **Sensibilidade extrema a *outliers* em métricas contínuas de receita:** Um único pedido corporativo atípico em uma variante pode inverter a média amostral e invalidar o teste $t$. Quando a distribuição possuir cauda pesada, aplique *winsorizing* (truncamento nos percentis 99 ou 99,9 definido antes do experimento) ou avalie métricas quantílicas via permutação.
- **Efeito Novidade (*Novelty Effect*) e Primazia:** Usuários recorrentes podem interagir mais com um novo componente visual apenas pela mudança repentina de interface, com o ganho desaparecendo após algumas semanas. Deve-se segmentar a análise entre novos usuários e usuários antigos e acompanhar coortes de *holdout* de longo prazo.
