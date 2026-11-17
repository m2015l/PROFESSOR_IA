# Aula 03 — Ingestão, Limpeza e Transformação Tabular em pandas

> **Fonte(s) desta aula:**
> - Livro: *Python for Data Analysis* (3ª Edição, Wes McKinney) — Capítulo 6 (*Data Loading, Storage, and File Formats*, pp. 175–202), Capítulo 7 (*Data Cleaning and Preparation*, pp. 203–246) e Capítulo 8 (*Data Wrangling: Join, Combine, and Reshape*, pp. 247–280).

---

## 1. Problema e Definição

Em projetos reais de engenharia e análise de dados, os arquivos brutos recebidos de sistemas transacionais, planilhas operacionais ou extrações externas raramente estão prontos para agregação ou modelagem. Os problemas mais recorrentes incluem inferência incorreta de tipos na leitura de arquivos texto (como códigos postais ou CPFs perdendo zeros à esquerda), valores ausentes representados por marcadores heterogêneos (`""`, `"N/A"`, `"null"`, `-999`), registros duplicados, strings despadronizadas e informações fragmentadas em múltiplas tabelas com diferentes granularidades.

O pipeline de preparação tabular no pandas divide-se em três etapas determinísticas:

1. **Ingestão e Formatos de Armazenamento:**
   - **Formatos baseados em texto (`read_csv`, `read_json`):** Não armazenam metadados de esquema nativamente. Por isso, a leitura em produção exige a especificação explícita de tipos (`dtype`), colunas de data (`parse_dates`), marcadores de nulidade (`na_values`), codificação (`encoding="utf-8"`) e, para arquivos maiores que a memória disponível, leitura iterativa em lotes (`chunksize`).
   - **Formatos binários colunares (`read_parquet`, `to_parquet` via PyArrow):** Armazenam o esquema de tipos junto aos dados, aplicam compressão eficiente por coluna (como Snappy ou Zstandard) e permitem leitura seletiva de colunas (*column pruning*) e predicados (*predicate pushdown*), reduzindo drasticamente o tempo de I/O e o uso de RAM em comparação ao CSV.

2. **Saneamento, Tipos Estendidos e Manipulação de Strings:**
   - **Valores Ausentes (`isna`, `dropna`, `fillna`):** O pandas unifica a detecção de nulidade (`np.nan`, `None` e `pd.NA`). A introdução dos *Nullable Extension Types* (`Int64`, `boolean`, `string`) evita que uma coluna de inteiros seja forçada para `float64` apenas por conter um único valor ausente.
   - **Deduplicação e Padronização (`drop_duplicates`, `.str`, `Categorical`):** A remoção de duplicatas deve especificar o subconjunto de chaves de negócio (`subset`) e a política de retenção (`keep="first"` ou `"last"` após ordenação temporal). Operações textuais em colunas inteiras devem utilizar o acessor vetorizado `.str` (que ignora valores `NA` com segurança), e colunas de baixa cardinalidade (como UF, status ou categoria) devem ser convertidas para o tipo `category` para reduzir o consumo de memória e acelerar agrupamentos.

3. **Junção Relacional e Reestruturação (`merge`, `concat`, `pivot`, `melt`):**
   - **`pd.merge`:** Executa junções relacionais em memória (`inner`, `left`, `right`, `outer`) sobre uma ou mais chaves. O parâmetro `validate` (`"one_to_one"`, `"many_to_one"`, `"one_to_many"`) atua como trava de segurança contra multiplicação acidental de linhas quando a tabela dimensão possui chaves duplicadas.
   - **`pd.concat`:** Empilha múltiplos `DataFrames` ao longo de um eixo (`axis=0` para união vertical de lotes; `axis=1` para alinhamento horizontal por índice).
   - **`pivot` e `melt`:** Convertem tabelas entre o formato longo (*tidy/long*, ideal para armazenamento e agrupamento programmatico) e o formato largo (*wide*, utilizado em matrizes de visualização ou séries alinhadas por coluna).

---

