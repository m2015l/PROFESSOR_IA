# Trilha 04 — Engenharia e Arquitetura de Dados

## Objetivo da Trilha
Capacitar o membro da Diretoria de Análise de Dados da ITAJr a projetar, construir e operar arquiteturas de dados confiáveis, escaláveis e manuteníveis. Ao concluir a trilha, o membro dominará o ciclo de vida da engenharia de dados, motores de armazenamento transacional (B-Trees e LSM-Trees) e analítico colunar (Parquet, Arrow, formatos de tabelas abertas Lakehouse), modelagem de dados analíticos (Inmon, Kimball, Data Vault e OBT), construção de pipelines de ingestão em lote e em tempo real (CDC, logs particionados e processamento de fluxos com controle de tempo de evento) e execução de transformações distribuídas, testes de qualidade e entrega de dados para analytics, Machine Learning e sistemas operacionais.

## Pré-requisitos
- Conclusão da **Trilha 01 — Python e Manipulação de Dados** (`01-python-e-manipulacao-de-dados/`).
- Conclusão da **Trilha 03 — SQL, Estatística e Storytelling com Dados** (`03-sql-estatistica-e-storytelling/`).
- Ambiente Python 3.10+ com `pyarrow`, `duckdb`, `pydantic` e motor SQL compatível com ANSI SQL / OLAP.

## Sequência de Aulas

1. **`01-ciclo-de-vida-e-arquitetura-de-dados.md`**
   Os cinco estágios do ciclo de vida da engenharia de dados e seus seis *undercurrents* transversais; propriedades fundamentais de sistemas intensivos em dados (confiabilidade, escalabilidade por percentis de latência e manutenibilidade); princípios de arquitetura (decisões reversíveis vs. irreversíveis, RTO/RPO, desacoplamento entre computação e armazenamento) e padrões arquiteturais (*Data Warehouse*, *Data Lake*, *Data Lakehouse* em camadas Bronze-Silver-Gold, *Lambda*, *Kappa*, modelo *Dataflow* unificado e *Data Mesh*).
2. **`02-armazenamento-formatos-colunares-e-modelagem.md`**
   Hierarquia física de armazenamento e temperatura de dados (*Hot*, *Warm*, *Cold*); motores OLTP orientados a páginas (*B-Trees* com *Write-Ahead Log*) vs. estruturados em log (*LSM-Trees* com *memtable*, *SSTables* e compactação); motores OLAP colunares, compressão (*Run-Length Encoding*, *Dictionary*, *Bitmap*), formatos de serialização e evolução de esquema (Avro, Protobuf, Apache Parquet, Apache Arrow, Delta Lake e Apache Iceberg); modelagem analítica (3NF/Inmon, modelagem dimensional de Kimball com *Star Schema* e *Slowly Changing Dimensions* Tipos 1, 2 e 3, *Data Vault* e *One Big Table*).
3. **`03-pipelines-de-ingestao-batch-e-streaming.md`**
   Sistemas de origem (*systems of record*) vs. sistemas de dados derivados; propriedades de ingestão (volumes limitados vs. ilimitados, síncrono vs. assíncrono, *push* vs. *pull*, contrapressão); extração em lote (*Full Snapshot* vs. incremental) e *Change Data Capture* (baseado em consulta vs. log binário de replicação); *message brokers* tradicionais vs. *partitioned logs* (Apache Kafka); processamento de *streams* (*Event Time* vs. *Processing Time*, *watermarks*, janelas temporais, junções em fluxo, idempotência e *Dead-Letter Queues*).
4. **`04-transformacao-qualidade-e-entrega-de-dados.md`**
   Evolução de ETL para ELT e transformações declarativas em SQL (dbt) vs. processamento distribuído programático (Spark); mecânica de junções distribuídas (*Broadcast Hash Join* vs. *Shuffle Sort-Merge Join* e mitigação de *data skew*); padrões de atualização física (*Truncate and Reload*, *Insert-Only*, *Copy-on-Write* vs. *Merge-on-Read* em `MERGE` e conformidade de exclusão); testes automatizados de qualidade, contratos de dados e observabilidade; entrega de dados (*Semantic Layer*, *Business/Operational/Embedded Analytics*, *Feature Stores* e *Reverse ETL*).

## Material Complementar e Referências
- **`referencias.md`** — Bibliografia primária detalhada e mapeamento de capítulos avançados para consulta sob demanda (replicação, particionamento, transações distribuídas, consenso tolerante a falhas Raft/Paxos em *Designing Data-Intensive Applications* Part II, e segurança, privacidade e redes em nuvem em *Fundamentals of Data Engineering* Caps. 10–11 e Apêndices).
