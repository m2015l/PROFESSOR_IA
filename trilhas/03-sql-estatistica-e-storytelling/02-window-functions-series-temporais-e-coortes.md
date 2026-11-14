# 02. Window Functions, Séries Temporais e Coortes

> **Fonte(s) desta aula:**
> - **Tanimura, Cathy.** *SQL for Data Analysis: Advanced Techniques for Transforming Data into Insights* (1ª Edição, O'Reilly Media, 2021) — **Cap. 2** (*Preparing Data for Analysis*, pp. 33–35), **Cap. 3** (*Time Series Analysis*, pp. 61–119) e **Cap. 4** (*Cohort Analysis*, pp. 121–174).

---

## 1. Problema e Definição

Agregações clássicas com `GROUP BY` colapsam as linhas originais da tabela em uma única linha por grupo, impedindo o cálculo direto de métricas que exigem simultaneamente o valor granular do registro e o contexto agregado ou sequencial de sua partição. Exemplos incluem calcular a participação percentual de uma filial na receita mensal total, a variação percentual em relação ao mês anterior (*Month-over-Month*), médias móveis de 7 dias ou a taxa de retenção de clientes ao longo do tempo após a primeira compra.

As **Funções de Janela (*Window Functions*)** resolvem esse problema avaliando uma função de agregação, ordenação ou deslocamento sobre um conjunto deslizante de linhas relacionadas ao registro atual, sem reduzir a cardinalidade da consulta. A sintaxe formal segue a estrutura:

$$\text{funcao\_janela}() \ \text{OVER} \ (\text{PARTITION BY } c_1, c_2 \ \text{ORDER BY } c_3 \ \text{frame\_clause})$$

1. **`PARTITION BY`:** Divide o conjunto de dados em partições independentes (análogas a grupos, porém mantendo todas as linhas). Se omitida, a tabela inteira constitui uma única partição.
2. **`ORDER BY`:** Define a ordenação lógica das linhas dentro de cada partição. É obrigatória para funções de ranking (`ROW_NUMBER`, `RANK`, `DENSE_RANK`, `NTILE`), deslocamento (`LAG`, `LEAD`, `FIRST_VALUE`, `LAST_VALUE`) e acumulados móveis.
3. **`frame_clause` (`ROWS | RANGE | GROUPS BETWEEN inicio AND fim`):** Delimita exatamente quais linhas dentro da partição entram no cálculo para a linha corrente (ex.: `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` para os últimos 7 registros físicos, ou `ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW` para somas acumuladas desde o início da partição).

A aplicação conjunta de funções de janela e aritmética temporal sustenta duas metodologias analíticas centrais:
- **Análise de Séries Temporais:** Padronização de fusos horários (`AT TIME ZONE`), truncamento em unidades de calendário (`DATE_TRUNC('month', ts)`), extração de componentes cíclicos (`DATE_PART` / `EXTRACT`), indexação a um período-base (`FIRST_VALUE`), janelas móveis para suavização de ruído sazonal (como ciclos semanais de 7 dias) e comparações período sobre período (*MoM*, *YoY*) com `LAG`.
- **Análise de Coortes (*Cohort Analysis*):** Agrupamento de entidades (usuários, clientes, contratos) pela data de ocorrência de um evento fundador (tipicamente a primeira compra ou ativação, obtida via `MIN(data_evento)`) e acompanhamento longitudinal de seu comportamento ao longo de períodos relativos de tempo ($t_0, t_1, t_2, \dots$). As quatro métricas principais de coorte são:
  1. **Retenção (*Retention*):** Proporção da coorte inicial que permanece ativa em cada período $t_k$ subsequente.
  2. **Sobrevivência (*Survivorship*):** Proporção da coorte cujo tempo total de permanência (*tenure* entre a primeira e a última atividade conhecida) é igual ou superior a $k$ períodos, independentemente de ter ocorrido atividade intermediária em todos os períodos.
  3. **Recorrência (*Returnship* / *Repeat Purchase*):** Proporção da coorte que executa uma ação repetida (ex.: segunda ou terceira compra) dentro de uma janela temporal fixa (*time box*, como 30 ou 90 dias após a aquisição), garantindo comparabilidade justa entre coortes antigas e recentes.
  4. **Cálculo Cumulativo (*Cumulative LTV*):** Soma acumulada de receita ou eventos gerados por membro da coorte inicial até o período $t_k$.

---

## 2. Aplicação Prática

### 2.1. Séries Temporais Contínuas, Média Móvel e Comparação YoY

Registros transacionais são frequentemente esparsos: se nenhuma venda ocorrer em uma data específica, essa linha não existirá na tabela de fatos, e uma janela física `ROWS BETWEEN 6 PRECEDING AND CURRENT ROW` abrangerá mais de 7 dias corridos do calendário. A solução rigorosa exige gerar uma dimensão de datas contínua (`GENERATE_SERIES` ou tabela `date_dim`) e realizar um `LEFT JOIN` antes de calcular as funções de janela:

```sql
WITH calendario_mensal AS (
    SELECT GENERATE_SERIES(
        '2024-01-01'::DATE,
        '2025-12-01'::DATE,
        INTERVAL '1 month'
    )::DATE AS mes_ref
),
receita_mensal AS (
    SELECT
        c.mes_ref,
        COALESCE(SUM(v.valor_liquido), 0.0) AS receita
    FROM calendario_mensal c
    LEFT JOIN vendas v
        ON DATE_TRUNC('month', v.data_venda AT TIME ZONE 'UTC')::DATE = c.mes_ref
    GROUP BY c.mes_ref
)
SELECT
    mes_ref,
    receita,
    -- Acumulado no ano (Year-to-Date / YTD) reiniciando a cada ano civil
    SUM(receita) OVER (
        PARTITION BY DATE_PART('year', mes_ref)
        ORDER BY mes_ref
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    ) AS receita_ytd,
    -- Média móvel trimestral (mês atual e 2 meses imediatamente anteriores)
    ROUND(AVG(receita) OVER (
        ORDER BY mes_ref
        ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
    ), 2) AS media_movel_3m,
    -- Indexação ao período-base (Janeiro de 2024 = 100)
    ROUND(100.0 * receita / NULLIF(FIRST_VALUE(receita) OVER (ORDER BY mes_ref), 0), 2) AS indice_base_100,
    -- Variação percentual Year-over-Year (YoY) comparando com 12 meses atrás
    ROUND(100.0 * (receita - LAG(receita, 12) OVER (ORDER BY mes_ref))
        / NULLIF(LAG(receita, 12) OVER (ORDER BY mes_ref), 0), 2) AS var_pct_yoy
FROM receita_mensal
ORDER BY mes_ref;
```

### 2.2. Matriz de Retenção e LTV Cumulativo por Coorte

Na consulta a seguir, identifica-se o mês de aquisição de cada cliente (`coorte_mes`), calcula-se o índice de meses decorridos (`periodo_mes`) para cada transação subsequente e normaliza-se o volume de clientes ativos e a receita acumulada pelo tamanho original da coorte no período zero (`FIRST_VALUE`):

```sql
WITH primeira_compra AS (
    SELECT
        customer_id,
        DATE_TRUNC('month', MIN(data_venda))::DATE AS coorte_mes,
        SUM(valor_liquido) AS receita_total_vida
    FROM vendas
    GROUP BY customer_id
),
atividade_coorte AS (
    SELECT
        p.coorte_mes,
        (DATE_PART('year', AGE(DATE_TRUNC('month', v.data_venda)::DATE, p.coorte_mes)) * 12
         + DATE_PART('month', AGE(DATE_TRUNC('month', v.data_venda)::DATE, p.coorte_mes)))::INT AS periodo_mes,
        COUNT(DISTINCT v.customer_id) AS clientes_ativos,
        SUM(v.valor_liquido) AS receita_periodo
    FROM vendas v
    INNER JOIN primeira_compra p
        ON v.customer_id = p.customer_id
    GROUP BY p.coorte_mes, 2
)
SELECT
    coorte_mes,
    periodo_mes,
    FIRST_VALUE(clientes_ativos) OVER (
        PARTITION BY coorte_mes ORDER BY periodo_mes
    ) AS tamanho_coorte_inicial,
    clientes_ativos,
    ROUND(
        100.0 * clientes_ativos::NUMERIC / FIRST_VALUE(clientes_ativos) OVER (
            PARTITION BY coorte_mes ORDER BY periodo_mes
        ), 2
    ) AS taxa_retencao_pct,
    ROUND(
        SUM(receita_periodo) OVER (
            PARTITION BY coorte_mes
            ORDER BY periodo_mes
            ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
        ) / FIRST_VALUE(clientes_ativos) OVER (
            PARTITION BY coorte_mes ORDER BY periodo_mes
        ), 2
    ) AS ltv_acumulado_por_cliente
FROM atividade_coorte
ORDER BY coorte_mes, periodo_mes;
```

---

## 3. Critério de Decisão

| Problema Analítico | Escolha de Implementação SQL | Justificativa Técnica |
| :--- | :--- | :--- |
| **Deduplicação mantendo o registro mais recente vs. Ranking de competição** | `ROW_NUMBER()` vs. `RANK()` / `DENSE_RANK()` | `ROW_NUMBER()` atribui inteiros estritamente únicos ($1, 2, 3$), ideal para selecionar exatamente 1 linha por chave (`WHERE rn = 1`). `RANK()` atribui o mesmo valor a empates e pula posições ($1, 1, 3$), enquanto `DENSE_RANK()` não pula posições ($1, 1, 2$). |
| **Definição de quadro de janela (`ROWS` vs. `RANGE`)** | `ROWS BETWEEN ...` por padrão em séries temporais regularizadas | `ROWS` conta linhas físicas de forma determinística e eficiente; `RANGE` agrupa linhas com valores idênticos na coluna do `ORDER BY`, o que pode incluir múltiplas linhas inesperadas se houver chaves temporais repetidas. |
| **Métrica de retenção para assinaturas (contratos com `start_date` e `end_date`)** | *Join* de intervalo (`d.data BETWEEN s.start_date AND COALESCE(s.end_date, CURRENT_DATE)`) com dimensão de calendário | Em produtos de assinatura, não há log diário de compra; cruzar os intervalos de vigência com uma tabela de datas converte contratos estáticos em uma série temporal ativa mensal ou diária exata. |
| **Comparação de conversão ou recompra entre coortes de idades diferentes** | Recorrência em janela fixa (*time box*, ex.: `v.data_venda <= p.primeira_data + INTERVAL '30 days'`) | Evita que coortes mais antigas aparentem desempenho superior apenas por terem tido mais tempo de calendário para acumular eventos. |

---

## 4. Erros Comuns

- **Omissão de quadro explícito ao usar `LAST_VALUE()` ou funções de janela com `ORDER BY`:** No padrão SQL, quando `ORDER BY` está presente em `OVER (...)` sem cláusula de quadro explícita, o quadro padrão é `RANGE BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW`. Assim, `LAST_VALUE(col) OVER (PARTITION BY x ORDER BY y)` retorna o valor da própria linha corrente em vez do último valor da partição. Para obter o último valor real, declare `ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING` (ou inverta a ordenação com `FIRST_VALUE`).
- **Cálculo de médias móveis e `LAG` sobre séries temporais esparsas (*sparse data*):** Aplicar `LAG(receita, 1)` ou `AVG(receita) OVER (ORDER BY data ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)` sobre uma tabela onde dias sem vendas estão ausentes desloca a janela para datas arbitrárias no passado, invalidando a média móvel e a variação *MoM*/*YoY*.
- **Viés de sobrevivência (*Survivorship Bias*) em análises de corte transversal:** Calcular o ticket médio ou o engajamento de todos os clientes ativos no mês corrente sem estratificar pela idade de coorte mistura clientes recém-adquiridos com clientes retidos há anos, ocultando deteriorações nas safras recentes.
- **Média de porcentagens em vez de razão das somas:** Calcular a retenção média global via `AVG(taxa_retencao_pct)` atribui peso idêntico a coortes de 10 e de 10.000 clientes. Agregações globais devem ponderar pelo tamanho inicial (`SUM(clientes_ativos) / SUM(tamanho_coorte_inicial)`).