### Fundamentos e Exemplos Progressivos Passo a Passo (Partindo do Zero)

Veja isoladamente como funciona cada operação de leitura, limpeza e combinação tabular antes de reuni-las no pipeline completo:

1. **Leitura controlada com `pd.read_csv`:**
   Por padrão, `read_csv` tenta adivinhar o tipo de cada coluna e pode remover zeros à esquerda de CPFs ou CEPs (`"0123"` vira número `123`). Passar `dtype={"coluna": "string"}` preserva o texto original; `na_values=[...]` converte textos como `"N/D"` em nulos reais; e `parse_dates=[...]` transforma textos de data em objetos temporais.

   ```python
   import io
   import pandas as pd

   csv_exemplo = "cpf,qtd,data\n01234567890,10,2026-10-01\n98765432100,N/D,2026-10-02"
   df_lido = pd.read_csv(
       io.StringIO(csv_exemplo),
       dtype={"cpf": "string"},
       na_values=["N/D"],
       parse_dates=["data"],
   )
   print(df_lido["cpf"].iloc[0])   # Saída: 01234567890 (zero inicial preservado!)
   print(df_lido["qtd"].isna().tolist())  # Saída: [False, True]
   ```

2. **Nulos (`isna`, `fillna`), duplicatas (`drop_duplicates`) e limpeza de texto (`.str`):**
   - `df["col"].isna()` devolve `True` onde o valor está faltando; `fillna(valor)` preenche esses nulos.
   - `df["col"].str.strip().str.upper()` remove espaços nas pontas e converte textos para maiúsculas com segurança, mesmo quando há valores nulos na coluna.
   - `drop_duplicates(subset=["id"], keep="last")` remove linhas com `"id"` repetido mantendo apenas a última ocorrência (útil após ordenar por data).

   ```python
   df_sujo = pd.DataFrame({
       "id": ["C1", "C1", "C2"],
       "uf": [" sp ", "SP", None],
       "valor": [100.0, 150.0, None],
   })
   df_sujo["uf"] = df_sujo["uf"].str.strip().str.upper()  # ' sp ' -> 'SP', None continua <NA>
   df_sujo["valor"] = df_sujo["valor"].fillna(0.0)        # Preenche None com 0.0
   df_limpo = df_sujo.drop_duplicates(subset=["id"], keep="last")
   print(df_limpo)  # Mantém a linha 1 (C1, valor 150.0) e a linha 2 (C2, valor 0.0)
   ```

3. **Junção relacional (`pd.merge`) e remodelagem (`pd.melt` / `pd.concat`):**
   - `pd.merge(tabela_a, tabela_b, on="chave", how="left", validate="many_to_one")` cruza duas tabelas pela coluna em comum `"chave"`. Usar `how="left"` garante que nenhuma linha da tabela da esquerda desapareça se não houver correspondência na direita; usar `validate="many_to_one"` lança erro imediatamente se a tabela da direita tiver chaves repetidas (evitando duplicação silenciosa).
   - `pd.melt(df, id_vars=[...], value_vars=[...], var_name=..., value_name=...)` transforma várias colunas em pares de linhas (formato longo).

   ```python
   pedidos = pd.DataFrame({"pedido": [1, 2], "cli_id": ["C1", "C3"]})
   clientes = pd.DataFrame({"cli_id": ["C1", "C2"], "nome": ["Ana", "Bruno"]})

   # how="left" mantém o pedido 2 (C3) mesmo sem cadastro em clientes (nome = NaN)
   cruzado = pd.merge(pedidos, clientes, on="cli_id", how="left", validate="many_to_one")
   print(cruzado)

   # Formato largo -> formato longo com melt
   largo = pd.DataFrame({"cli_id": ["C1"], "jan": [100], "fev": [200]})
   longo = pd.melt(largo, id_vars=["cli_id"], value_vars=["jan", "fev"],
                   var_name="mes", value_name="receita")
   print(longo)  # Gera 2 linhas: (C1, jan, 100) e (C1, fev, 200)
   ```

---

## 2. Aplicação Prática

