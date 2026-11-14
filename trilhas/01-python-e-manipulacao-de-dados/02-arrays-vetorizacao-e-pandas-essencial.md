# Aula 02 — Arrays, Vetorização em NumPy e Estruturas Essenciais do pandas

> **Fonte(s) desta aula:**
> - Livro: *Python for Data Analysis* (3ª Edição, Wes McKinney) — Capítulo 4 (*NumPy Basics: Arrays and Vectorized Computation*, pp. 83–122) e Capítulo 5 (*Getting Started with pandas*, pp. 123–174).

---

## 1. Problema e Definição

Em listas nativas do Python, cada elemento é um ponteiro para um objeto independente alocado separadamente na memória, exigindo verificação dinâmica de tipo (*type checking*) e despacho de instruções a cada iteração de um laço `for`. Quando o volume de dados atinge centenas de milhares ou milhões de registros numéricos e tabulares, a iteração elemento a elemento no interpretador Python torna-se um gargalo severo de CPU e memória.

O **NumPy** resolve esse problema por meio do objeto `ndarray` (*N-dimensional array*): um contêiner multidimensional homogêneo no qual todos os elementos possuem exatamente o mesmo tipo de dado (`dtype`, como `float64`, `int32` ou `bool`) e são armazenados em um bloco contíguo de memória. Essa organização permite:

1. **Vetorização e Funções Universais (`ufuncs`):** Operações aritméticas (`+`, `-`, `*`, `/`), comparações lógicas e funções matemáticas (`np.log`, `np.exp`, `np.where`) são executadas em lote diretamente por rotinas compiladas em C e Fortran sobre o bloco de memória, sem laços no nível do Python. Isso reduz o tempo de execução em uma a duas ordens de grandeza (10x a 100x mais rápido) e diminui drasticamente o consumo de RAM.
2. **Fatiamento por Visualização (*Views* vs *Copies*):** Diferentemente das listas do Python, em que `lista[1:5]` aloca uma nova lista, o fatiamento básico de um `ndarray` (`arr[1:5]`) retorna uma *view* (janela de visualização) sobre o mesmo buffer de memória original, evitando cópias desnecessárias de grandes volumes de dados.

Construído sobre a semântica de arrays do NumPy, o **pandas** estende a computação vetorizada para dados tabulares heterogêneos (em que cada coluna pode ter um tipo distinto: numérico, texto, booleano ou temporal) por meio de duas estruturas principais:

- **`Series`:** Array unidimensional tipado associado a um array de rótulos chamado `Index`. Funciona simultaneamente como um vetor vetorizado e como um mapeamento indexado.
- **`DataFrame`:** Tabela bidimensional composta por uma coleção ordenada de colunas (`Series`) que compartilham o mesmo índice de linhas (`index`) e possuem um índice próprio de colunas (`columns`).

Duas propriedades operacionais distinguem o pandas de matrizes puras:
- **Alinhamento Automático por Índice:** Em operações aritméticas entre duas `Series` ou dois `DataFrames`, o pandas alinha automaticamente os elementos pelos rótulos do `Index` (e não apenas pela posição física), introduzindo `NaN` onde um rótulo existe em apenas um dos operandos.
- **Indexação Explícita (`.loc` vs `.iloc`):** Para eliminar ambiguidades quando um índice contém números inteiros fora de ordem, o pandas separa estritamente a seleção baseada em **rótulos** (`.loc[linhas, colunas]`, com intervalo final inclusivo) da seleção baseada em **posição inteira zero-indexada** (`.iloc[linhas, colunas]`, com intervalo final exclusivo).

---

## 2. Aplicação Prática

O código a seguir demonstra a diferença prática entre lógica condicional vetorizada com NumPy e pandas, o alinhamento automático de índices no cálculo de margens e a seleção e atualização segura com `.loc`:

```python
import numpy as np
import pandas as pd


def processar_carteira_pedidos() -> pd.DataFrame:
    # 1. Criação de DataFrame tabular heterogêneo indexado por código de produto
    vendas = pd.DataFrame(
        {
            "categoria": ["Hardware", "Cloud", "Licenca", "Cloud", "Hardware"],
            "quantidade": [12, 45, 8, 110, 3],
            "preco_unitario": [3500.0, 120.0, 950.0, 95.0, 4200.0],
        },
        index=["PRD_101", "PRD_205", "PRD_309", "PRD_412", "PRD_518"],
    )
    vendas.index.name = "produto_id"

    # 2. Série separada de custos unitários (em outra ordem e sem o PRD_518)
    custos_unitarios = pd.Series(
        {"PRD_309": 200.0, "PRD_101": 2600.0, "PRD_412": 40.0, "PRD_205": 55.0},
        name="custo_unitario",
    )

    # 3. Alinhamento automático pelo índice produto_id (PRD_518 receberá NaN)
    vendas["custo_unitario"] = custos_unitarios

    # Imputação vetorizada do custo ausente como 70% do preço unitário usando np.where
    vendas["custo_unitario"] = np.where(
        vendas["custo_unitario"].isna(),
        vendas["preco_unitario"] * 0.70,
        vendas["custo_unitario"],
    )

    # 4. Cálculos aritméticos 100% vetorizados (sem for/iterrows)
    vendas["receita_bruta"] = vendas["quantidade"] * vendas["preco_unitario"]
    vendas["custo_total"] = vendas["quantidade"] * vendas["custo_unitario"]
    vendas["margem_liquida"] = (
        vendas["receita_bruta"] - vendas["custo_total"]
    ) / vendas["receita_bruta"]

    # 5. Classificação multiclasse vetorizada com np.select
    condicoes = [
        (vendas["receita_bruta"] >= 10000.0) & (vendas["margem_liquida"] >= 0.40),
        (vendas["receita_bruta"] >= 10000.0) & (vendas["margem_liquida"] < 0.40),
    ]
    escolhas = ["ALTO_VALOR_ALTA_MARGEM", "ALTO_VALOR_MARGEM_COMPRIMIDA"]
    vendas["segmento"] = np.select(condicoes, escolhas, default="PADRAO")

    # 6. Seleção explícita com .loc (filtro booleano nas linhas + lista de colunas)
    relatorio_prioritario = vendas.loc[
        vendas["receita_bruta"] >= 10000.0,
        ["categoria", "receita_bruta", "margem_liquida", "segmento"],
    ].sort_values(by="receita_bruta", ascending=False)

    return relatorio_prioritario


if __name__ == "__main__":
    df_resultado = processar_carteira_pedidos()
    print(df_resultado.round(3))
```

