# Trilha 03 — SQL, Estatística e Storytelling com Dados

## Objetivo da Trilha
Capacitar o membro da Diretoria de Análise de Dados da ITAJr a extrair, higienizar e modelar conjuntos de dados analíticos diretamente no banco de dados relacional ou colunar utilizando SQL avançado, conduzir análises exploratórias e inferenciais rigorosas (amostragem, distribuições amostrais, bootstrap, testes de hipóteses paramétricos e de permutação, dimensionamento amostral e avaliação de experimentos A/B) e comunicar recomendações técnicas de forma executiva e orientada à decisão.

## Pré-requisitos
- Conclusão da **Trilha 01 — Python e Manipulação de Dados** (`01-python-e-manipulacao-de-dados/`).
- Ambiente SQL configurado (PostgreSQL 14+ ou engine analítica compatível com ANSI SQL) e ambiente Python 3.10+ com `pandas`, `numpy`, `scipy`, `statsmodels` e `matplotlib`.

## Sequência de Aulas

1. **`01-preparacao-e-consultas-analiticas-em-sql.md`**
   Arquitetura de bancos orientados a linhas e a colunas, ordem lógica de execução de cláusulas SQL, perfilamento de distribuições e duplicatas, limpeza e conversão de tipos (`CASE`, `CAST`, `COALESCE`, `NULLIF`), pivotamento, despivotamento, `GROUPING SETS` e organização modular com CTEs (`WITH`).
2. **`02-window-functions-series-temporais-e-coortes.md`**
   Anatomia das funções de janela (`PARTITION BY`, `ORDER BY`, *frame clauses*), manipulação de datas e fusos horários, métricas de séries temporais (médias móveis, acumulados YTD, indexação a período-base, comparações YoY/MoM com `LAG` e preenchimento de lacunas com dimensão de calendário) e análise de coortes (retenção, sobrevivência, recorrência em janela fixa e LTV cumulativo).
3. **`03-analise-exploratoria-e-distribuicoes-amostrais.md`**
   Taxonomia de dados tabulares, estimadores de localização e variabilidade robustos a assimetria e valores extremos (média aparada, mediana, IQR, MAD), correlação e análise multivariada, vieses de amostragem, Teorema Central do Limite, erro padrão vs. desvio-padrão, reamostragem via *Bootstrap* e distribuições paramétricas fundamentais (Normal, t-Student, Binomial, Poisson e Exponencial).
4. **`04-testes-de-hipotese-e-analise-de-experimentos.md`**
   Desenho de experimentos controlados (A/B), métricas de sucesso primárias e *guardrail metrics*, extração SQL de variantes e conversões, testes de permutação, teste t de Welch, Qui-Quadrado e Exato de Fisher, interpretação rigorosa de *p-value*, erros Tipo I ($\alpha$) e Tipo II ($\beta$), poder estatístico, cálculo de tamanho amostral (MDE), correção para múltiplos testes, *Multi-Arm Bandits* e armadilhas operacionais.
5. **`05-visualizacao-executiva-e-storytelling-com-dados.md`**
   Separação entre análise exploratória e explanatória, definição de contexto (*Who, What, How* e *Big Idea*), seleção de representações visuais eficazes e gráficos a evitar, redução de carga cognitiva pelos princípios da Gestalt, direcionamento de atenção com atributos pré-atentivos, hierarquia visual e estruturação narrativa com lógica horizontal e vertical.

## Material Complementar e Referências
- **`referencias.md`** — Bibliografia primária detalhada e mapeamento de capítulos avançados para consulta sob demanda (análise textual e detecção de anomalias em SQL, modelagem estatística e estudos de caso de visualização).