O script abaixo implementa um pipeline de ingestão controlada, saneamento de tipos e strings, deduplicação por carimbo de tempo, validação de cardinalidade no `merge` e remodelagem com `melt`:

```python
import io
import pandas as pd


def executar_pipeline_limpeza() -> tuple[pd.DataFrame, pd.DataFrame]:
    # Simulação de CSV bruto com zeros à esquerda, marcadores de nulo variados e duplicatas
    csv_clientes = """cliente_id,documento_cpf,uf,data_atualizacao,limite_credito
C001,01234567890, sp ,2026-10-01 10:00:00,15000.50
C001,01234567890,SP,2026-10-05 14:30:00,18000.00
C002,09876543211,rj,2026-10-02 09:15:00,N/D
C003,11122233344,MG,2026-10-03 11:20:00,9500.00
"""
    # 1. Ingestão determinística preservando zeros à esquerda em documento_cpf
    df_clientes = pd.read_csv(
        io.StringIO(csv_clientes),
        dtype={"cliente_id": "string", "documento_cpf": "string", "uf": "string"},
        na_values=["N/D", "null", "-", ""],
        parse_dates=["data_atualizacao"],
    )

    # 2. Padronização textual vetorizada com .str e conversão para Categorical
    df_clientes["uf"] = df_clientes["uf"].str.strip().str.upper().astype("category")

    # 3. Deduplicação mantendo apenas o registro mais recente de cada cliente_id
    df_clientes = (
        df_clientes.sort_values("data_atualizacao", ascending=True)
        .drop_duplicates(subset=["cliente_id"], keep="last")
        .reset_index(drop=True)
    )

    # 4. Tratamento explícito de valores ausentes
    mediana_limite = df_clientes["limite_credito"].median()
    df_clientes["limite_credito"] = df_clientes["limite_credito"].fillna(mediana_limite)

    # Tabela de faturamento em formato largo (wide)
    df_faturamento_wide = pd.DataFrame(
        {
            "cliente_id": pd.Series(["C001", "C002", "C003"], dtype="string"),
            "receita_2025": pd.Series([42000.0, 19500.0, 8300.0], dtype="float64"),
            "receita_2026": pd.Series([51000.0, 24000.0, 11200.0], dtype="float64"),
        }
    )

    # 5. Reestruturação de wide para long (tidy data) usando pd.melt
    df_faturamento_long = pd.melt(
        df_faturamento_wide,
        id_vars=["cliente_id"],
        value_vars=["receita_2025", "receita_2026"],
        var_name="ano_ref",
        value_name="receita",
    )
    df_faturamento_long["ano"] = (
        df_faturamento_long["ano_ref"].str.replace("receita_", "", regex=False).astype("Int64")
    )
    df_faturamento_long = df_faturamento_long.drop(columns=["ano_ref"])

    # 6. Junção relacional validando cardinalidade many_to_one (muitos anos -> 1 cliente único)
    df_consolidado = pd.merge(
        df_faturamento_long,
        df_clientes[["cliente_id", "documento_cpf", "uf", "limite_credito"]],
        on="cliente_id",
        how="left",
        validate="many_to_one",
    )

    return df_clientes, df_consolidado


if __name__ == "__main__":
    clientes, consolidado = executar_pipeline_limpeza()
    print("--- Clientes Saneados ---")
    print(clientes)
    print("\n--- Faturamento Consolidado (Formato Longo) ---")
    print(consolidado)
```

---

## 3. Critério de Decisão

