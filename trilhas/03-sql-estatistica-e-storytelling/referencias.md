# Referências e Capítulos Avançados de Consulta — Trilha 03

## 1. Bibliografia Primária Utilizada nas Aulas

1. **Tanimura, Cathy.** *SQL for Data Analysis: Advanced Techniques for Transforming Data into Insights*. 1ª Edição. Sebastopol: O'Reilly Media, 2021. ISBN 978-1-492-08878-3.
   - **Cobertura nas aulas:** Capítulos 1, 2, 3, 4, 7 e 8 (arquitetura de armazenamento analítico, preparação e limpeza de dados, ordem lógica de processamento SQL, CTEs, séries temporais, janelas móveis, análise de coortes e estruturação de conjuntos de dados para experimentos).
2. **Bruce, Peter; Bruce, Andrew.** *Practical Statistics for Data Scientists: 50 Essential Concepts*. 1ª Edição. Sebastopol: O'Reilly Media, 2017. ISBN 978-1-491-95296-2.
   - **Cobertura nas aulas:** Capítulos 1, 2 e 3 (análise exploratória de dados estruturados, estimadores robustos de posição e dispersão, amostragem, distribuições amostrais, reamostragem *Bootstrap*, testes de permutação, testes de significância paramétricos e não paramétricos, poder estatístico e dimensionamento amostral).
3. **Knaflic, Cole Nussbaumer.** *Storytelling with Data: A Data Visualization Guide for Business Professionals*. 1ª Edição. Hoboken: Wiley, 2015. ISBN 978-1-119-00225-3.
   - **Cobertura nas aulas:** Capítulos 1, 2, 3, 4, 5 e 7 (análise exploratória vs. explanatória, definição de contexto e *Big Idea*, escolha de gráficos eficazes, eliminação de ruído visual via princípios da Gestalt, atributos pré-atentivos, acessibilidade visual e estrutura narrativa).

---

## 2. Capítulos Avançados para Consulta Sob Demanda (Não Cobertos nas Aulas)

Os capítulos abaixo pertencem às obras do acervo local processado, mas tratam de domínios especializados de consulta puntual ou foram reservados para trilhas posteriores do currículo.

### *SQL for Data Analysis* (Cathy Tanimura, 2021)
- **Capítulo 5 — *Text Analysis* (pp. 175–226):** Manipulação avançada de strings em SQL, funções de busca e extração (`position`, `strpos`, `split_part`, `regexp_matches`, `regexp_replace`), padronização textual, tokenização em nível de consulta e construção de *features* categóricas a partir de textos semiestruturados.
- **Capítulo 6 — *Anomaly Detection* (pp. 227–266):** Identificação de valores atípicos diretamente em SQL por ordenação, percentis (`percentile_cont`, `percentile_disc`), desvios-padrão (*z-score* calculado via *window functions*), detecção de anomalias de frequência, falhas de coleta e mudanças abruptas em séries temporais.
- **Capítulo 9 — *Conclusion* (pp. 317–327):** Síntese de padrões analíticos complementares em SQL: análise de funis de conversão (*Funnel Analysis*), distinção operacional entre *Churn* e *Lapse*, e análise de cesta de compras (*Market Basket Analysis* via autojunções de transações).

### *Practical Statistics for Data Scientists* (Peter Bruce & Andrew Bruce, 2017)
- **Capítulos 4 a 7 (pp. 133–296):**Reservados para a **Trilha 05 (`05-machine-learning-e-sistemas-em-producao/`)**:
  - **Cap. 4 — *Regression and Prediction* (pp. 133–180):** Regressão linear simples e múltipla, ponderação, predição vs. explicação, variáveis categóricas, multicolinearidade, heterocedasticidade, outliers, resíduos parciais e regressão polinomial/*splines*.
  - **Cap. 5 — *Classification* (pp. 181–222):** Naive Bayes, análise discriminante linear, regressão logística, métricas de classificação (matriz de confusão, precisão, *recall*, curva ROC e AUC) e tratamento de classes desbalanceadas (*undersampling*, *oversampling*, SMOTE).
  - **Cap. 6 — *Statistical Machine Learning* (pp. 223–258):** K-Nearest Neighbors (KNN), árvores de decisão, *bagging*, *Random Forest* e *Gradient Boosting* (XGBoost, regularização e hiperparâmetros).
  - **Cap. 7 — *Unsupervised Learning* (pp. 259–296):** Análise de Componentes Principais (PCA), *K-Means clustering*, agrupamento hierárquico, modelos de mistura gaussiana e escalonamento de variáveis.

### *Storytelling with Data* (Cole Nussbaumer Knaflic, 2015)
- **Capítulo 6 — *Dissecting Model Visuals* (pp. 151–164):** Análise detalhada de cinco visualizações de referência (gráfico de linhas com faixa de referência, linha com previsão sombreada, barras horizontais empilhadas em 100%, barras divergentes e barras verticais agrupadas), examinando decisões de posicionamento, tipografia, cor e hierarquia.
- **Capítulo 8 — *Pulling It All Together* (pp. 187–206):** Demonstração ponta a ponta das seis etapas do método em um único problema de precificação competitiva: definição do contexto, escolha da visualização, remoção de elementos desnecessários, aplicação de contraste pré-atentivo, ajustes de design e construção da narrativa final.
- **Capítulo 9 — *Case Studies* (pp. 207–240):** Soluções práticas para problemas recorrentes de apresentação corporativa: uso de fundos escuros, incorporação controlada de animação em apresentações ao vivo, estabelecimento de ordem lógica em categorias, estratégias para evitar gráficos de linhas sobrepostos (*spaghetti graphs*) e alternativas a gráficos de setores.
- **Capítulo 10 — *Final Thoughts* (pp. 241–256):** Diretrizes para adoção organizacional de boas práticas de visualização de dados, escolha de ferramentas e desenvolvimento contínuo de competências analíticas e comunicativas.
