# Aula 01 — Do Vibe Coding à Engenharia Orientada a Especificação

> **Fonte(s) desta aula:**
> - Livro: *Beyond Vibe Coding: From Coder to AI-Era Developer* (Addy Osmani) — Parte I, Capítulos 1 e 2 (*Introduction: What Is Vibe Coding?*, *The Art of the Prompt: Communicating Effectively with AI*, pp. 3–64) e Parte II, Capítulos 3 e 4 (*The 70% Problem: AI-Assisted Workflows That Actually Work*, *Beyond the 70%: Maximizing Human Contribution*, pp. 67–96).
> - Livro: *AI-Assisted Programming* (Tom Taulli) — Capítulo 7 (*Ideas, Planning, and Requirements*, pp. 131–152) e Capítulo 8 (*Coding*, Seção *Modular Programming*, pp. 153–178).

---

## 1. Problema e Definição

A adoção de modelos de linguagem (LLMs) no desenvolvimento de software divide-se em dois modos operacionais distintos: a geração exploratória orientada apenas por conversação (*vibe coding*) e a **engenharia de software assistida por IA** (*plan-first AI-assisted engineering*).

No modo puramente exploratório (*vibe coding*), o desenvolvedor fornece descrições abertas em linguagem natural, aceita alterações sem inspecionar os *diffs* gerados e tenta corrigir falhas colando mensagens de erro repetidamente de volta no prompt. Embora essa abordagem acelere a criação de protótipos descartáveis, sua aplicação em sistemas de produção esbarra no fenômeno documentado por Addy Osmani como **o Problema dos 70%**:

1. **Assimetria entre Complexidade Acidental e Complexidade Essencial:** Modelos de linguagem resolvem rapidamente cerca de 70% da implementação inicial (código repetitivo, estruturas padrão de frameworks e integrações comuns). Entretanto, os 30% finais — tratamento de casos de borda, garantias de concorrência, contratos de dados estritos, segurança e manutenibilidade — exigem conhecimento arquitetural explícito.
2. **Padrão de Regressão em Cascata (*Two Steps Back*):** Quando o desenvolvedor solicita correções sem especificar invariantes do sistema, o modelo altera trechos adjacentes para satisfazer o erro imediato, quebrando funcionalidades previamente operacionais e introduzindo duplicação de código ou dependências conflitantes.
3. **Viés de Maioria Estatística:** O modelo gera o padrão mais frequente nos dados públicos de treinamento, que frequentemente diverge da versão atual da biblioteca utilizada no projeto ou das restrições de desempenho do sistema.

A **engenharia orientada a especificação** substitui solicitações abertas por um fluxo determinístico composto por quatro pilares:
- **Especificação Prévia (*Plan-First*):** Antes de solicitar geração de código, define-se o contrato de entrada e saída (tipos, schemas Pydantic/SQL), as restrições não funcionais (limites de memória, bibliotecas permitidas, complexidade esperada) e os critérios de aceite verificáveis.
- **Decomposição Modular:** Em vez de pedir um pipeline completo em um único prompt, o problema é particionado em funções ou módulos independentes com responsabilidade única e interfaces estritas.
- **Arquivos de Contexto Persistente no Repositório (`GEMINI.md`, `CLAUDE.md`, `AGENTS.md`):** Regras arquiteturais, convenções de nomenclatura, comandos de teste e restrições da equipe são versionados na raiz do repositório para que qualquer agente de IA carregue automaticamente os padrões do projeto no início de cada sessão.

---

## 2. Aplicação Prática

O exemplo abaixo contrasta a estrutura de um arquivo de regras de repositório (`AGENTS.md` / `CLAUDE.md` / `GEMINI.md`) e uma especificação técnica estruturada para implementação modular em um projeto de dados da ITAJr:

```markdown
# Exemplo de Arquivo de Contexto Persistente (.agent/instrucoes-projeto.md)

## Stack e Restrições Técnicas
- Linguagem: Python 3.11+. Proibido usar funções sem Type Hints explícitos.
- Manipulação tabular: pandas >= 2.1 com backend PyArrow onde aplicável.
- Validação de fronteira: Pydantic v2 (`BaseModel`, `model_validate`, `Field`).
- Proibições:
  1. Nunca utilizar `df.iterrows()` ou `df.apply(..., axis=1)` em transformações numéricas.
  2. Nunca concatenar strings para montar queries SQL; usar sempre parâmetros vinculados.
  3. Nunca alterar arquivos em `migrations/` sem aprovação explícita.

## Comandos de Verificação Obrigatória
- Testes unitários: `pytest tests/ -v --tb=short`
- Verificação de tipos: `mypy src/`
```

Abaixo, a implementação em Python resultante de uma especificação modular que exige cálculo vetorizado de anomalias de faturamento com contrato de entrada/saída explícito:

