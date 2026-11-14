# 01. Preparação e Consultas Analíticas em SQL

> **Fonte(s) desta aula:**
> - **Tanimura, Cathy.** *SQL for Data Analysis: Advanced Techniques for Transforming Data into Insights* (1ª Edição, O'Reilly Media, 2021) — **Cap. 1** (*Analysis with SQL*, pp. 1–17), **Cap. 2** (*Preparing Data for Analysis*, pp. 19–59) e **Cap. 8** (*Creating Complex Data Sets for Analysis*, pp. 287–316).

---

## 1. Problema e Definição

A extração de dados para análise estatística, construção de relatórios ou treinamento de modelos depende da execução eficiente de transformações diretamente no sistema gerenciador de banco de dados (SGBD). Carregar tabelas brutas inteiras para a memória local em Python antes de filtrar, deduplicar e agregar registros causa gargalos de rede e esgotamento de memória RAM. O SQL (*Structured Query Language*), especificamente em seu subconjunto DQL (*Data Query Language*, centrado na instrução `SELECT`), permite delegar o processamento pesado de filtragem, junção, padronização e remodelagem tabular para o motor de execução do banco de dados.

A eficiência de uma consulta analítica depende primeiramente da arquitetura física de armazenamento:
1. **Bancos orientados a linhas (*Row-store*, ex.: PostgreSQL, MySQL):** Armazenam todos os atributos de uma tupla contiguamente em disco. São otimizados para cargas transacionais (OLTP) de escrita e leitura por chave primária, mas leem todas as colunas das páginas de dados mesmo quando a consulta projeta poucos atributos.
2. **Bancos orientados a colunas (*Column-store*, ex.: Snowflake, BigQuery, Redshift, ClickHouse):** Armazenam os valores de cada coluna contiguamente e comprimidos em blocos separados. São projetados para cargas analíticas (OLAP) e *data warehouses*, lendo estritamente as colunas requisitadas e aplicando agregações vetorizadas com baixo custo de entrada e saída (I/O).

Para construir conjuntos de dados analíticos corretos, o analista deve dominar a **ordem lógica de avaliação das cláusulas SQL** (distinta da ordem léxica de escrita):
1. `FROM` e `JOIN`: Produto cartesiano, predicados `ON` e união das tabelas de origem.
2. `WHERE`: Filtragem de linhas individuais antes do agrupamento.
3. `GROUP BY`: Agrupamento das linhas pelos valores únicos das expressões especificadas.
4. `HAVING`: Filtragem de grupos com base em funções de agregação (`COUNT`, `SUM`, `AVG`, `MIN`, `MAX`).
5. **Funções de Janela (*Window Functions*):** Cálculo de expressões `OVER (...)` pós-agrupamento.
6. `SELECT`: Projeção das colunas finais e atribuição de *aliases* (`AS`).
7. `DISTINCT`: Remoção de linhas duplicadas na projeção final.
8. `UNION` / `INTERSECT` / `EXCEPT`: Combinação de conjuntos de resultados.
9. `ORDER BY`: Ordenação determinística do conjunto final.
10. `LIMIT` / `OFFSET`: Restrição do número de linhas retornadas.

Essa sequência explica por que um *alias* definido no `SELECT` não pode ser usado no `WHERE` da mesma consulta (no padrão ANSI SQL), por que filtros sobre funções de janela exigem uma *Common Table Expression* (CTE) ou subconsulta externa, e por que predicados sobre a tabela à direita de um `LEFT JOIN` colocados no `WHERE` convertem silenciosamente a junção externa em `INNER JOIN`.

---

## 2. Aplicação Prática

A preparação de dados em SQL compreende quatro operações estruturais: perfilamento de distribuição e detecção de duplicatas, limpeza e coerção de tipos, remodelagem tabular (*pivoting* / *unpivoting*) e agregações multidimensionais com CTEs e `GROUPING SETS`.

### 2.1. Auditoria de Duplicatas e Perfilamento de Distribuições

Antes de agregar métricas financeiras ou operacionais, deve-se verificar a granularidade real da tabela (se a chave primária esperada é de fato única) e inspecionar a distribuição de variáveis contínuas por meio de histogramas discretizados (*binning* com `CASE`, `ROUND`, `LOG` ou `NTILE`):

```sql
-- 1. Detecção de violação de unicidade na chave (order_id, item_id)
WITH duplicatas AS (
    SELECT
        order_id,
        item_id,
        COUNT(*) AS qtd_registros
    FROM vendas_brutas
    GROUP BY order_id, item_id
    HAVING COUNT(*) > 1
)
SELECT
    qtd_registros,
    COUNT(*) AS total_chaves_afetadas
FROM duplicatas
GROUP BY qtd_registros
ORDER BY qtd_registros DESC;
```

### 2.2. Higienização, Tratamento de Nulos e Pivotamento Condicional

Para consolidar dados com falhas de registro, combinam-se quatro expressões essenciais: `CAST(x AS tipo)` (ou `x::tipo` em PostgreSQL) para conversão explícita de tipos, `COALESCE(val1, val2, ...)` para substituir `NULL` pelo primeiro argumento não nulo, `NULLIF(val1, val2)` para converter valores sentinelas (como strings vazias `''` ou zeros que causariam divisão por zero) em `NULL`, e `CASE WHEN ... THEN ... END` para recodificação categórica e pivotamento de linhas para colunas.

```sql
-- 2. Limpeza com CTE, deduplicação determinística e pivotamento + GROUPING SETS
WITH pedidos_limpos AS (
    SELECT
        order_id,
        customer_id,
        LOWER(TRIM(COALESCE(NULLIF(canal_venda, ''), 'nao_informado'))) AS canal,
        COALESCE(valor_bruto, 0.0)::NUMERIC(12, 2) AS receita_liquida,
        -- Calcula ticket médio por item protegendo contra divisão por zero
        COALESCE(valor_bruto, 0.0) / NULLIF(quantidade_itens, 0) AS preco_unitario,
        DATE_TRUNC('month', data_pedido::DATE)::DATE AS mes_pedido
    FROM vendas_brutas
    WHERE status_pedido NOT IN ('CANCELADO', 'TESTE_INTERNO')
      AND data_pedido IS NOT NULL
)
SELECT
    COALESCE(canal, 'TOTAL_GERAL') AS canal_venda,
    COUNT(DISTINCT order_id) AS total_pedidos,
    ROUND(AVG(preco_unitario), 2) AS media_preco_unitario,
    -- Pivotamento condicional (linhas -> colunas) por trimestre de 2025
    SUM(CASE WHEN mes_pedido BETWEEN '2025-01-01' AND '2025-03-31' THEN receita_liquida ELSE 0 END) AS receita_q1,
    SUM(CASE WHEN mes_pedido BETWEEN '2025-04-01' AND '2025-06-30' THEN receita_liquida ELSE 0 END) AS receita_q2
FROM pedidos_limpos
GROUP BY GROUPING SETS ((canal), ())
ORDER BY total_pedidos DESC;
```

No bloco acima, `GROUP BY GROUPING SETS ((canal), ())` calcula simultaneamente as agregações por `canal` e o subtotal global `()` em uma única varredura da tabela, eliminando a necessidade de concatenar uma segunda consulta via `UNION ALL`. Quando há múltiplas dimensões hierárquicas, `ROLLUP(dim1, dim2)` gera subtotais acumulados da esquerda para a direita, enquanto `CUBE(dim1, dim2)` gera todas as $2^k$ combinações possíveis de agregação. Para a operação inversa ao pivotamento (*unpivoting* — transformar colunas largas em formato longo *tidy*), utiliza-se `UNION ALL` selecionando um par `(nome_coluna, valor_coluna)` por ramo ou funções de expansão de arrays como `UNNEST(ARRAY[...])` em conjunto com `CROSS JOIN LATERAL`.

---

## 3. Critério de Decisão

Ao estruturar pipelines de preparação de dados em SQL, escolha a abstração técnica seguindo estas regras:

| Escolha Técnica | Quando Utilizar | Quando Evitar |
| :--- | :--- | :--- |
| **CTEs (`WITH nome AS (...)`)** | Consultas analíticas multi-etapas em que a legibilidade, a depuração incremental de cada bloco lógico e o reuso na mesma consulta são prioritários. | Quando o conjunto intermediário precisa ser consultado por múltiplas sessões ou scripts independentes, ou quando o otimizador do SGBD exige índices físicos sobre a tabela intermediária. |
| **Tabelas Temporárias (`CREATE TEMP TABLE`)** | Quando um resultado intermediário volumoso será referenciado repetidas vezes em consultas subsequentes da mesma sessão e se beneficia de estatísticas físicas ou índices próprios. | Ambientes onde o usuário analítico possui permissão estritamente de leitura (`SELECT`) ou em visualizações conectadas diretamente a ferramentas de BI que aceitam apenas uma instrução `SELECT`. |
| **Views (`CREATE VIEW`) vs. Tabelas Materializadas** | *Views* para encapsular lógica de negócio padronizada sem duplicar armazenamento; *Materialized Views* ou tabelas de ETL quando o cálculo base é custoso e consultado com alta frequência. | Evitar *views* empilhadas em múltiplos níveis (uma *view* que consulta outra *view*), pois ocultam junções redundantes e degradam severamente o plano de execução. |
| **Amostragem Determinística (`MOD(id_hash, 100) < 10`)** | Redução de volume em tabelas de bilhões de registros preservando todas as interações históricas do mesmo `user_id` na amostra de forma reprodutível. | Quando a chave sequencial possui correlação cíclica com o módulo escolhido (nesse caso, aplique uma função de *hash* criptográfico ou pseudoaleatório sobre o identificador antes do operador módulo). |

---

## 4. Erros Comuns

- **Uso indiscriminado de `SELECT DISTINCT` para mascarar explosão de junções (*fan-out*):** Quando um `JOIN` entre uma tabela de dimensão mal deduplicada e uma tabela de fatos multiplica o número de linhas, aplicar `DISTINCT` ou `COUNT(DISTINCT ...)` sem corrigir a cardinalidade da junção distorce somas (`SUM`) e médias (`AVG`), além de impor ordenação ou *hashing* de alto custo computacional. A correção obrigatória é agregar ou deduplicar a tabela secundária em uma CTE antes do `JOIN`.
- **Comparação direta com `NULL` usando operadores de igualdade (`= NULL` ou `!= NULL`):** Em SQL, `NULL` representa a ausência ou desconhecimento de valor, operando sob lógica ternária (`TRUE`, `FALSE`, `UNKNOWN`). Qualquer expressão `coluna = NULL` ou `coluna <> 'A'` avalia como `UNKNOWN` para registros nulos e descarta essas linhas no `WHERE`. Deve-se utilizar explicitamente `IS NULL`, `IS NOT NULL`, `IS DISTINCT FROM` ou envolver a coluna em `COALESCE(coluna, 'PADRAO')`.
- **Filtros na tabela externa dentro da cláusula `WHERE` após um `LEFT JOIN`:** Escrever `FROM clientes c LEFT JOIN compras p ON c.id = p.cliente_id WHERE p.ano = 2025` elimina todos os clientes sem compras em 2025 (pois `p.ano` é `NULL` para eles), anulando o efeito do `LEFT JOIN`. Condições restritivas sobre a tabela preservada à direita devem residir na cláusula `ON` (`LEFT JOIN compras p ON c.id = p.cliente_id AND p.ano = 2025`).
- **Divisão inteira truncada e falta de proteção em denominadores:** Em dialetos como PostgreSQL e SQL Server, dividir dois inteiros (`5 / 2`) retorna o inteiro truncado (`2`), subestimando taxas de conversão. Sempre converta um dos operandos para ponto flutuante ou decimal (`numerador * 1.0 / NULLIF(denominador, 0)`).
