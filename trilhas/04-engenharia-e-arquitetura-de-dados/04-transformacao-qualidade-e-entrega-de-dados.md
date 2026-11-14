# 04. Transformação, Qualidade e Entrega de Dados

> **Fonte(s) desta aula:**
> - **Reis, Joe; Housley, Matt.** *Fundamentals of Data Engineering: Plan and Build Robust Data Systems* (1ª Edição, O'Reilly Media, 2022) — **Cap. 8** (*Queries, Modeling, and Transformation*, seções *Queries* e *Transformations*, pp. 390–406 e pp. 435–457) e **Cap. 9** (*Serving Data for Analytics, Machine Learning, and Reverse ETL*, pp. 458–497).
> - **Kleppmann, Martin.** *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems* (1ª Edição, O'Reilly Media, 2017) — **Cap. 10** (*Batch Processing*, seções de junções distribuídas e saídas de fluxos em lote, pp. 403–429) e **Cap. 12** (*The Future of Data Systems*, pp. 489–543).

---

## 1. Problema e Definição

Sem transformações estruturadas e validação rigorosa, dados ingeridos permanecem inertes e não confiáveis para tomada de decisão. Enquanto uma **consulta (*query*)** recupera e agrega registros existentes sob demanda, uma **transformação** altera estruturalmente o esquema, aplica regras de negócio, integra múltiplas fontes e persiste novos artefatos derivados nas camadas *Silver* e *Gold*. Com a consolidação de *Data Warehouses* elásticos e *Data Lakehouses*, o paradigma tradicional **ETL** (*Extract, Transform, Load*) migrou amplamente para **ELT** (*Extract, Load, Transform*): os dados brutos são carregados diretamente no armazenamento escalável e transformados de maneira declarativa via SQL modular (padrão *dbt*) ou motores de processamento distribuído (Apache Spark, Trino, DuckDB).

Para construir pipelines de transformação e entrega eficientes, o engenheiro deve dominar quatro pilares técnicos:

### 1.1. Mecânica de Junções Distribuídas e Assimetria (*Data Skew*)
Em motores distribuídos (MapReduce, Spark, MPP SQL), o custo de uma junção depende da movimentação de dados pela rede (*shuffle*):
1. **Broadcast Hash Join (*Map-Side Join*):** Quando uma tabela de fatos grande é unida a uma dimensão pequena que cabe na memória RAM de cada nó executor, o motor transmite uma cópia completa da dimensão para todos os nós, construindo uma tabela *hash* local e varrendo a tabela fato sem redistribuir suas partições pela rede.
2. **Shuffle Hash Join / Sort-Merge Join (*Reduce-Side Join*):** Quando ambas as tabelas são grandes, ambas são particionadas pelo *hash* da chave de junção, transferidas pela rede para os mesmos nós executores e ordenadas antes da mesclagem.
3. **Hot Spots e Assimetria (*Skew*):** Se uma única chave (ex.: `NULL` ou um cliente corporativo massivo) concentra milhões de registros, um único nó receptor sofre gargalo de memória e CPU. Mitiga-se filtrando chaves nulas antecipadamente (*filter early*) ou adicionando um sufixo aleatório (*key salting*) na tabela maior e replicando a chave correspondente na tabela menor.

### 1.2. Padrões de Atualização Física em Tabelas Analíticas
Atualizar arquivos colunares imutáveis exige escolher a estratégia correta de mutação:
- **Truncate and Reload:** Apaga e reescreve a tabela inteira; viável apenas para tabelas pequenas.
- **Insert-Only (Append):** Apenas anexa novos fatos imutáveis (ex.: logs de eventos), reconstruindo o estado atual via visão analítica (`ROW_NUMBER()`).
- **Upsert / Merge (`MERGE INTO`):** Combina inserções, atualizações e exclusões. Em tabelas *Lakehouse*, opera sob duas estratégias físicas: **Copy-on-Write (CoW)**, que reescreve inteiramente qualquer arquivo Parquet que contenha ao menos um registro alterado (otimizado para leitura, mas custoso na escrita), ou **Merge-on-Read (MoR)**, que grava apenas arquivos diferenciais de alteração/exclusão (*delete vectors*) e os reconcilia durante a leitura ou compactação posterior.

### 1.3. Qualidade, Contratos de Dados e Observabilidade
A integridade dos dados derivados deve ser auditada no próprio pipeline pelo padrão **Write-Audit-Publish (WAP)**: os dados transformados são gravados em uma partição ou *branch* isolada, submetidos a testes automatizados de **esquema** (unicidade, não nulidade, integridade referencial) e **testes estatísticos** (volume de linhas, distribuição de métricas e *freshness*/pontualidade frente ao SLA/SLO), e somente publicados para os consumidores se todas as asserções passarem.

### 1.4. Modalidades de Entrega (*Serving Data*)
A entrega final exige adequar a latência e a estrutura ao consumidor:
- **Business Analytics vs. Operational / Embedded Analytics:** Relatórios internos toleram latência de segundos sobre uma **Camada Semântica e de Métricas** (*Semantic Layer*) centralizada; já painéis embarcados em produtos (*Embedded Analytics*) e sistemas operacionais exigem consultas sub-segundo e alta concorrência.
- **Machine Learning e *Feature Stores*:** Modelos exigem consistência entre o histórico usado no treinamento (*offline store* em armazenamento colunar, evitando vazamento temporal via *point-in-time joins*) e os vetores de baixa latência servidos na inferência em produção (*online store* em banco chave-valor em memória), eliminando a distorção treino-serviço (*training-serving skew*).
- **Reverse ETL:** Sincronização de atributos analíticos calculados no *Warehouse/Lakehouse* (ex.: *Lead Score*, risco de *Churn*, LTV) de volta para sistemas operacionais SaaS (CRM, plataformas de cobrança e suporte).

---

## 2. Aplicação Prática

Abaixo implementamos: (1) uma transformação incremental idempotente em SQL (`MERGE INTO`) e (2) um validador **Write-Audit-Publish (WAP)** em Python que executa testes determinísticos e estatísticos sobre a tabela candidata antes de liberar a entrega (*serving*) ou disparar carga de *Reverse ETL*.

```sql
-- Transformacao incremental idempotente na camada Gold (faturamento diario por cliente)
MERGE INTO gold.fct_faturamento_cliente_diario AS tgt
USING (
    SELECT
        DATE_TRUNC('day', data_pedido)::DATE AS data_referencia,
        id_cliente,
        COUNT(DISTINCT id_pedido)            AS qtd_pedidos,
        SUM(valor_liquido)                   AS receita_liquida_brl
    FROM silver.pedidos_validados
    WHERE data_atualizacao >= CURRENT_TIMESTAMP - INTERVAL '2 days'
      AND id_cliente IS NOT NULL
    GROUP BY 1, 2
) AS src
ON  tgt.data_referencia = src.data_referencia
AND tgt.id_cliente      = src.id_cliente
WHEN MATCHED THEN
    UPDATE SET
        qtd_pedidos         = src.qtd_pedidos,
        receita_liquida_brl = src.receita_liquida_brl,
        atualizado_em       = CURRENT_TIMESTAMP
WHEN NOT MATCHED THEN
    INSERT (data_referencia, id_cliente, qtd_pedidos, receita_liquida_brl, atualizado_em)
    VALUES (src.data_referencia, src.id_cliente, src.qtd_pedidos, src.receita_liquida_brl, CURRENT_TIMESTAMP);
```

```python
from dataclasses import dataclass
import numpy as np

@dataclass
class DataQualityGate:
    expected_columns: set[str]
    primary_key: tuple[str, ...]
    min_row_count: int
    historical_mean_revenue: float
    historical_std_revenue: float
    max_z_score: float = 3.0

    def audit_staging_batch(self, rows: list[dict]) -> None:
        if len(rows) < self.min_row_count:
            raise AssertionError(f"Violacao de volume: {len(rows)} linhas < minimo ({self.min_row_count}).")

        actual_cols = set(rows[0].keys())
        missing = self.expected_columns - actual_cols
        if missing:
            raise AssertionError(f"Violacao de contrato de esquema. Colunas ausentes: {missing}")

        seen_keys: set[tuple] = set()
        revenues: list[float] = []
        for idx, row in enumerate(rows):
            key = tuple(row.get(k) for k in self.primary_key)
            if any(v is None for v in key):
                raise AssertionError(f"Violacao de nao-nulidade na chave primaria (linha {idx}).")
            if key in seen_keys:
                raise AssertionError(f"Violacao de unicidade na chave primaria: {key}.")
            seen_keys.add(key)

            rev = float(row["receita_liquida_brl"])
            if rev < 0:
                raise AssertionError(f"Valor de receita negativo detectado para chave {key}: {rev}")
            revenues.append(rev)

        batch_mean = float(np.mean(revenues))
        z_score = abs(batch_mean - self.historical_mean_revenue) / max(self.historical_std_revenue, 1e-9)
        if z_score > self.max_z_score:
            raise AssertionError(f"Anomalia estatistica na receita media (Z={z_score:.2f} > {self.max_z_score}).")
```

---

## 3. Critério de Decisão

| Cenário de Transformação e Entrega | Abordagem Recomendada | Justificativa Técnica |
| :--- | :--- | :--- |
| **Junção entre tabela fato (1 bilhão de linhas) e dimensão (< 50 MB) em motor distribuído** | **Broadcast Hash Join (*Map-Side*)** | Evita o tráfego de rede (*shuffle*) e a ordenação da tabela fato inteira, executando a junção localmente na memória de cada *worker*. |
| **Atualização de tabela *Lakehouse* com mutações de registros espalhadas por 80% das partições a cada 15 minutos** | **Merge-on-Read (MoR)** com compactação assíncrona programada | Evita a amplificação de escrita do *Copy-on-Write* (que reescreveria gigabytes de arquivos Parquet a cada micro-lote), gravando apenas arquivos diferenciais rápidos. |
| **Transformação pesada em PySpark / SQL distribuído** | **Expressões nativas SQL / DataFrame API** (evitando UDFs em Python puro) | Funções nativas são compiladas pelo otimizador (*Catalyst*) e executadas de forma vetorizada na JVM/C++; UDFs em Python exigem serialização linha a linha entre processos, degradando a performance em até uma ordem de grandeza. |
| **Servir *features* para modelo de recomendação online (< 20 ms) e treinamento histórico reprodutível** | **Feature Store Dual (Offline Colunar + Online Key-Value)** | Garante que a mesma definição matemática alimente o treino histórico via *point-in-time join* e a inferência em tempo real via leitura chave-valor em memória. |

---

## 4. Erros Comuns

- **Executar `MERGE` / `UPDATE` Linha a Linha (*Single-Row DML*) em Bancos Colunares:** Disparar milhares de instruções `UPDATE` individuais em Snowflake, BigQuery ou Delta Lake em vez de uma única operação em lote (`MERGE` set-based), gerando milhares de micro-arquivos e alto custo computacional.
- **Publicar Dados Transformados sem Auditoria Prévia (*Write-Publish* direto):** Gravar o resultado de uma transformação diretamente na tabela consumida pela diretoria sem validar unicidade de chaves, contagem de linhas e desvios estatísticos, propagando duplicações ou quedas de origem para relatórios executivos.
- **Ciclos de Retroalimentação (*Feedback Loops*) em *Reverse ETL*:** Sincronizar uma coluna calculada no *Data Warehouse* de volta para o CRM operacional e reingerir essa mesma atualização via CDC como se fosse uma nova modificação humana, disparando reprocessamentos infinitos.
- **Divergência de Métricas por Ausência de Camada Semântica Centralizada:** Permitir que cada painel de BI ou script de análise implemente sua própria fórmula de receita líquida, *Churn* ou margem de contribuição, resultando em números conflitantes em relatórios executivos.
