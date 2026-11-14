# Trilha 05 — Machine Learning e Sistemas em Produção

## Objetivo da Trilha

Capacitar o engenheiro de software e de dados a projetar, treinar, avaliar e operar sistemas de Machine Learning ponta a ponta em ambientes de produção. A trilha abrange o alinhamento entre objetivos de negócio e formulação matemática de problemas preditivos, engenharia e curadoria de dados de treinamento, construção de pipelines determinísticos de *feature engineering* imunes a *data leakage*, modelagem supervisionada clássica e *ensembles* de árvores, validação *out-of-sample* orientada a métricas financeiras e *slices* operacionais, implantação de serviços de inferência de baixa latência via FastAPI e monitoramento contínuo de *data distribution shifts*.

## Pré-requisitos

- **Trilha 01 — Python e Manipulação de Dados**: Domínio de estruturas vetoriais e tabulares (`NumPy` e `pandas`), tipagem estática com `Pydantic` e construção de rotas HTTP assíncronas com `FastAPI`.
- **Trilha 03 — SQL, Estatística e Storytelling com Dados**: Domínio de distribuições amostrais, testes de hipóteses, intervalos de confiança, bootstrap e análise exploratória de variáveis numéricas e categóricas.
- **Trilha 04 — Engenharia e Arquitetura de Dados**: Compreensão de arquiteturas de armazenamento analítico, processamento em lote (*batch*) versus fluxo contínuo (*streaming*), contratos de dados e idempotência em pipelines.

## Sequência de Aulas

1. **[01 — Anatomia de Projetos de ML e Curadoria de Dados de Treino](./01-anatomia-de-projetos-ml-e-curadoria-de-dados-de-treino.md)**
   Critérios para adoção de Machine Learning versus heurísticas determinísticas, requisitos de sistemas de ML em produção (confiabilidade, escalabilidade, manutenibilidade e adaptabilidade), alinhamento entre métricas de negócio e funções objetivo, desenho de esquemas de anotação (`problema -> esquema -> dados brutos -> anotações`), garantia de qualidade (*Gold Standard* e *review loops*), amostragem probabilística, rotulagem programática (*weak supervision*) e mitigação de desbalanceamento de classes.

2. **[02 — Feature Engineering e Prevenção de Data Leakage](./02-feature-engineering-e-prevencao-de-data-leakage.md)**
   Diagnóstico e tratamento de valores ausentes (MCAR, MAR e MNAR), escalonamento numérico (*Min-Max*, padronização *z-score* e transformação logarítmica), codificação de variáveis categóricas (`OneHotEncoder`, codificação $P-1$ e *Feature Hashing* para alta cardinalidade em produção), cruzamento de atributos (*feature crossing*), taxonomia de *data leakage* (vazamento temporal, vazamento de estatísticas globais, duplicatas e vazamento de grupo) e encapsulamento via `Pipeline` e `ColumnTransformer` no `scikit-learn`.

3. **[03 — Modelos Supervisionados Clássicos e Ensembles](./03-modelos-supervisionados-classicos-e-ensembles.md)**
   Modelos lineares paramétricos (Regressão Linear OLS, Equação Normal/SVD versus Descida de Gradiente, diagnóstico de resíduos, alavancagem e distância de Cook), regularização penalizada (*Ridge* $\ell_2$, *Lasso* $\ell_1$ e *Elastic Net*), classificadores probabilísticos e geométricos (Regressão Logística via máxima verossimilhança, LDA, Naive Bayes, KNN e SVM), árvores de decisão (algoritmo CART, impureza de Gini e entropia) e métodos de *Ensemble* (*Bagging*, *Random Forests* com avaliação *Out-of-Bag*, *Gradient Boosting*, XGBoost, `HistGradientBoosting` e *Stacking*).

4. **[04 — Avaliação Offline, Validação e Métricas de Negócio](./04-avaliacao-offline-validacao-e-metricas-de-negocio.md)**
   Estratégias de validação cruzada sem vazamento (`StratifiedKFold`, `GroupKFold` e `TimeSeriesSplit`), curvas de aprendizado para diagnóstico de viés e variância, hierarquia de *baselines*, métricas de regressão (RMSE, MAE, $R^2$) e classificação (matriz de confusão, precisão, *recall*, especificidade, $F_1$-score, curvas PR e ROC AUC), calibração de probabilidades (*Platt scaling* e regressão isotônica), curvas de *Lift* e matrizes de retorno financeiro esperado, testes comportamentais (perturbação, invariância e expectativa direcional) e avaliação por fatias (*slice-based evaluation* e prevenção do Paradoxo de Simpson).

5. **[05 — Deploy, Serviços de Predição e Monitoramento de Drift](./05-deploy-servicos-de-predicao-e-monitoramento-de-drift.md)**
   Arquiteturas de inferência em lote (*batch prediction*) versus *online* síncrona, prevenção de *train-serving skew* na unificação de *batch* e *streaming features*, compressão de modelos (*knowledge distillation*, *pruning* e quantização FP16/INT8), implementação de serviço de predição com `FastAPI`, `Pydantic` e gerenciamento de ciclo de vida (`lifespan`), mitigação de *degenerate feedback loops* e monitoramento estatístico de mudanças de distribuição (*covariate shift* $P(X)$, *label shift* $P(Y)$, *concept drift* $P(Y|X)$, teste Kolmogorov-Smirnov e PSI).

## Material Complementar

- **[Referências Bibliográficas e Leituras Avançadas](./referencias.md)**: Mapeamento completo das fontes primárias utilizadas na trilha e guia estruturado para consulta avançada sobre redução de dimensionalidade e aprendizado não supervisionado (PCA, *K-Means*, DBSCAN, GMM), redes neurais profundas, visão computacional, NLP, modelos generativos e aprendizado por reforço (*Hands-On Machine Learning*, Parte II, Caps. 10–19), aprendizado contínuo, testes A/B em produção, infraestrutura de MLOps (*Feature Stores* e *Model Stores*) e governança de equipes (*Designing Machine Learning Systems*, Caps. 9–11).
