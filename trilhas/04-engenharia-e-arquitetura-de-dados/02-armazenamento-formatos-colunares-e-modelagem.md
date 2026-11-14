# 02. Armazenamento, Formatos Colunares e Modelagem

> **Fonte(s) desta aula:**
> - **Reis, Joe; Housley, Matt.** *Fundamentals of Data Engineering: Plan and Build Robust Data Systems* (1ª Edição, O'Reilly Media, 2022) — **Cap. 6** (*Storage*, pp. 276–339), **Cap. 8** (seção *Data Modeling*, pp. 406–435) e **Apêndice A** (*Serialization and Compression Technical Details*, pp. 529–536).
> - **Kleppmann, Martin.** *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems* (1ª Edição, O'Reilly Media, 2017) — **Cap. 2** (*Data Models and Query Languages*, pp. 27–63), **Cap. 3** (*Storage and Retrieval*, pp. 69–103) e **Cap. 4** (*Encoding and Evolution*, pp. 111–139).

---

## 1. Problema e Definição

O subsistema de armazenamento está presente em todas as etapas do ciclo de vida dos dados e exige equilibrar latência de acesso, taxa de transferência (*throughput*), durabilidade e custo financeiro conforme a frequência de acesso (**temperatura dos dados**: *Hot* para acesso imediato em RAM/NVMe, *Warm* para consultas periódicas e *Cold* para arquivamento de longo prazo em *Object Storage*).

Para projetar camadas de persistência eficientes, o engenheiro deve distinguir três dimensões técnicas:

### 1.1. Motores de Armazenamento OLTP vs. OLAP
1. **Árvores B (*B-Trees*):** Padrão em bancos relacionais transacionais (PostgreSQL, MySQL/InnoDB). Organizam os dados em páginas ou blocos de tamanho fixo (tipicamente 4 KB a 16 KB) ordenados pela chave primária, atualizando páginas *in-place* e garantindo atomicidade e durabilidade via **Write-Ahead Log (WAL)**. Oferecem leituras pontuais e por intervalo com complexidade $O(\log N)$, mas sofrem com acessos aleatórios em disco durante escritas intensas.
2. **Árvores Estruturadas em Log (*LSM-Trees* — *Log-Structured Merge-Trees*):** Utilizadas em motores de alta taxa de escrita (RocksDB, Cassandra, HBase). As inserções e atualizações são gravadas sequencialmente em um log em disco e inseridas em uma estrutura ordenada em memória (**memtable**, como uma *red-black tree* ou *skip list*). Quando a *memtable* atinge seu limite, é descarregada no disco como um arquivo imutável ordenado (**SSTable** — *Sorted String Table*). Processos em segundo plano executam a **compactação** (*compaction*) para mesclar *SSTables* e descartar versões sobrescritas ou marcadores de exclusão (*tombstones*), enquanto **filtros de Bloom** (*Bloom filters*) evitam leituras de disco para chaves inexistentes.
3. **Armazenamento Colunar (OLAP):** Cargas analíticas varrem milhões de registros projetando poucas colunas. Em vez de armazenar tuplas inteiras contiguamente, os motores colunares gravam cada atributo separadamente, permitindo ler apenas as colunas necessárias e aplicar algoritmos de compressão de alta eficiência, como **codificação por dicionário** (*Dictionary Encoding*), **codificação de comprimento de carreira** (*Run-Length Encoding* — RLE) e **índices de mapas de bits** (*Bitmap Indexes*), além de execução vetorizada em lotes nos caches L1/L2 da CPU (instruções SIMD).

### 1.2. Serialização, Evolução de Esquema e Tabelas Abertas
A troca e a persistência de dados dependem de formatos de codificação que suportem **compatibilidade regressiva** (*backward compatibility* — código novo lê dados antigos) e **compatibilidade progressiva** (*forward compatibility* — código antigo lê dados novos ignorando campos adicionados):
- **Formatos baseados em linhas:** **Apache Avro** (separa o esquema do *writer* e do *reader* em JSON, gravando binário compacto sem tags numéricas, ideal para *staging* e *streams* Kafka) e **Protocol Buffers (Protobuf)** (associa cada campo a uma *tag* numérica imutável).
- **Formatos colunares híbridos em disco e em memória:** **Apache Parquet** e **Apache ORC** dividem os dados horizontalmente em grupos de linhas (*row groups* de 128 MB a 1 GB) e verticalmente em blocos de colunas (*column chunks*) divididos em páginas com estatísticas `min`/`max` no rodapé para salto de blocos (*predicate pushdown*). **Apache Arrow** padroniza o layout colunar **em memória RAM** para transferência *zero-copy* entre processos (Python, C++, JVM) sem custo de desserialização.
- **Formatos de Tabelas Abertas (*Lakehouse*):** **Delta Lake**, **Apache Iceberg** e **Apache Hudi** adicionam um registro de transações e manifestos de metadados sobre arquivos Parquet em *Object Storage*, habilitando transações ACID, isolamento de *snapshot*, *Time Travel*, evolução de esquema e alteração de particionamento sem reescrever os arquivos físicos (*hidden partitioning*).

### 1.3. Paradigmas de Modelagem Analítica
- **Terceira Forma Normal (3NF / Inmon):** Elimina redundâncias funcionais e transitivas para preservar integridade de escrita; utilizado no núcleo corporativo integrado antes da derivação de *data marts*.
- **Modelagem Dimensional (Kimball):** Organiza os dados em **Tabelas Fato** (medições quantitativas aditivas definidas em um **grão** estrito e imutável) cercadas por **Tabelas Dimensão** desnormalizadas (contexto descritivo *quem, o quê, onde, quando* em um **Star Schema**; se normalizadas em subdimensões, formam um **Snowflake Schema**). O rastreamento histórico de atributos dimensionais é resolvido por **Slowly Changing Dimensions (SCD)**: **Tipo 1** (sobrescrita sem histórico), **Tipo 2** (inserção de nova linha com chave substituta *surrogate key*, datas de início/fim de vigência e flag de registro ativo) e **Tipo 3** (coluna adicional para o valor imediatamente anterior).
- **Data Vault:** Projetado para auditoria histórica rigorosa e agilidade na ingestão de múltiplas fontes, separando chaves de negócio (**Hubs**), relacionamentos (**Links**) e atributos descritivos temporais (**Satellites**) vinculados por chaves de *hash*.
- **One Big Table (OBT):** Desnormalização completa da tabela fato com suas dimensões em uma única tabela larga colunar, eliminando o custo de `JOIN` em motores OLAP que comprimem valores repetidos via RLE.

---

## 2. Aplicação Prática

Abaixo implementamos: (1) a escrita otimizada de dados analíticos em **Apache Parquet** com `pyarrow`, demonstrando ordenação prévia para maximizar compressão RLE e *predicate pushdown*; e (2) a atualização SQL determinística de uma **Dimensão SCD Tipo 2**.

```python
import pyarrow as pa
import pyarrow.parquet as pq

def write_optimized_parquet(records: list[dict], output_path: str) -> dict:
    """Ordena pela chave de filtro para otimizar RLE e min/max de Row Groups."""
    schema = pa.schema([
        ("tenant_id", pa.string()),
        ("event_date", pa.date32()),
        ("user_id", pa.int64()),
        ("amount_brl", pa.decimal128(12, 2)),
    ])
    table = pa.Table.from_pylist(records, schema=schema)
    sorted_table = table.sort_by([("tenant_id", "ascending"), ("event_date", "ascending")])

    pq.write_table(
        sorted_table,
        output_path,
        compression="ZSTD",
        use_dictionary=["tenant_id"],
        row_group_size=100_000,
        write_statistics=True,
    )
    meta = pq.read_metadata(output_path)
    rg0 = meta.row_group(0)
    return {
        "num_rows": meta.num_rows,
        "num_row_groups": meta.num_row_groups,
        "col0_compression": rg0.column(0).compression,
        "col0_min": rg0.column(0).statistics.min,
        "col0_max": rg0.column(0).statistics.max,
    }
```

```sql
-- Implementacao de Slowly Changing Dimension Tipo 2 (SCD2) para dim_cliente
-- Passo 1: Expirar os registros ativos cujo atributo monitorado (segmento ou uf) mudou
UPDATE dw.dim_cliente AS dim
SET
    data_fim_vigencia = stg.data_atualizacao,
    registro_ativo    = FALSE
FROM staging.clientes_cdc AS stg
WHERE dim.id_cliente_natural = stg.id_cliente
  AND dim.registro_ativo = TRUE
  AND (
      dim.segmento IS DISTINCT FROM stg.segmento
      OR dim.uf IS DISTINCT FROM stg.uf
  );

-- Passo 2: Inserir novos clientes e novas versoes dos clientes que sofreram alteracao
INSERT INTO dw.dim_cliente (
    sk_cliente,
    id_cliente_natural,
    nome_cliente,
    segmento,
    uf,
    data_inicio_vigencia,
    data_fim_vigencia,
    registro_ativo
)
SELECT
    MD5(stg.id_cliente::TEXT || '|' || stg.data_atualizacao::TEXT) AS sk_cliente,
    stg.id_cliente                                                 AS id_cliente_natural,
    stg.nome_cliente,
    stg.segmento,
    stg.uf,
    stg.data_atualizacao                                           AS data_inicio_vigencia,
    TIMESTAMP '9999-12-31 23:59:59'                                AS data_fim_vigencia,
    TRUE                                                           AS registro_ativo
FROM staging.clientes_cdc AS stg
LEFT JOIN dw.dim_cliente AS dim_ativa
    ON stg.id_cliente = dim_ativa.id_cliente_natural
   AND dim_ativa.registro_ativo = TRUE
WHERE dim_ativa.sk_cliente IS NULL;
```

---

## 3. Critério de Decisão

| Componente / Camada | Alternativa A | Alternativa B | Regra de Escolha Técnica |
| :--- | :--- | :--- | :--- |
| **Motor Transacional (OLTP)** | **B-Tree** (PostgreSQL, MySQL) | **LSM-Tree** (RocksDB, Cassandra) | Escolha **B-Tree** quando a carga exigir leituras previsíveis de baixa latência e transações relacionais fortes; escolha **LSM-Tree** quando a taxa de ingestão/escrita contínua exceder a capacidade de I/O aleatório do disco. |
| **Formato de Persistência em Dados Brutos vs. Analíticos** | **Apache Avro** (orientado a linhas) | **Apache Parquet** (colunar híbrido) | Use **Avro** em tópicos de *streaming* e *landing zones* onde a linha inteira é lida ou escrita e a evolução de esquema é frequente; use **Parquet** nas camadas *Silver/Gold* para varreduras analíticas, compressão colunar e *predicate pushdown*. |
| **Modelagem de Camada Analítica** | **Star Schema (Kimball)** | **One Big Table (OBT)** | Adote **Star Schema** quando houver necessidade de governança semântica centralizada, dimensões conformadas (*conformed dimensions*) compartilhadas entre múltiplos processos de negócio e atualizações frequentes de dimensões; adote **OBT** na camada final de consumo quando o motor colunar cobrar por bytes escaneados/CPU em `JOIN`s pesados e a largura da tabela acelerar dashboards e extração de *features*. |

---

## 4. Erros Comuns

- **Problema dos Arquivos Pequenos (*Small Files Problem*):** Gravar milhares de arquivos Parquet com poucos kilobytes (ex.: um arquivo por micro-lote de *streaming* ou particionamento por coluna de alta cardinalidade como `user_id`). Isso sobrecarrega a listagem de metadados no *Object Storage* e destrói a compressão colunar dos *row groups*.
- **Misturar Grãos na Mesma Tabela Fato:** Combinar métricas de cabeçalho de pedido (frete total, desconto global) com métricas de item de pedido na mesma tabela fato sem rateio proporcional, causando duplicação aritmética em agregações `SUM()`.
- **Usar Chaves Naturais Mutáveis em Junções Históricas:** Vincular tabelas fato diretamente ao `id_cliente` natural em vez da *surrogate key* (`sk_cliente`) de uma dimensão SCD Tipo 2, atribuindo incorretamente todas as vendas passadas ao estado cadastral atual do cliente.
- **Quebra de Compatibilidade em Evolução de Esquema:** Renomear colunas ou alterar o tipo primitivo de um campo obrigatório sem valor padrão (*default*) em esquemas Avro/Protobuf/Parquet sem coordenar leitores e escritores.