```python
from dataclasses import dataclass
import numpy as np
import pandas as pd


@dataclass(frozen=True)
class ConfigDeteccaoAnomalia:
    coluna_grupo: str
    coluna_valor: str
    limite_zscore: float = 3.0
    minimo_observacoes_grupo: int = 5


def detectar_anomalias_intragrupo(
    df: pd.DataFrame, config: ConfigDeteccaoAnomalia
) -> pd.DataFrame:
    """
    Calcula o z-score robusto (baseado em mediana e MAD) dentro de cada grupo
    e sinaliza observações que excedem config.limite_zscore.

    Pré-condições verificadas:
    - df deve conter config.coluna_grupo e config.coluna_valor.
    - Grupos com menos de config.minimo_observacoes_grupo recebem z_robusto = 0.0.
    """
    colunas_obrigatorias = {config.coluna_grupo, config.coluna_valor}
    faltantes = colunas_obrigatorias - set(df.columns)
    if faltantes:
        raise ValueError(f"Colunas obrigatórias ausentes no DataFrame: {sorted(faltantes)}")

    if config.limite_zscore <= 0:
        raise ValueError("O parâmetro limite_zscore deve ser estritamente positivo.")

    resultado = df.copy()
    valores = resultado[config.coluna_valor].astype("float64")
    agrupador = resultado.groupby(config.coluna_grupo, dropna=False)[config.coluna_valor]

    contagem_grupo = agrupador.transform("count")
    mediana_grupo = agrupador.transform("median")

    # Desvio absoluto mediano (MAD) calculado de forma vetorizada
    resultado["_desvio_abs"] = (valores - mediana_grupo).abs()
    mad_grupo = resultado.groupby(config.coluna_grupo, dropna=False)["_desvio_abs"].transform(
        "median"
    )
    resultado = resultado.drop(columns=["_desvio_abs"])

    # Fator de escala 1.4826 para consistência com o desvio-padrão normal
    denominador = mad_grupo * 1.4826
    z_calculado = np.where(
        (contagem_grupo >= config.minimo_observacoes_grupo) & (denominador > 0),
        (valores - mediana_grupo).abs() / denominador,
        0.0,
    )

    resultado["zscore_robusto"] = np.round(z_calculado, 4)
    resultado["is_anomalia"] = resultado["zscore_robusto"] >= config.limite_zscore
    return resultado
```

---

## 3. Critério de Decisão

| Contexto da Tarefa | Abordagem Recomendada | Abordagem a Evitar e Justificativa Técnica |
| :--- | :--- | :--- |
| Exploração inicial de interface visual ou script descartável de uso único | Prototipação rápida orientada a prompt (*vibe coding*) em diretório isolado fora do repositório principal | Incorporar código prototipado diretamente na branch `main` sem refatoração modular e sem cobertura de testes. |
| Desenvolvimento de módulos de pipeline de dados, APIs ou modelos para produção | Engenharia orientada a especificação: definir tipos de entrada/saída, casos de borda e invariantes antes da geração | Solicitar "crie um script que limpe e processe os dados" sem especificar o esquema das colunas, a política de nulos e a cardinalidade dos joins. |
| Padronização do comportamento da IA para todos os membros da equipe | Versionar instruções concisas em `GEMINI.md`, `CLAUDE.md` e `AGENTS.md` apontando para um protocolo único em `.agent/` | Repetir instruções de estilo e arquitetura manualmente no chat a cada nova sessão de trabalho. |
| Tarefa complexa envolvendo alteração em múltiplos subsistemas (banco, serviço, API, testes) | Dividir em etapas sequenciais verificáveis (1. Schema -> 2. Função pura -> 3. Teste unitário -> 4. Endpoint) | Pedir todas as alterações em um único prompt extenso, excedendo a capacidade de atenção efetiva do modelo e dificultando a revisão do *diff*. |

---

## 4. Erros Comuns

1. **Aceitação Cega de Alterações (*Accept All* sem Leitura de *Diff*):**
   - **Falha:** Aceitar código gerado sem revisar linha a linha as alterações produzidas. O modelo pode remover validações existentes, alterar assinaturas de funções chamadas por outros módulos ou introduzir bibliotecas não listadas nas dependências do projeto.
   - **Correção:** Inspecionar obrigatoriamente `git diff` antes de confirmar qualquer etapa e rejeitar qualquer trecho cujo funcionamento o desenvolvedor não consiga explicar integralmente.

2. **Loop Infinito de Correção por Colagem de Stack Trace:**
   - **Falha:** Quando um teste falha, copiar apenas o erro para o agente repetidas vezes sem diagnosticar a causa-raiz. Após duas ou três tentativas malsucedidas, o modelo frequentemente contorna o problema afrouxando o teste, capturando exceções genéricas (`except Exception: pass`) ou codificando valores fixos (*hardcoding*).
   - **Correção:** Se o agente falhar duas vezes seguidas na mesma correção, interrompa a geração, inspecione o estado das variáveis com depurador ou logs, identifique a falha lógica e forneça uma instrução técnica precisa sobre como corrigi-la.

3. **Arquivos de Regras (`AGENTS.md` / `CLAUDE.md` / `GEMINI.md`) Excessivamente Longos ou Contraditórios:**
   - **Falha:** Preencher o arquivo de regras da raiz com milhares de linhas de documentação genérica ou regras conflitantes. Isso consome tokens úteis da janela de contexto em todas as interações e dilui a atenção do modelo sobre as restrições críticas.
   - **Correção:** Manter o arquivo de instruções enxuto e operacional, contendo apenas comandos exatos de build/teste, arquitetura de diretórios, convenções obrigatórias de código e restrições invioláveis.

4. **Omissão de Restrições de Desempenho e Volume de Dados no Prompt:**
   - **Falha:** Solicitar uma função de cruzamento ou agregação em Python sem informar a ordem de grandeza dos dados (ex.: $10^7$ linhas). O modelo frequentemente gera uma solução correta para 10 linhas usando laços aninhados em Python puro ($O(n^2)$), que trava em produção.
   - **Correção:** Explicitar sempre na especificação o volume esperado de dados, o limite de memória e a exigência de operações vetorizadas (NumPy/pandas) ou indexadas em $O(1)$.
