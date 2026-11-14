# Aula 06 — Aplicações Interativas e Dashboards de Dados com Streamlit

> **Fonte(s) desta aula:**
> - Documentação Oficial: *Streamlit Docs — Get Started* ([https://docs.streamlit.io/get-started](https://docs.streamlit.io/get-started)).
> - Documentação Oficial: *Streamlit Docs — Development Concepts* ([https://docs.streamlit.io/develop/concepts](https://docs.streamlit.io/develop/concepts)).

---

## 1. Problema e Definição

Em projetos de análise de dados e Machine Learning, notebooks Jupyter atendem à exploração técnica individual, mas não oferecem uma interface segura, reprodutível e parametrizável para usuários de negócio. Por outro lado, construir um frontend completo em React conectado a uma API separada exige tempo de engenharia que frequentemente atrasa a entrega de ferramentas analíticas internas, simuladores de cenários e protótipos de modelos.

O **Streamlit** resolve essa lacuna permitindo construir aplicações web interativas diretamente em scripts Python padrão, utilizando uma arquitetura cliente-servidor baseada em WebSockets entre o processo Python no backend e a interface no navegador. Para operar essa ferramenta sem degradação de desempenho nem perda de dados entre interações, é indispensável compreender quatro mecanismos centrais de seu modelo de execução:

1. **Modelo de Reexecução (*Top-to-Bottom Rerun*):**
   - Ao executar `streamlit run app.py`, cada sessão de usuário no navegador dispara a leitura do script Python de cima para baixo. Sempre que o usuário altera um widget (como um filtro de data ou caixa de seleção), o Streamlit reexecuta o script inteiro do início ao fim com o novo valor retornado pelo widget. Não há necessidade de escrever rotas HTTP manuais nem callbacks separados para atualizar elementos visuais na tela.

2. **Cache em Dois Níveis (`@st.cache_data` e `@st.cache_resource`):**
   - Como o script reexecuta a cada clique, leituras de arquivos Parquet/CSV, consultas SQL e chamadas a APIs não podem rodar diretamente no corpo principal sem cache.
   - **`@st.cache_data`:** Indicado para funções que retornam objetos de dados serializáveis (`pd.DataFrame`, `np.ndarray`, `dict`, `list`, tipos primitivos). O Streamlit armazena o resultado em cache indexado pelos argumentos e pelo código da função e devolve uma cópia isolada a cada chamada, protegendo contra mutações acidentais entre sessões. Aceita o parâmetro `ttl` (tempo de expiração em segundos) para dados que atualizam periodicamente.
   - **`@st.cache_resource`:** Indicado para recursos globais não serializáveis que devem existir em instância única compartilhada entre *reruns* e usuários, como conexões de banco de dados, clientes de API autenticados e modelos de Machine Learning carregados em memória.

3. **Persistência de Estado, Formulários e Fragmentos:**
   - **`st.session_state`:** Dicionário persistente vinculado à sessão individual de cada usuário. Preserva contadores, históricos, etapas de fluxo ou resultados intermediários entre reexecuções.
   - **`st.form` e `st.form_submit_button`:** Agrupam múltiplos widgets de entrada para que o script só execute o *rerun* quando o usuário submeter o formulário inteiro, evitando recálculos parciais a cada campo preenchido.
   - **`@st.fragment`:** Isola uma função contendo widgets e saídas visuais. Quando o usuário interage apenas com widgets dentro do fragmento, o Streamlit reexecuta somente aquela função, sem reprocessar o restante do script.

4. **Estrutura Multipágina, Segredos e Testes:**
   - Aplicações maiores são organizadas com `st.Page` e `st.navigation`, mantendo um arquivo de entrada único que roteia páginas modulares. Credenciais e chaves de acesso devem residir em `.streamlit/secrets.toml` (acessíveis via `st.secrets`) ou variáveis de ambiente, jamais codificadas no script. Para validação automatizada em CI, o módulo `streamlit.testing.v1.AppTest` simula entradas de usuário e verifica elementos renderizados sem depender de navegador.

---

## 2. Aplicação Prática

O script abaixo (`app_vendas.py`) implementa um painel analítico completo utilizando `@st.cache_data` com expiração, `@st.cache_resource` para configuração compartilhada, `st.form` na barra lateral para filtragem em lote, `st.session_state` para registro de ações e `@st.fragment` para inspeção isolada de SKUs:

```python
from datetime import date
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Painel Analítico ITAJr", layout="wide")


# --- 1. Recurso global compartilhado (ex.: cliente ou motor de inferência) ---
@st.cache_resource
def obter_parametros_modelo() -> dict[str, float]:
    # Em produção, aqui seria carregado um modelo serializado ou pool de conexão
    return {"margem_alvo": 0.28, "desconto_maximo": 0.15}


# --- 2. Cache de dados serializáveis com TTL de 5 minutos ---
@st.cache_data(ttl=300)
def carregar_vendas(caminho_csv: str) -> pd.DataFrame:
    # Simulação determinística caso não haja arquivo externo
    datas = pd.date_range("2026-09-01", periods=60, freq="D")
    df = pd.DataFrame(
        {
            "data": datas,
            "categoria": ["Dados", "Automação", "BI"] * 20,
            "receita": [4200 + (i * 85) % 1900 for i in range(60)],
            "custo": [2800 + (i * 50) % 1100 for i in range(60)],
        }
    )
    df["data"] = df["data"].dt.date
    df["margem"] = (df["receita"] - df["custo"]) / df["receita"]
    return df


# --- 3. Inicialização idempotente do estado de sessão ---
if "historico_consultas" not in st.session_state:
    st.session_state["historico_consultas"] = []

parametros = obter_parametros_modelo()
df_bruto = carregar_vendas("dados/vendas.csv")

# --- 4. Barra lateral com formulário para evitar reruns intermediários ---
with st.sidebar.form("form_filtros"):
    st.header("Parâmetros de Análise")
    categorias_disponiveis = sorted(df_bruto["categoria"].unique())
    categorias_selecionadas = st.multiselect(
        "Categorias",
        options=categorias_disponiveis,
        default=categorias_disponiveis,
    )
    data_inicio = st.date_input("Data inicial", value=date(2026, 9, 1))
    data_fim = st.date_input("Data final", value=date(2026, 10, 30))
    aplicar = st.form_submit_button("Aplicar filtros")

if aplicar:
    st.session_state["historico_consultas"].append(
        f"{data_inicio} a {data_fim} ({', '.join(categorias_selecionadas)})"
    )

# Filtragem tabular padrão em pandas
mascara = (
    df_bruto["categoria"].isin(categorias_selecionadas)
    & (df_bruto["data"] >= data_inicio)
    & (df_bruto["data"] <= data_fim)
)
df_filtrado = df_bruto.loc[mascara].copy()

st.title("Monitoramento de Receita e Margem")

if df_filtrado.empty:
    st.warning("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

# --- 5. Indicadores executivos e visualização principal ---
col1, col2, col3 = st.columns(3)
receita_total = float(df_filtrado["receita"].sum())
margem_media = float(df_filtrado["margem"].mean())

col1.metric("Receita Total", f"R$ {receita_total:,.2f}")
col2.metric(
    "Margem Média",
    f"{margem_media:.1%}",
    delta=f"{(margem_media - parametros['margem_alvo']):.1%} vs alvo",
)
col3.metric("Registros Filtrados", len(df_filtrado))

serie_diaria = df_filtrado.groupby("data", as_index=True)["receita"].sum()
st.line_chart(serie_diaria)


# --- 6. Fragmento isolado: reexecuta apenas este bloco ao trocar a categoria ---
@st.fragment
def painel_detalhe_categoria(dados: pd.DataFrame) -> None:
    st.subheader("Inspeção Local por Categoria")
    cat_foco = st.selectbox(
        "Selecione uma categoria para detalhamento",
        options=sorted(dados["categoria"].unique()),
    )
    sub = dados.loc[dados["categoria"] == cat_foco]
    st.dataframe(sub, use_container_width=True, hide_index=True)


painel_detalhe_categoria(df_filtrado)

with st.expander("Histórico de filtros aplicados na sessão"):
    st.write(st.session_state["historico_consultas"])
```

Para executar localmente em ambiente de desenvolvimento:

```bash
streamlit run app_vendas.py
```

---

## 3. Critério de Decisão

| Cenário Técnico | Abordagem Recomendada | Abordagem a Evitar e Justificativa |
| :--- | :--- | :--- |
| Cachear leitura de CSV/Parquet, queries SQL ou respostas de API que retornam `DataFrame` | `@st.cache_data(ttl=...)` | `@st.cache_resource` — não cria cópia por chamada; qualquer alteração no `DataFrame` em uma sessão corrompe os dados exibidos para todos os outros usuários. |
| Cachear modelo de ML carregado, engine SQLAlchemy ou cliente de conexão | `@st.cache_resource` | `@st.cache_data` — tenta serializar o objeto via pickle, falhando em conexões abertas ou duplicando modelos pesados em memória a cada usuário. |
| Tela com 4 ou mais filtros pesados antes de consultar um banco | Agrupar widgets dentro de `st.form` com `st.form_submit_button` | Widgets soltos fora de formulário — cada alteração individual em um filtro dispara um rerun completo e uma consulta desnecessária. |
| Aplicação exige autenticação corporativa complexa, alta concorrência pública ou SLA de API REST | Backend dedicado com `FastAPI` (e frontend web separado) | Expor Streamlit como serviço principal para alto tráfego concorrente ou como substituto de APIs REST para outros sistemas. |

---

## 4. Erros Comuns

1. **Mutar Objetos Retornados por `@st.cache_resource`:**
   - **Falha:** Armazenar listas, dicionários de configuração mutáveis ou modelos em `@st.cache_resource` e modificá-los in-place durante a execução do script. Como a referência é compartilhada globalmente entre todas as sessões, a alteração afeta outros usuários simultâneos e produz condições de corrida.
   - **Correção:** Utilizar `@st.cache_resource` exclusivamente para objetos imutáveis ou recursos *thread-safe* (como conexões configuradas e modelos apenas em modo de inferência), mantendo dados mutáveis sob `@st.cache_data` ou `st.session_state`.

2. **Sobrescrever `st.session_state` Incondicionalmente no Topo do Script:**
   - **Falha:** Escrever `st.session_state["contador"] = 0` diretamente no corpo do script sem condicional. A cada clique em qualquer botão, o Streamlit reexecuta o script do início e reinicia a variável para `0`.
   - **Correção:** Inicializar sempre com guarda de existência: `if "contador" not in st.session_state: st.session_state["contador"] = 0`.

3. **Executar Ingestão ou Processamento Pesado Fora de Funções Cacheadas:**
   - **Falha:** Chamar `pd.read_parquet(...)` ou requisições `httpx` diretamente no fluxo principal sem decorador `@st.cache_data`. Qualquer interação simples de interface força o recarregamento integral dos dados.
   - **Correção:** Encapsular toda leitura externa e transformação custosa em funções puras decoradas com `@st.cache_data`, garantindo que o corpo principal execute apenas filtragem leve e renderização.

4. **Versionar `.streamlit/secrets.toml` no Repositório Git:**
   - **Falha:** Salvar senhas de banco de dados ou tokens de API em `.streamlit/secrets.toml` para uso com `st.secrets` e realizar commit desse arquivo no GitHub.
   - **Correção:** Adicionar `.streamlit/secrets.toml` ao `.gitignore` imediatamente na criação do projeto e registrar apenas um modelo sem valores sensíveis (por exemplo, `secrets.example.toml`) para orientar a equipe.