---

## 3. Critério de Decisão

| Operação Desejada | Abordagem Recomendada | Abordagem a Evitar e Justificativa Técnica |
| :--- | :--- | :--- |
| Condicional binária sobre colunas (`se condicao então A senão B`) | `np.where(condicao, valor_se_verdadeiro, valor_se_falso)` ou `Series.mask()` / `Series.where()` | `df.apply(lambda row: ..., axis=1)` — executa função Python linha a linha, sendo de 50x a 200x mais lento que `np.where`. |
| Condicional com 3 ou mais regras mutuamente exclusivas | `np.select([cond1, cond2, ...], [val1, val2, ...], default=padrao)` | Cadeias aninhadas de `np.where` (difíceis de manter) ou laços `for idx, row in df.iterrows():`. |
| Filtragem de linhas e seleção simultânea de colunas (leitura ou escrita) | `df.loc[mascara_booleana, ["col_a", "col_b"]]` | Indexação encadeada `df[mascara_booleana]["col_a"] = valor`, que pode operar sobre uma cópia temporária sem alterar o `DataFrame` original. |
| Seleção estritamente posicional (ex.: primeiras 10 linhas e 3 primeiras colunas) | `df.iloc[:10, :3]` | `df.loc[:10, ...]` quando o índice não é um `RangeIndex` padrão ou após ordenação, pois `.loc` busca o rótulo `10` e não a décima posição. |
| Soma ou média entre duas séries/tabelas com possíveis chaves faltantes | `serie_a.add(serie_b, fill_value=0)` | `serie_a + serie_b` direto quando chaves ausentes não devem propagar `NaN` para o resultado final. |

---

## 4. Erros Comuns

1. **Mutação Involuntária de Arrays via *Slices* do NumPy:**
   - **Falha:** Criar um subconjunto `sub = arr[0:5]` e executar `sub[:] = 0` assumindo que `arr` permanecerá intacto. Como fatias básicas em NumPy são *views* do buffer original, todos os 5 primeiros elementos de `arr` serão zerados.
   - **Correção:** Quando precisar modificar um subconjunto de forma independente do array de origem, invoque explicitamente `sub = arr[0:5].copy()`.

2. **Indexação Encadeada (*Chained Indexing*) e `SettingWithCopyWarning`:**
   - **Falha:** Escrever `df[df["quantidade"] > 50]["preco_unitario"] = 100.0`. Essa expressão executa duas chamadas consecutivas (`__getitem__` seguido de `__setitem__`). Dependendo do layout interno de tipos do `DataFrame`, a primeira chamada pode retornar uma cópia descartável, fazendo com que a atribuição falhe silenciosamente no objeto original.
   - **Correção:** Realizar toda atribuição filtrada em uma única operação `.loc`: `df.loc[df["quantidade"] > 50, "preco_unitario"] = 100.0`.

3. **Uso de Operadores Booleanos Python (`and`, `or`, `not`) em Máscaras Vetoriais:**
   - **Falha:** Escrever `df[(df["a"] > 0) and (df["b"] < 10)]`. O operador `and` tenta avaliar o valor verdade escalar da `Series` inteira, disparando `ValueError: The truth value of a Series is ambiguous`. Além disso, omitir parênteses em `df["a"] > 0 & df["b"] < 10` causa erro porque o operador bitwise `&` tem precedência maior que `>` e `<`.
   - **Correção:** Utilizar sempre os operadores bit a bit `&` (AND), `|` (OR) e `~` (NOT) com cada comparação isolada entre parênteses: `df[(df["a"] > 0) & (df["b"] < 10)]`.

4. **Desalinhamento Silencioso ao Atribuir uma `Series` com Índice Diferente:**
   - **Falha:** Filtrar ou ordenar um `DataFrame` (`df_filtrado = df[df["ativo"]].reset_index(drop=True)`) e tentar atribuir a ele uma `Series` calculada a partir do `df` original antes do `reset_index`. O pandas alinhará pelos rótulos de índice antigos, associando valores às linhas erradas ou preenchendo com `NaN`.
   - **Correção:** Preservar o mesmo índice ao longo das transformações ou, quando a atribuição for comprovadamente posicional e de mesmo comprimento, atribuir o array subjacente (`df_filtrado["nova_col"] = serie_calculada.to_numpy()`).