| Problema de Engenharia / Análise | Decisão Técnica Recomendada | Alternativa Inadequada e Consequência |
| :--- | :--- | :--- |
| Persistência de tabelas intermediárias entre etapas de um pipeline Python | `df.to_parquet("dados.parquet", index=False)` | `df.to_csv("dados.csv")` — perde os tipos (`datetime`, `Int64`, `category`), ocupa 3x a 10x mais disco e exige re-inferência lenta na leitura. |
| Colunas de identificadores numéricos (CEP, CNPJ, CPF, SKU, telefone) | Declarar `dtype={"cpf": "string"}` na chamada de `read_csv` | Converter para string apenas após a leitura (`df["cpf"].astype(str)`), quando os zeros à esquerda já foram truncados irreversivelmente pelo parser numérico. |
| Enriquecimento de tabela fato com tabela dimensão (ex.: vendas + cadastro de clientes) | `pd.merge(..., how="left", on="id", validate="many_to_one")` | `pd.merge` sem `validate` e com `how="inner"` por padrão — descarta silenciosamente vendas sem cadastro e duplica receitas caso a dimensão tenha chaves repetidas. |
| Presença de valores nulos em colunas de inteiros ou booleanos | Utilizar tipos anuláveis do pandas (`"Int64"`, `"boolean"`) | Utilizar tipos padrão do NumPy (`int64`, `bool`), que falham ao encontrar `NaN` ou convertem toda a coluna para `float64` / `object`. |
| União de dezenas de arquivos mensais com mesmo esquema | Acumular `DataFrames` em uma `list` e chamar `pd.concat(lista_dfs, ignore_index=True)` uma única vez | Chamar `pd.concat` dentro de um laço `for` a cada arquivo lido, realocando toda a memória acumulada a cada iteração (complexidade quadrática). |

---

## 4. Erros Comuns

1. **Explosão Cartesiana Acidental em `pd.merge` por Chaves Duplicadas:**
   - **Falha:** Realizar `pd.merge(df_pedidos, df_lojas, on="loja_id", how="left")` sem verificar se `loja_id` é único em `df_lojas`. Se uma loja aparecer duas vezes na tabela de cadastro, todos os pedidos daquela loja serão duplicados no resultado final, inflando somas financeiras e contagens sem gerar erro de execução.
   - **Correção:** Deduplicar explicitamente a tabela dimensão antes do join ou exigir `validate="many_to_one"` (ou `"one_to_one"`) na chamada de `pd.merge`, o que lança `MergeError` imediatamente caso a unicidade seja violada.

2. **Descarte Involuntário de Registros pelo `how="inner"` Padrão do `pd.merge`:**
   - **Falha:** Omitir o argumento `how` ao cruzar uma tabela principal de eventos com uma tabela auxiliar de atributos (`pd.merge(eventos, atributos, on="user_id")`). Como o padrão de `pd.merge` é `how="inner"`, qualquer evento cujo `user_id` não conste na tabela auxiliar é eliminado silenciosamente da análise.
   - **Correção:** Sempre declarar explicitamente o tipo de junção (`how="left"`, `how="inner"`, `how="outer"`) e, em auditorias de cobertura, utilizar o parâmetro `indicator=True` para inspecionar a coluna `_merge` (`left_only`, `both`, `right_only`).

3. **Falha com `NaN` em Expressões Regulares e Métodos de String:**
   - **Falha:** Aplicar funções de string via `df["texto"].apply(lambda x: x.lower())` em uma coluna que contém valores nulos. Quando o método encontra `NaN` (que é do tipo `float`) ou `None`, o código falha com `AttributeError`.
   - **Correção:** Utilizar exclusivamente os métodos vetorizados de `df["texto"].str` (ex.: `df["texto"].str.lower()`, `df["texto"].str.contains("padrao", na=False)`), que tratam valores ausentes automaticamente.

4. **Imputação Global de Dados Ausentes sem Considerar o Contexto da Variável:**
   - **Falha:** Executar `df.fillna(0)` indiscriminadamente em todo o `DataFrame`. Em variáveis contínuas como temperatura, preço ou tempo de resposta, substituir `NaN` por `0` distorce severamente a média, o desvio-padrão e os coeficientes de modelos estatísticos.
   - **Correção:** Avaliar o mecanismo de ausência por coluna: manter `NA` quando o algoritmo a jusante suportar nulos, criar uma variável indicadora booleana de ausência (`df["col_ausente"] = df["col"].isna()`) ou imputar estatísticas segmentadas por grupo (como a mediana por categoria).
