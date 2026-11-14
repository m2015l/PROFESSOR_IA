# Trilha 01 — Python e Manipulação de Dados

## Objetivos da Trilha
Capacitar o membro da Diretoria de Análise de Dados da ITAJr no uso operacional de Python para engenharia e análise de dados. Ao concluir esta trilha, o aluno será capaz de estruturar coleções em memória com complexidade algorítmica adequada, vetorizar operações numéricas e tabulares com NumPy e pandas, executar rotinas completas de ingestão, limpeza e junção de dados, construir agregações e janelas temporais, integrar pipelines de dados via APIs HTTP com Pydantic e FastAPI, construir aplicações interativas de dados em Streamlit e versionar projetos de forma colaborativa com Git e GitHub.

## Pré-requisitos
- Lógica de programação básica (variáveis, condicionais e laços de repetição).
- Ambiente Python 3.10+ configurado com `numpy`, `pandas`, `pyarrow`, `httpx`, `pydantic`, `fastapi` e `streamlit`, além de Git instalado na linha de comando.

## Sequência de Aulas

1. **`01-estruturas-nativas-e-controle-de-fluxo.md`**
   - Mutabilidade, referências em memória, complexidade de busca em `list`, `tuple`, `dict` e `set`, comprehensions, geradores, funções e anotações de tipo (`Type Hints`).
2. **`02-arrays-vetorizacao-e-pandas-essencial.md`**
   - Alocação contígua em `ndarray`, operações universais (`ufuncs`), estruturas `Series` e `DataFrame`, alinhamento automático de índices e seleção determinística com `.loc` e `.iloc`.
3. **`03-ingestao-limpeza-e-transformacao-tabular.md`**
   - Leitura e escrita em CSV, JSON e Parquet, tratamento de dados ausentes (`NA`/`NaN`), remoção de duplicatas, conversão de tipos estendidos e junções relacionais (`merge`, `concat`, `pivot`, `melt`).
4. **`04-agregacoes-groupby-e-series-temporais.md`**
   - Mecânica `split-apply-combine`, agregações nomeadas (`agg`), transformações intragrupo (`transform`), indexação temporal (`DatetimeIndex`), reamostragem (`resample`) e janelas móveis (`rolling`).
5. **`05-integracao-de-dados-via-apis-e-fastapi.md`**
   - Consumo de APIs REST com paginação e tratamento de falhas, validação de contratos de dados com Pydantic e exposição de pipelines analíticos via endpoints FastAPI.
6. **`06-aplicacoes-interativas-de-dados-com-streamlit.md`**
   - Modelo de execução *top-to-bottom*, cache de dados e recursos (`@st.cache_data`, `@st.cache_resource`), estado de sessão (`st.session_state`), formulários, fragmentos (`@st.fragment`), apps multipágina e gestão de segredos (`st.secrets`).
7. **`07-controle-de-versao-e-colaboracao-com-git-e-github.md`**
   - Modelo de snapshots e três áreas do Git, `.gitignore`, criação e merge de branches, resolução de conflitos, sincronização com remotos (`fetch`, `merge`, `push`) e fluxo de Pull Requests no GitHub.

## Material de Referência e Consulta Avançada
Consulte o arquivo `referencias.md` desta pasta para acessar os links diretos das documentações oficiais (FastAPI, Streamlit e GitHub) e o mapeamento de capítulos avançados das obras de Wes McKinney (*Python for Data Analysis*), Luciano Ramalho (*Fluent Python*) e Scott Chacon & Ben Straub (*Pro Git*).
