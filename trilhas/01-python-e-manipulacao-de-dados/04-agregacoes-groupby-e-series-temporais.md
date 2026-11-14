# Aula 04 — Agregações, Operações de Grupo (`GroupBy`) e Séries Temporais

> **Fonte(s) desta aula:**
> - Livro: *Python for Data Analysis* (3ª Edição, Wes McKinney) — Capítulo 10 (*Data Aggregation and Group Operations*, pp. 319–356) e Capítulo 11 (*Time Series*, pp. 357–404).

---

## 1. Problema e Definição

Após a limpeza e junção das tabelas, a extração de indicadores analíticos e a construção de variáveis preditivas (*features*) exigem responder a duas classes de perguntas: como resumir métricas por categorias de negócio (ou normalizar valores dentro de cada categoria) e como agregar eventos ao longo do tempo respeitando fusos horários, periodicidades irregulares e janelas móveis sem misturar dados futuros com dados passados.

No pandas, essas operações fundamentam-se em dois subsistemas:

1. **Arquitetura `split-apply-combine` (`GroupBy`):**
   Toda operação `df.groupby(chaves)` divide logicamente o objeto em grupos a partir de uma ou mais chaves (`split`), aplica uma função sobre cada partição (`apply`) e combina os resultados em uma nova estrutura (`combine`). Existem três verbos distintos para a etapa de aplicação, cada um com contrato de dimensionalidade específico:
   - **Agregação (`.agg`):** Reduz cada grupo de $N_g$ linhas para **uma única linha** resumida por grupo. Suporta funções nativas otimizadas em C (`"sum"`, `"mean"`, `"median"`, `"std"`, `"count"`, `"nunique"`, `"min"`, `"max"`) e a sintaxe de agregação nomeada (`pd.NamedAgg`), que permite aplicar múltiplas funções a diferentes colunas atribuindo nomes claros às colunas de saída.
   - **Transformação Intragrupo (`.transform`):** Aplica uma função ao grupo e **retorna uma `Series` ou `DataFrame` com exatamente o mesmo tamanho e índice da tabela original**, propagando (*broadcasting*) o resultado do grupo para cada linha individual. É a ferramenta correta para calcular a participação percentual de uma linha no total do seu grupo, padronizar variáveis por grupo ($z$-score intragrupo) ou imputar valores ausentes pela média/mediana do grupo.
   - **Aplicação Geral (`.apply`):** Recebe um sub-`DataFrame` por grupo e permite retornar objetos de tamanho arbitrário (como os $k$ maiores registros de cada grupo). Por executar uma função Python para cada grupo, possui maior custo computacional e deve ser reservada para lógicas que `.agg` e `.transform` não expressam diretamente.

2. **Séries Temporais (`DatetimeIndex`, `resample` e `rolling`):**
   - **Tipos Temporais e Fusos Horários:** O tipo `pd.Timestamp` (e índices `DatetimeIndex`) representa instantes no tempo com precisão de nanossegundos. Dados de produção devem ser localizados (`tz_localize`) ou convertidos (`tz_convert`) para UTC a fim de evitar ambiguidades em transições de horário de verão.
   - **Deslocamento (`shift` e `pct_change`):** Move valores para frente ou para trás no tempo para calcular defasagens (*lags*) e variações percentuais entre períodos consecutivos.
   - **Reamostragem (`resample`):** É um `groupby` baseado no tempo que converte uma série temporal de uma frequência para outra — seja reduzindo a frequência (*downsampling*, ex.: transações em minutos para fechamento diário `"1D"` ou mensal `"MS"`) com uma função de agregação, seja aumentando a frequência (*upsampling*, ex.: diário para horário) com preenchimento controlado (`ffill`).
   - **Janelas Móveis e Expansivas (`rolling` e `expanding`):** Calculam estatísticas sobre uma janela deslizante de tamanho fixo (em número de observações, como `rolling(7)`, ou em intervalo temporal, como `rolling("7D")`) ou acumulada desde o início da série (`expanding()`).

