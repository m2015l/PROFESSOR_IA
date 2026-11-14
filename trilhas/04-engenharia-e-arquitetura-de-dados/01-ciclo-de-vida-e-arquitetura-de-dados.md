# 01. Ciclo de Vida e Arquitetura de Dados

> **Fonte(s) desta aula:**
> - **Reis, Joe; Housley, Matt.** *Fundamentals of Data Engineering: Plan and Build Robust Data Systems* (1ª Edição, O'Reilly Media, 2022) — **Cap. 1** (*Data Engineering Described*, pp. 18–59), **Cap. 2** (*The Data Engineering Lifecycle*, pp. 60–110), **Cap. 3** (*Designing Good Data Architecture*, pp. 111–170) e **Cap. 4** (*Choosing Technologies Across the Data Engineering Lifecycle*, pp. 171–223).
> - **Kleppmann, Martin.** *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems* (1ª Edição, O'Reilly Media, 2017) — **Cap. 1** (*Reliable, Scalable, and Maintainable Applications*, pp. 3–22).

---

## 1. Problema e Definição

Uma aplicação é classificada como intensiva em dados (*data-intensive*), em oposição a intensiva em computação (*compute-intensive*), quando seu gargalo primário reside no volume, na complexidade ou na taxa de mutação dos dados, e não na capacidade bruta de ciclos de CPU. Projetar e operar sistemas intensivos em dados exige abandonar a visão restrita a ferramentas isoladas e estruturar o fluxo ponta a ponta segundo o **Ciclo de Vida da Engenharia de Dados** (*Data Engineering Lifecycle*).

Reis e Housley decompõem esse ciclo em cinco estágios sequenciais sustentados por seis disciplinas transversais (*undercurrents*):

1. **Estágios Principais:**
   - **Geração (*Generation*):** Sistemas transacionais (OLTP), aplicações externas, IoT e logs de eventos que produzem dados brutos.
   - **Armazenamento (*Storage*):** Persistência durável e endereçável que conecta ingestão, transformação e entrega.
   - **Ingestão (*Ingestion*):** Coleta e transporte de dados das fontes para o armazenamento, em lote (*batch*) ou fluxo contínuo (*streaming*).
   - **Transformação (*Transformation*):** Padronização de tipos, aplicação de regras de negócio, modelagem, deduplicação e agregação.
   - **Entrega (*Serving Data*):** Disponibilização de dados para *Business Intelligence*, sistemas operacionais, *Machine Learning* e *Reverse ETL*.
2. **Disciplinas Transversais (*Undercurrents*):**
   - **Segurança (*Security*):** Controle de acesso (RBAC), princípio do menor privilégio e criptografia em trânsito e repouso.
   - **Gerenciamento de Dados (*Data Management*):** Governança, catalogação, linhagem, qualidade e conformidade regulatória (LGPD/GDPR).
   - **DataOps:** Automação de CI/CD, monitoramento operacional e resposta a incidentes em pipelines.
   - **Arquitetura de Dados (*Data Architecture*):** Avaliação de *trade-offs*, flexibilidade e custo total de propriedade (TCO).
   - **Orquestração (*Orchestration*):** Coordenação de dependências de execução via Grafos Acíclicos Direcionados (DAGs).
   - **Engenharia de Software:** Modularidade, controle de versão, testes automatizados e infraestrutura como código (IaC).

Kleppmann estabelece que toda arquitetura de dados deve otimizar três propriedades não funcionais:
- **Confiabilidade (*Reliability*):** Capacidade de operar corretamente mesmo diante de falhas parciais (*faults* de hardware, software ou erro humano), impedindo a indisponibilidade total do serviço (*failure*). Mede-se pelo **RTO** (*Recovery Time Objective* — tempo máximo tolerável de indisponibilidade) e pelo **RPO** (*Recovery Point Objective* — janela máxima aceitável de perda de dados).
- **Escalabilidade (*Scalability*):** Capacidade de manter o desempenho quando os parâmetros de carga (*load parameters* — requisições por segundo, razão leitura/escrita, usuários simultâneos) aumentam. O desempenho deve ser medido pelos **percentis de latência**: mediana ($p_{50}$) e percentis de cauda ($p_{95}$, $p_{99}$, $p_{99.9}$), pois a amplificação de latência em chamadas paralelas (*tail latency amplification*) degrada o tempo de resposta global.
- **Manutenibilidade (*Maintainability*):** Redução do custo de engenharia ao longo do tempo via **operabilidade** (visibilidade e administração rotineira), **simplicidade** (controle de complexidade acidental) e **evolvabilidade** (agilidade para adaptar esquemas e fluxos).

---

## 2. Aplicação Prática

Na prática de engenharia, a coordenação entre os estágios de ingestão, transformação e entrega é materializada por um motor de orquestração que valida um Grafo Acíclico Direcionado (DAG) de tarefas, enquanto a saúde da arquitetura é monitorada por métricas quantitativas de latência e frescor (*freshness*).

O código Python abaixo implementa um validador topológico de DAG (algoritmo de Kahn) acoplado a um monitor de SLA que calcula os percentis exatos de latência ($p_{50}, p_{95}, p_{99}$) e verifica violações de RPO/frescor das tabelas:

```python
from collections import deque
from dataclasses import dataclass, field
from datetime import datetime, timezone
import numpy as np

@dataclass
class TaskNode:
    task_id: str
    stage: str  # generation, ingestion, storage, transformation, serving
    upstream_ids: list[str] = field(default_factory=list)
    latencies_ms: list[float] = field(default_factory=list)
    last_success_utc: datetime | None = None

class PipelineArchitectureMonitor:
    def __init__(self, rpo_minutes: float, p99_sla_ms: float) -> None:
        self.rpo_minutes = rpo_minutes
        self.p99_sla_ms = p99_sla_ms
        self.tasks: dict[str, TaskNode] = {}

    def register_task(self, node: TaskNode) -> None:
        self.tasks[node.task_id] = node

    def resolve_execution_order(self) -> list[str]:
        """Retorna a ordenacao topologica do DAG ou levanta erro se houver ciclo."""
        in_degree = {tid: 0 for tid in self.tasks}
        adj: dict[str, list[str]] = {tid: [] for tid in self.tasks}

        for tid, node in self.tasks.items():
            for up_id in node.upstream_ids:
                if up_id not in self.tasks:
                    raise KeyError(f"Dependencia '{up_id}' nao registrada para '{tid}'.")
                adj[up_id].append(tid)
                in_degree[tid] += 1

        queue = deque([tid for tid, deg in in_degree.items() if deg == 0])
        order: list[str] = []

        while queue:
            current = queue.popleft()
            order.append(current)
            for downstream in adj[current]:
                in_degree[downstream] -= 1
                if in_degree[downstream] == 0:
                    queue.append(downstream)

        if len(order) != len(self.tasks):
            raise ValueError("Violacao arquitetural: ciclo detectado no grafo de tarefas.")
        return order

    def evaluate_reliability_and_latency(self, now_utc: datetime) -> dict[str, dict]:
        report: dict[str, dict] = {}
        for tid in self.resolve_execution_order():
            node = self.tasks[tid]
            arr = np.asarray(node.latencies_ms, dtype=np.float64)
            p50, p95, p99 = np.percentile(arr, [50, 95, 99]) if arr.size > 0 else (0.0, 0.0, 0.0)

            staleness_min = (
                (now_utc - node.last_success_utc).total_seconds() / 60.0
                if node.last_success_utc else float("inf")
            )
            report[tid] = {
                "stage": node.stage,
                "p50_ms": round(float(p50), 2),
                "p95_ms": round(float(p95), 2),
                "p99_ms": round(float(p99), 2),
                "staleness_min": round(staleness_min, 2),
                "rpo_violated": staleness_min > self.rpo_minutes,
                "latency_sla_violated": float(p99) > self.p99_sla_ms,
            }
        return report

if __name__ == "__main__":
    now = datetime(2026, 11, 14, 12, 0, tzinfo=timezone.utc)
    monitor = PipelineArchitectureMonitor(rpo_minutes=30.0, p99_sla_ms=2500.0)

    monitor.register_task(TaskNode(
        task_id="ingest_orders_cdc",
        stage="ingestion",
        latencies_ms=[420, 450, 480, 510, 490, 1850],
        last_success_utc=datetime(2026, 11, 14, 11, 45, tzinfo=timezone.utc),
    ))
    monitor.register_task(TaskNode(
        task_id="transform_silver_orders",
        stage="transformation",
        upstream_ids=["ingest_orders_cdc"],
        latencies_ms=[900, 950, 1020, 1100, 3100],
        last_success_utc=datetime(2026, 11, 14, 11, 20, tzinfo=timezone.utc),
    ))
    for task_id, metrics in monitor.evaluate_reliability_and_latency(now).items():
        print(f"{task_id}: {metrics}")
```

---

## 3. Critério de Decisão

A seleção da arquitetura e das tecnologias ao longo do ciclo de vida deve distinguir **decisões estruturais irreversíveis de alto custo de migração** (como a plataforma de nuvem ou o modelo de governança organizacional) de **decisões modulares reversíveis** (como a escolha de um conector de ingestão), priorizando o desacoplamento entre computação e armazenamento.

| Padrão Arquitetural | Estrutura Técnica | Quando Adotar | Quando Evitar |
| :--- | :--- | :--- | :--- |
| **Data Warehouse (DW) em Nuvem** | Armazenamento colunar gerenciado com esquema na escrita (*Schema-on-Write*) e motor MPP SQL. | Cargas estruturadas de BI, relatórios auditáveis e equipes centradas em SQL. | Ingestão massiva de dados não estruturados ou processamento direto por motores externos não suportados. |
| **Data Lake** | Armazenamento de objetos (S3/GCS) com arquivos brutos heterogêneos e *Schema-on-Read*. | Retenção econômica de grandes volumes brutos e exploração sem esquema prévio. | Sem camada transacional de metadados, perde garantias ACID (`UPDATE`/`DELETE`) e controle de qualidade. |
| **Data Lakehouse (Bronze / Silver / Gold)** | Metadados transacionais ACID (Delta Lake, Iceberg, Hudi) sobre arquivos Parquet em *Object Storage*, divididos em camadas de refinamento. | Unificação de engenharia de dados, BI e *Machine Learning* sobre armazenamento aberto compartilhado. | Volumes pequenos (< 10 GB) onde um banco relacional ou DW gerenciado exige menor esforço operacional. |
| **Arquitetura Lambda vs. Kappa / Dataflow** | *Lambda* separa pipelines *batch* e *streaming*; *Kappa* e *Dataflow* unificam o processamento sobre um log de eventos. | Adotar *Kappa/Dataflow* para processamento contínuo sub-segundo e reprocessamento histórico sem duplicar código. | Evitar *Lambda* pela duplicação de lógica entre lotes e tempo real; evitar *Kappa* para cargas puramente diárias. |
| **Data Mesh** | Descentralização sociotécnica: dados como produtos (*Data as a Product*) geridos por domínios autônomos com governança federada. | Grandes organizações com múltiplos domínios independentes e gargalo na equipe central de dados. | Organizações pequenas ou com baixa maturidade de engenharia nos domínios, onde a descentralização gera silos. |

---

## 4. Erros Comuns

- **Arquitetura Orientada a Currículo (*Resume-Driven Development*):** Adotar motores distribuídos complexos (clusters Kubernetes com Spark, Kafka e Flink) para processar poucos gigabytes de dados tabulares diários que seriam processados em segundos por uma única instância SQL ou motor *in-process* (DuckDB/PostgreSQL), inflando o custo operacional e o tempo de manutenção.
- **Dimensionar Sistemas pela Latência Média:** Avaliar o desempenho de consultas ou APIs de dados usando a média aritmética em vez dos percentis $p_{95}$ e $p_{99}$. Outliers na cauda da distribuição bloqueiam *workers* e causam falhas em cascata nos sistemas consumidores.
- **Acoplamento Rígido entre Armazenamento e Computação (*Monolith Lock-in*):** Gravar todos os dados exclusivamente em formatos proprietários fechados de um único motor de consulta, exigindo migrações completas e reescrita de pipelines quando surge a necessidade de executar cargas de *Machine Learning* ou motores alternativos sobre os mesmos dados.
- **Tratar Segurança, Qualidade e Orquestração como Etapas Posteriores:** Construir pipelines manuais sem controle de acesso, sem testes de esquema e sem DAGs determinísticos, tentando adicionar governança e observabilidade apenas após vazamentos de dados ou corrupção silenciosa em relatórios executivos.
