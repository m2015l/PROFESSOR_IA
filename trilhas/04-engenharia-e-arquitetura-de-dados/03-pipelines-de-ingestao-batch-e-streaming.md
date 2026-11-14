# 03. Pipelines de Ingestão: Batch e Streaming

> **Fonte(s) desta aula:**
> - **Reis, Joe; Housley, Matt.** *Fundamentals of Data Engineering: Plan and Build Robust Data Systems* (1ª Edição, O'Reilly Media, 2022) — **Cap. 5** (*Data Generation in Source Systems*, pp. 225–275) e **Cap. 7** (*Ingestion*, pp. 340–389).
> - **Kleppmann, Martin.** *Designing Data-Intensive Applications: The Big Ideas Behind Reliable, Scalable, and Maintainable Systems* (1ª Edição, O'Reilly Media, 2017) — **Cap. 10** (*Batch Processing*, pp. 389–429) e **Cap. 11** (*Stream Processing*, pp. 439–479).

---

## 1. Problema e Definição

A arquitetura de dados moderna divide os sistemas em duas categorias: **sistemas de registro** (*systems of record* ou *source of truth*), onde cada fato é inserido ou mutado pela primeira vez por aplicações transacionais, e **sistemas de dados derivados** (*derived data systems*, como *caches*, índices de busca textual, *data warehouses* e *data lakes*), que resultam da transformação determinística dos dados de origem. A **ingestão** é o estágio responsável por transportar dados dos sistemas de origem para o armazenamento analítico de modo confiável, superando gargalos de rede, limites de taxa (*rate limits*), mutações de esquema e indisponibilidades temporárias.

O projeto de um pipeline de ingestão fundamenta-se em cinco eixos técnicos:

1. **Dados Limitados (*Bounded*) vs. Ilimitados (*Unbounded*):**
   - Na realidade operacional, quase todos os dados de negócio são fluxos contínuos e ilimitados de eventos. A **ingestão em lote (*batch*)** discretiza artificialmente esse fluxo em conjuntos finitos delimitados por intervalos temporais (ex.: extração a cada 24 horas ou micro-lotes a cada 5 minutos). A **ingestão em fluxo (*streaming*)** processa cada evento individualmente assim que ele é produzido ou publicado.
2. **Acoplamento de Comunicação (*Push* vs. *Pull* e Síncrono vs. Assíncrono):**
   - No modelo **Pull / Polling**, o sistema de ingestão consulta periodicamente a fonte (bancos JDBC/ODBC, APIs REST). No modelo **Push**, a fonte envia ativamente o evento para o coletor (Webhooks, SDKs de telemetria). Comunicações **assíncronas** intermediadas por filas ou logs de mensagens evitam que uma lentidão no destino bloqueie a aplicação de origem, exigindo mecanismos de **contrapressão (*backpressure*)** para controlar a taxa de envio quando o consumidor atinge sua capacidade máxima.
3. **Padrões de Extração de Bancos de Dados e *Change Data Capture* (CDC):**
   - **Extração Completa (*Full Snapshot*):** Lê e transfere a tabela inteira a cada execução. É simples, mas torna-se inviável conforme a tabela cresce.
   - **CDC Baseado em Consulta (*Query-Based Differential*):** Filtra registros com `WHERE updated_at > :last_watermark`. Não exige acesso ao motor interno do banco, mas sobrecarrega o índice do OLTP e **não detecta exclusões físicas (`DELETE`)**, exigindo exclusão lógica (*soft delete*).
   - **CDC Baseado em Log (*Log-Based CDC*):** Lê diretamente o log binário interno de recuperação e replicação do banco de dados (`WAL` no PostgreSQL, `binlog` no MySQL, `redo log` no Oracle) por meio de conectores como Debezium. Captura todas as operações (`INSERT`, `UPDATE`, `DELETE`) em ordem estrita de efetivação sem impactar a CPU de consultas do banco transacional.
4. **Brokers de Mensagens Tradicionais vs. Logs Particionados (*Partitioned Logs*):**
   - *Message brokers* baseados em AMQP/JMS (RabbitMQ, ActiveMQ) entregam mensagens aos consumidores e as apagam da fila imediatamente após o recebimento da confirmação (*ACK*).
   - **Logs particionados baseados em disco** (Apache Kafka, Amazon Kinesis) gravam eventos de forma imutável (*append-only*) divididos em partições escaláveis. Cada evento recebe um número sequencial monotônico (**offset**). Os consumidores apenas avançam seu ponteiro de leitura, permitindo que múltiplos grupos de consumidores independentes (*fan-out*) leiam o mesmo fluxo simultaneamente e que pipelines inteiros sejam **reprocessados (*replay*)** retrocedendo o *offset*, além de suportar **compactação de log (*log compaction*)** para reter apenas o último estado de cada chave primária.
5. **Semântica Temporal e Garantias de Entrega em *Streams*:**
   - Deve-se separar estritamente o **Tempo do Evento (*Event Time*)** — instante real em que o fato ocorreu no dispositivo ou transação — do **Tempo de Processamento (*Processing Time*)** — instante em que o servidor de ingestão processa o registro. Atrasos de rede geram eventos fora de ordem (*stragglers*), controlados por **limiares de completude temporal (*watermarks*)** sobre janelas temporais (**Tumbling** de tamanho fixo sem sobreposição, **Hopping** de tamanho fixo com passo deslizante, **Sliding** baseadas na distância exata entre eventos e **Session** delimitadas por períodos de inatividade).
   - Como falhas de rede impedem confirmações perfeitas sem coordenação custosa, a maioria dos coletores opera em regime **pelo menos uma vez (*at-least-once*)**, o que exige que o destino aplique **escrita idempotente** para alcançar efeito equivalente a **exatamente uma vez (*effectively-once*)**, isolando mensagens corrompidas em uma **Dead-Letter Queue (DLQ)**.

---

## 2. Aplicação Prática

O código Python abaixo implementa um consumidor de eventos de **CDC baseado em log** que aplica: (1) roteamento de eventos corrompidos para uma *Dead-Letter Queue* (DLQ), (2) deduplicação e controle de ordem por *Event Time* e *offset* (garantindo **idempotência** sob entrega *at-least-once*), e (3) agregação em **janelas fixas (*tumbling windows*)** com tolerância a atraso (*watermark*) para separar eventos no prazo de eventos tardios (*late events*):

```python
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any

@dataclass(frozen=True)
class CDCEvent:
    offset: int
    op: str  # 'c' (create), 'u' (update), 'd' (delete)
    order_id: str
    amount: float
    event_time: datetime

class IdempotentStreamIngestor:
    def __init__(self, window_size_min: int, allowed_lateness_min: int) -> None:
        self.window_delta = timedelta(minutes=window_size_min)
        self.allowed_lateness = timedelta(minutes=allowed_lateness_min)
        self.max_event_time: datetime | None = None
        self.state_store: dict[str, tuple[int, float]] = {}  # order_id -> (last_offset, amount)
        self.dlq: list[dict[str, Any]] = []
        self.late_events: list[CDCEvent] = []

    def _parse_raw(self, raw: dict[str, Any]) -> CDCEvent | None:
        try:
            if raw["op"] not in {"c", "u", "d"} or float(raw.get("amount", 0.0)) < 0:
                raise ValueError("Operacao invalida ou valor negativo.")
            return CDCEvent(
                offset=int(raw["offset"]),
                op=str(raw["op"]),
                order_id=str(raw["order_id"]),
                amount=float(raw.get("amount", 0.0)),
                event_time=datetime.fromisoformat(raw["event_time"]),
            )
        except (KeyError, ValueError, TypeError) as exc:
            self.dlq.append({"raw_payload": raw, "error": str(exc)})
            return None

    def process_batch(self, raw_messages: list[dict[str, Any]]) -> dict[str, float]:
        for raw in raw_messages:
            ev = self._parse_raw(raw)
            if ev is None:
                continue

            # Atualiza o relogio de Event Time e calcula a Watermark atual
            if self.max_event_time is None or ev.event_time > self.max_event_time:
                self.max_event_time = ev.event_time
            watermark = self.max_event_time - self.allowed_lateness

            if ev.event_time < watermark:
                self.late_events.append(ev)
                continue

            # Idempotencia por chave primaria e monotonicidade de offset do log
            prev = self.state_store.get(ev.order_id)
            if prev is not None and ev.offset <= prev[0]:
                continue  # Ignora reentrega duplicada (at-least-once -> effectively-once)

            if ev.op == "d":
                self.state_store.pop(ev.order_id, None)
            else:
                self.state_store[ev.order_id] = (ev.offset, ev.amount)

        return {oid: val for oid, (_, val) in self.state_store.items()}
```

---

## 3. Critério de Decisão

| Requisito Operacional | Padrão Recomendado | Justificativa Técnica |
| :--- | :--- | :--- |
| **Replicação de tabela OLTP (> 10 milhões de linhas) com exclusões físicas (`DELETE`) e baixo impacto no banco de produção** | **Log-Based CDC** (ex.: Debezium lendo `WAL`/`binlog` para Kafka ou Object Storage) | Lê apenas os bytes alterados sequencialmente no log de transações, preserva eventos de exclusão via *tombstones* e evita consultas `SELECT` pesadas sobre as tabelas ativas. |
| **Integração com API SaaS externa sem suporte a Webhooks ou logs de eventos** | **Batch / Micro-batch Incremental via Polling** com *exponential backoff*, paginação por cursor e controle de *watermark* | Respeita limites de requisição (*rate limits*), retoma do último ponto salvo em caso de falha HTTP 429/5xx e grava o JSON bruto na camada *Bronze* antes de transformar. |
| **Múltiplos sistemas consumidores independentes (BI, antifraude em tempo real, busca textual) lendo os mesmos eventos** | **Partitioned Log** (Apache Kafka / Redshift/Kinesis) em vez de fila AMQP tradicional | Preserva os eventos em disco por período configurável ou compactação por chave, permitindo leituras paralelas sem bloqueio mútuo e *replay* histórico a partir de qualquer *offset*. |
| **Enriquecimento de fluxo de eventos com tabela cadastral de baixa mutação** | **Stream-Table Join com Estado Local** alimentado por tópico CDC compactado | Mantém uma cópia local indexada da tabela dimensão no próprio nó processador de *stream*, eliminando chamadas de rede síncronas por evento ao banco de dados remoto. |

---

## 4. Erros Comuns

- **Agrupar Janelas Temporais pelo *Processing Time* em vez do *Event Time*:** Quando um lote de eventos atrasados (por queda temporária de rede ou dispositivo *offline*) chega ao servidor, o uso de *Processing Time* concentra todos os registros atrasados na janela do instante de chegada, distorcendo métricas financeiras e operacionais.
- **Executar *Full Snapshot* ou *Query-Based CDC* sem Índice diretamente na Instância Primária OLTP:** Disparar varreduras completas em horário de pico comercial esgota o *buffer pool* de memória e as conexões do banco transacional, derrubando a aplicação voltada ao cliente; extrações por consulta devem apontar para uma réplica de leitura (*read replica*).
- **Ausência de Idempotência no Consumidor:** Usar instruções `INSERT` cegas ao consumir filas ou reexecutar tarefas de lote que falharam no meio, gerando registros duplicados a cada tentativa de *retry*.
- **Interromper o Pipeline Inteiro por um Único Registro Malformado:** Não isolar falhas de desserialização ou violação de esquema em uma *Dead-Letter Queue* (DLQ), fazendo com que o consumidor entre em loop infinito de falha e reinicialização no mesmo *offset*.