---

## 2. Aplicação Prática

O código a seguir demonstra o uso combinado de agregações nomeadas (`.agg`), cálculo de métricas intragrupo (`.transform`), reamostragem temporal diária (`resample`) e médias móveis de 3 dias (`rolling`) por unidade operacional:

```python
import numpy as np
import pandas as pd


def analisar_operacao_temporal() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    # 1. Série de eventos transacionais com timestamps em UTC
    dados = pd.DataFrame(
        {
            "timestamp": pd.to_datetime(
                [
                    "2026-03-01 09:15:00",
                    "2026-03-01 16:40:00",
                    "2026-03-02 11:00:00",
                    "2026-03-03 14:20:00",
                    "2026-03-04 10:05:00",
                    "2026-03-01 10:30:00",
                    "2026-03-02 15:10:00",
                    "2026-03-04 18:00:00",
                ],
                utc=True,
            ),
            "regional": ["SUL", "SUL", "SUL", "SUL", "SUL", "SUDESTE", "SUDESTE", "SUDESTE"],
            "vendedor_id": ["V1", "V2", "V1", "V2", "V1", "V3", "V3", "V4"],
            "valor_venda": [1200.0, 800.0, 1500.0, np.nan, 2500.0, 3000.0, 2200.0, 4800.0],
        }
    )

    # 2. Uso de .transform() para imputar NaN com a mediana da própria regional
    # e calcular o peso percentual de cada venda dentro da sua regional sem perder linhas
    mediana_por_regional = dados.groupby("regional")["valor_venda"].transform("median")
    dados["valor_venda"] = dados["valor_venda"].fillna(mediana_por_regional)

    soma_por_regional = dados.groupby("regional")["valor_venda"].transform("sum")
    dados["share_na_regional"] = (dados["valor_venda"] / soma_por_regional).round(4)

    # 3. Agregação nomeada (.agg) com múltiplas métricas em uma única passagem
    resumo_regional = (
        dados.groupby("regional", as_index=False, dropna=False)
        .agg(
            total_transacoes=("valor_venda", "count"),
            vendedores_ativos=("vendedor_id", "nunique"),
            receita_total=("valor_venda", "sum"),
            ticket_medio=("valor_venda", "mean"),
            desvio_padrao=("valor_venda", "std"),
        )
        .round(2)
    )

    # 4. Reamostragem diária (downsampling) e janela móvel de 3 dias para a regional SUL
    sul_diario = (
        dados.loc[dados["regional"] == "SUL"]
        .set_index("timestamp")
        .resample("1D")["valor_venda"]
        .sum()
        .to_frame(name="receita_diaria")
    )
    sul_diario["receita_lag_1d"] = sul_diario["receita_diaria"].shift(1)
    sul_diario["media_movel_3d"] = (
        sul_diario["receita_diaria"].rolling(window=3, min_periods=1).mean().round(2)
    )

    return dados, resumo_regional, sul_diario


if __name__ == "__main__":
    df_enriquecido, df_resumo, df_serie_sul = analisar_operacao_temporal()
    print("--- Dados Enriquecidos Intragrupo (.transform) ---")
    print(df_enriquecido[["timestamp", "regional", "valor_venda", "share_na_regional"]])
    print("\n--- Resumo Executivo por Regional (.agg) ---")
    print(df_resumo)
    print("\n--- Série Diária e Média Móvel 3D (Regional SUL) ---")
    print(df_serie_sul)
```

---

## 3. Critério de Decisão

