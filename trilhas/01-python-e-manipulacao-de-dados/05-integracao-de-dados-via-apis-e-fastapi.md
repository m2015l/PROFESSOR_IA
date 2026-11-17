# Aula 05 — Integração de Dados via APIs HTTP, Pydantic e FastAPI

> **Fonte(s) desta aula:**
> - Livro: *Python for Data Analysis* (3ª Edição, Wes McKinney) — Capítulo 6, Seção 6.3 (*Interacting with Web APIs*, pp. 197–199).
> - Documentação Oficial: *FastAPI Tutorial — User Guide* ([https://fastapi.tiangolo.com/tutorial/](https://fastapi.tiangolo.com/tutorial/)).

---

## 1. Problema e Definição

Pipelines de dados não operam apenas sobre arquivos estáticos em disco: eles precisam extrair registros de sistemas externos via APIs REST (CRMs, ERPs, plataformas financeiras) e, no sentido inverso, expor resultados analíticos, indicadores ou inferências de modelos para outros sistemas por meio de serviços HTTP. Sem validação formal de esquema e controle de transporte HTTP, integrações de dados falham por mudanças silenciosas no formato JSON das respostas, ausência de timeouts de rede ou serialização incorreta de tipos do NumPy/pandas (como `np.nan` e `np.int64`, que não fazem parte da especificação JSON padrão RFC 8259).

Uma arquitetura robusta de integração de dados em Python apoia-se em três componentes:

1. **Consumo Resiliente de APIs HTTP (`httpx` ou `requests`):**
   - Toda chamada externa sobre a rede deve definir um **timeout explícito** (conexão e leitura) para impedir que o processo trave indefinidamente caso o servidor remoto não responda.
   - O código deve verificar o código de status HTTP (`response.raise_for_status()`), tratar paginação (`offset`/`limit` ou cursores) e reutilizar conexões TCP/TLS por meio de um cliente persistente (`httpx.Client` ou `httpx.AsyncClient`).

2. **Validação de Contratos de Dados com Pydantic (`BaseModel`):**
   - Dicionários JSON recebidos da rede são estruturas sem garantia de tipo. O **Pydantic** utiliza as anotações de tipo do Python para validar em tempo de execução a presença de campos obrigatórios, converter tipos compatíveis (ex.: string ISO `"2026-11-14"` para objeto `date`) e rejeitar payloads malformados com erros estruturados (`ValidationError`) antes que dados corrompidos entrem no `DataFrame` ou banco de dados.

3. **Exposição de Serviços de Dados com FastAPI:**
   - O **FastAPI** é um framework web ASGI de alto desempenho baseado em Starlette e Pydantic. Ao declarar parâmetros de rota (*path parameters*), parâmetros de consulta (*query parameters*) e modelos Pydantic para o corpo da requisição (*request body*) e de resposta (`response_model`), o FastAPI executa automaticamente:
     - Parsing e validação dos dados de entrada;
     - Serialização segura de tipos complexos (`datetime`, `UUID`, `Decimal`, listas de registros) para JSON;
     - Geração automática da especificação OpenAPI (`/openapi.json`) e documentação interativa (`/docs`).

---

### Fundamentos e Exemplos Progressivos Passo a Passo (Partindo do Zero)

Veja do zero cada peça usada antes de integrá-las em um serviço completo:

1. **Requisições HTTP com `httpx` (`GET`, `timeout` e `raise_for_status()`):**
   Quando um programa busca dados na internet ou em outro serviço interno, ele envia uma requisição HTTP (`GET` para ler, `POST` para enviar/processar) para uma URL e recebe um código numérico de status (`200` = sucesso; `400`/`422` = dados inválidos; `429` = excesso de chamadas; `500` = falha no servidor) junto de um corpo de texto em formato **JSON** (muito parecido com dicionários e listas em Python).
   O bloco `with httpx.Client(timeout=5.0) as client:` abre uma conexão reutilizável com tempo máximo de espera de 5 segundos e a fecha automaticamente ao sair do bloco.

   ```python
   import httpx

   with httpx.Client(timeout=5.0) as client:
       resp = client.get("https://api.exemplo.com/itens", params={"page": 1})
       resp.raise_for_status()   # Lança erro automaticamente se o status for >= 400
       dados = resp.json()       # Converte o texto JSON da resposta em dict/list Python
   ```

2. **Validação de esquemas com `Pydantic` (`BaseModel`, `Field` e `ValidationError`):**
   Um dicionário vindo de fora pode ter campos faltando ou tipos errados (ex.: `"valor": -50` ou `"valor": "abc"`). No Pydantic, criamos uma classe herdando de `BaseModel` onde cada atributo declara seu tipo e restrições opcionais via `Field(...)` (`gt=0` = maior que 0; `ge=0` = maior ou igual a 0; `min_length=3` = texto com ao menos 3 caracteres).
   - `MinhaClasse.model_validate(dicionario)` valida e converte tipos; se falhar, lança `ValidationError`.
   - `objeto.model_dump()` converte o modelo validado de volta para um `dict` comum.

   ```python
   from pydantic import BaseModel, Field, ValidationError

   class Produto(BaseModel):
       sku: str = Field(..., min_length=3)
       preco: float = Field(..., gt=0.0)

   valido = Produto.model_validate({"sku": "ABC", "preco": "19.5"})
   print(valido.model_dump())  # Saída: {'sku': 'ABC', 'preco': 19.5} (converteu str para float)

   try:
       Produto.model_validate({"sku": "AB", "preco": -10.0})
   except ValidationError as err:
       print("Falhou na validação:", len(err.errors()), "erros encontrados")
   ```

3. **Criando uma rota mínima com `FastAPI`:**
   No FastAPI, `app = FastAPI()` cria a aplicação. O decorador `@app.post("/rota", response_model=...)` registra uma função Python que será executada sempre que alguém enviar um `POST` para `/rota`:
   - Parâmetros cujo tipo é uma classe `BaseModel` são lidos automaticamente do corpo JSON da requisição.
   - Parâmetros simples anotados com `Query(...)` vêm na URL (`?minimo=10`).
   - `raise HTTPException(status_code=400, detail="...")` devolve um erro HTTP claro ao cliente.

   ```python
   from fastapi import FastAPI, HTTPException
   from pydantic import BaseModel

   app = FastAPI()

   class Entrada(BaseModel):
       x: float
       y: float

   @app.post("/somar")
   def somar(dados: Entrada, fator: float = 1.0) -> dict[str, float]:
       if fator <= 0:
           raise HTTPException(status_code=400, detail="fator deve ser positivo")
       return {"resultado": (dados.x + dados.y) * fator}
   ```

---

## 2. Aplicação Prática

O código abaixo demonstra as duas pontas da integração: (1) um cliente HTTP com timeout e validação Pydantic que converte lotes JSON validados em `DataFrame`, e (2) uma API FastAPI que recebe um lote de transações, processa métricas vetorizadas no pandas e devolve um contrato de resposta estritamente tipado:

```python
from datetime import date
from typing import Annotated

import httpx
import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, ValidationError


# --- 1. Contratos de Dados (Schemas Pydantic) ---
class RegistroTransacaoIn(BaseModel):
    transacao_id: str = Field(..., min_length=3, description="Identificador único")
    cliente_id: str = Field(..., min_length=2)
    data_competencia: date
    valor: float = Field(..., gt=0.0, description="Valor estritamente positivo")
    imposto_retido: float = Field(default=0.0, ge=0.0)


class ResumoClienteOut(BaseModel):
    cliente_id: str
    quantidade_transacoes: int
    receita_liquida_total: float
    ticket_medio_liquido: float


# --- 2. Cliente de Ingestão HTTP com Validação de Contrato ---
def ingerir_transacoes_de_api(
    base_url: str, token: str, limite_por_pagina: int = 100
) -> pd.DataFrame:
    registros_validados: list[dict] = []
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/json"}

    # Uso de Client com timeout explícito e reaproveitamento de conexão TCP
    with httpx.Client(base_url=base_url, headers=headers, timeout=10.0) as client:
        pagina = 1
        while True:
            resp = client.get(
                "/v1/transacoes",
                params={"page": pagina, "limit": limite_por_pagina},
            )
            resp.raise_for_status()
            payload = resp.json()
            itens = payload.get("items", [])
            if not itens:
                break

            for item in itens:
                try:
                    modelo = RegistroTransacaoIn.model_validate(item)
                    registros_validados.append(modelo.model_dump())
                except ValidationError as err:
                    # Registra rejeição de contrato sem derrubar o pipeline inteiro
                    print(f"[REJEITADO] Item inválido na página {pagina}: {err.errors()}")

            if not payload.get("has_next", False):
                break
            pagina += 1

    return pd.DataFrame(registros_validados)


# --- 3. Serviço de Dados e Agregação com FastAPI ---
app = FastAPI(title="ITAJr Data Pipeline API", version="1.0.0")


@app.post("/analise/consolidar-clientes", response_model=list[ResumoClienteOut])
def consolidar_clientes(
    transacoes: list[RegistroTransacaoIn],
    receita_minima: Annotated[float, Query(ge=0.0)] = 0.0,
) -> list[ResumoClienteOut]:
    if not transacoes:
        raise HTTPException(status_code=400, detail="A lista de transações não pode ser vazia.")

    # Conversão de modelos Pydantic validados para DataFrame pandas
    df = pd.DataFrame([t.model_dump() for t in transacoes])
    df["receita_liquida"] = df["valor"] - df["imposto_retido"]

    resumo = (
        df.groupby("cliente_id", as_index=False)
        .agg(
            quantidade_transacoes=("transacao_id", "count"),
            receita_liquida_total=("receita_liquida", "sum"),
            ticket_medio_liquido=("receita_liquida", "mean"),
        )
        .round(2)
    )
    resumo = resumo.loc[resumo["receita_liquida_total"] >= receita_minima]

    # Substitui eventuais NaN por None antes de serializar e retorna lista de dicts
    registros_saida = resumo.where(pd.notna(resumo), None).to_dict(orient="records")
    return [ResumoClienteOut.model_validate(reg) for reg in registros_saida]
```

---

## 3. Critério de Decisão

| Requisito de Arquitetura | Abordagem Recomendada | Abordagem a Evitar e Justificativa Técnica |
| :--- | :--- | :--- |
| Consumir centenas de requisições HTTP em um pipeline de ingestão | Instanciar `httpx.Client(timeout=10.0)` (ou `requests.Session()`) em bloco `with` | Chamar `requests.get(url)` avulso dentro de um loop sem `timeout` — abre e fecha um handshake TCP/TLS novo a cada chamada e pode travar o processo indefinidamente. |
| Validar dicionários JSON externos antes de inserir no DataFrame ou banco | Modelos `pydantic.BaseModel` com restrições `Field(gt=0, ...)` e `model_validate()` | Acessar chaves diretamente (`item["valor"]`) ou confiar em `pd.DataFrame(json_list)` sem validar tipos e campos obrigatórios. |
| Definir funções de rota no FastAPI que executam cálculos pesados em pandas/NumPy (CPU-bound) ou I/O síncrono | Declarar a rota com `def nome_rota(...):` padrão | Declarar `async def nome_rota(...):` contendo código bloqueante/síncrono, pois trava o *event loop* principal do servidor ASGI e bloqueia todas as demais requisições concorrentes. |
| Retornar um `DataFrame` processado em um endpoint FastAPI | Converter para lista de registros limpos (`df.to_dict(orient="records")`) validada por um `response_model` Pydantic | Retornar o objeto `DataFrame` diretamente ou dicionários contendo `np.nan` / `np.int64` sem validação de saída. |

---

## 4. Erros Comuns

1. **Bloqueio do Event Loop Assíncrono em Rotas `async def` do FastAPI:**
   - **Falha:** Declarar um endpoint como `async def processar():` e, dentro dele, executar chamadas síncronas como `requests.get()`, `time.sleep()` ou transformações pesadas de CPU no pandas. No FastAPI, funções `async def` rodam diretamente na *main thread* do event loop; qualquer operação bloqueante congela o servidor inteiro durante sua execução.
   - **Correção:** Utilizar `async def` exclusivamente quando todo o I/O interno for não bloqueante (usando `await httpx.AsyncClient().get(...)`). Se a rota executar operações síncronas ou processamento tabular em CPU com pandas, declare-a com `def` normal para que o FastAPI a execute automaticamente em um *threadpool* separado.

2. **Falha de Serialização JSON com `NaN`, `Infinity` e Tipos Escalares do NumPy:**
   - **Falha:** Retornar diretamente um dicionário extraído do pandas contendo `float('nan')` ou `np.float64`. O padrão JSON não aceita `NaN` nem `Infinity`, causando `ValueError: Out of range float values are not JSON compliant` no momento de enviar a resposta HTTP.
   - **Correção:** Tratar valores ausentes antes da serialização convertendo-os para `None` (`df.where(pd.notna(df), None).to_dict(orient="records")`) e validar a saída por meio do `response_model` do FastAPI.

3. **Ausência de Timeout e de Tratamento de Rate Limit (HTTP 429) na Extração:**
   - **Falha:** Disparar milhares de requisições consecutivas para uma API externa sem `timeout` e sem verificar o código `429 Too Many Requests`. A API externa bloqueará o IP de origem ou deixará o socket aberto indefinidamente.
   - **Correção:** Configurar sempre `timeout` explícito no cliente HTTP e implementar retentativas com *exponential backoff* (respeitando o cabeçalho `Retry-After` quando o status for `429` ou `503`).

4. **Uso de Parâmetros de Consulta Mutáveis ou sem Limite de Paginação em Endpoints de Dados:**
   - **Falha:** Expor um endpoint `GET /registros` que retorna uma tabela inteira de milhões de linhas sem paginação ou sem teto máximo no parâmetro `limit`. Uma única requisição com `limit=10000000` esgotará a memória do servidor da API.
   - **Correção:** Exigir paginação com limites estritos validados via `Query`, por exemplo: `limit: Annotated[int, Query(ge=1, le=500)] = 100`.