| Necessidade Analítica | Método Recomendado | Método a Evitar e Justificativa Técnica |
| :--- | :--- | :--- |
| Gerar tabela de resumo com 1 linha por grupo e múltiplas métricas | `df.groupby(chaves, as_index=False).agg(nome_col=("col", "func"))` | Calcular cada métrica separadamente (`g["a"].sum()`, `g["b"].mean()`) e fazer vários `pd.merge` posteriores. |
| Adicionar estatística do grupo (média, soma, desvio) como nova coluna na tabela original | `df.groupby(chaves)["col"].transform("mean")` | Fazer `df.groupby(chaves)["col"].mean()` seguido de `pd.merge` de volta na tabela original (mais lento e consome o dobro de memória). |
| Selecionar os $N$ maiores ou menores registros dentro de cada grupo | `df.sort_values("metrica", ascending=False).groupby("grupo").head(N)` | `df.groupby("grupo").apply(lambda g: g.nlargest(N, "metrica"))`, que invoca uma função Python por grupo e reconstrói índices hierárquicos. |
| Converter eventos irregulares em série periódica contínua (diária, semanal, mensal) | `df.set_index("data").resample("1D").agg(...)` | Agrupar por string formatada (`df["data"].dt.strftime("%Y-%m-%d")`), pois omite dias sem movimento (`0` vendas), quebrando o cálculo de médias móveis e lags. |
| Calcular média móvel sobre série temporal que possui lacunas de datas | `df.set_index("data").rolling("7D")["valor"].mean()` (janela baseada em offset de tempo) | `df["valor"].rolling(7).mean()` (janela baseada em contagem de linhas), que misturará períodos distantes caso faltem dias no registro. |

---

## 4. Erros Comuns

1. **Omissão Silenciosa de Grupos com Chave Nula (`dropna=True` por Padrão):**
   - **Falha:** Executar `df.groupby("categoria")["receita"].sum()` quando parte das vendas está com `categoria` nula (`NaN` ou `<NA>`). Por padrão, `groupby` define `dropna=True`, excluindo todas as linhas sem categoria da soma final e gerando divergência contábil em relação a `df["receita"].sum()`.
   - **Correção:** Em relatórios financeiros e auditorias de dados, passe explicitamente `df.groupby("categoria", dropna=False)` ou preencha valores ausentes na chave antes de agrupar.

2. **Passar Funções Python (`lambda`) onde Existem Nomes de Funções Cythonizadas:**
   - **Falha:** Escrever `df.groupby("id")["valor"].agg(lambda x: x.sum())` ou `transform(lambda x: x.mean())`. Ao receber uma `lambda`, o pandas sai do caminho otimizado em C e instancia objetos `Series` em Python para cada um dos milhares de grupos, tornando a execução até 50 vezes mais lenta.
   - **Correção:** Passar sempre o nome da operação como string (`"sum"`, `"mean"`, `"median"`, `"std"`, `"first"`, `"last"`, `"count"`, `"nunique"`).

3. **Vazamento de Dados do Futuro (*Look-Ahead Bias*) em Séries Temporais:**
   - **Falha:** Calcular médias móveis com `rolling(7, center=True)` ou preencher dados faltantes com `bfill()` (*backward fill*) antes de alimentar um modelo preditivo ou regra de decisão operacional. Ambas as operações utilizam informações de instantes futuros ($t+1, t+2, \dots$) para calcular o valor no instante $t$.
   - **Correção:** Garantir que o `DatetimeIndex` esteja ordenado em ordem estritamente crescente (`sort_index()`), utilizar apenas janelas alinhadas à direita (`center=False`, padrão) e propagar informações exclusivamente do passado para o presente (`ffill()`).

4. **Uso de `pct_change()` ou `shift(1)` em Tabela Agrupada sem Isolar a Entidade:**
   - **Falha:** Ordenar um `DataFrame` por `["produto_id", "data"]` e aplicar `df["preco"].shift(1)` diretamente na coluna inteira. A primeira data do produto `B` herdará como `lag` o preço da última data do produto `A`.
   - **Correção:** Executar o deslocamento sempre escopado pelo grupo da entidade: `df.groupby("produto_id")["preco"].shift(1)`.
