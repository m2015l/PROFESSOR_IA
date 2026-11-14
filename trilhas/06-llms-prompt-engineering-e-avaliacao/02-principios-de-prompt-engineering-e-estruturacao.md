# Aula 02 — Princípios de Prompt Engineering e Estruturação

**Fonte(s) desta aula:**
- HUYEN, Chip. *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Cap. 5 (*Prompt Engineering*, pp. 211–252).
- ALAMMAR, Jay; GROOTENDORST, Maarten. *Hands-On Large Language Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Part II — Cap. 6 (*Prompt Engineering*, pp. 167–198).
- BERRYMAN, John; ZIEGLER, Albert. *Prompt Engineering for LLMs*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Caps. 1, 3–6 e 8 (pp. 1–14, 45–146, 169–198).
- PHOENIX, James; TAYLOR, Mike. *Prompt Engineering for Generative AI*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Caps. 1 e 3 (pp. 1–40, 57–124).
- ANTHROPIC. *Prompt Engineering Overview — Claude Documentation*. URL: `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview`.

---

## 1. Problema e Definição

**Prompt Engineering** é o processo sistemático de estruturar entradas textuais e multimodais para condicionar a distribuição de probabilidade $P(Y \mid X)$ de um modelo de linguagem sem alterar seus pesos $\theta$. Como o modelo prediz tokens subsequentes que maximizam a verossimilhança em relação aos padrões de seu treinamento, a organização sintática, a posição das informações e a seleção de exemplos determinam diretamente a precisão da saída.

Phoenix e Taylor (2024) estruturam **cinco princípios operacionais** de engenharia de prompts:
1. **Fornecer Direção (*Give Direction*):** declarar objetivo, papel operacional (*role*), restrições de escopo e critérios de decisão explícitos.
2. **Especificar Formato (*Specify Format*):** definir a sintaxe exata de saída (JSON, XML, tabela Markdown).
3. **Fornecer Exemplos (*Provide Examples*):** demonstrar pares entrada-saída (*In-Context Learning*) que fixam o mapeamento esperado.
4. **Avaliar Qualidade (*Evaluate Quality*):** mensurar sistematicamente as respostas sobre um conjunto de testes representativo.
5. **Dividir o Trabalho (*Divide Labor*):** decompor tarefas complexas em chamadas encadeadas (*chaining*).

Em modelos ajustados para diálogo, a entrada é serializada por **templates de chat** (como **ChatML**, que delimita mensagens com `<|im_start|>role\nconteudo<|im_end|>`). A interface divide-se em três papéis:
- **`system`:** especifica instruções globais estáticas, regras operacionais e definições de ferramentas. Modelos treinados com **Hierarquia de Instruções (*Instruction Hierarchy*)** (Wallace et al., 2024) impõem prioridade máxima às diretrizes do `system` sobre turnos subsequentes.
- **`user`:** contém a consulta e os dados dinâmicos fornecidos pelo usuário ou recuperados em tempo de execução.
- **`assistant`:** representa as saídas do modelo. Em APIs que suportam **pré-preenchimento (*prefill*)** do turno `assistant` (como Anthropic Claude e motores locais), iniciar a mensagem com `{` ou `<analise>` força o modelo a continuar exatamente a partir daquele prefixo, suprimindo preâmbulos conversacionais.

A montagem programática de prompts distingue **conteúdo estático** (instruções e exemplos fixos) de **conteúdo dinâmico** (contexto variável por requisição). Berryman e Ziegler (2024) estabelecem quatro propriedades para fragmentos (*snippets*) de contexto: **modularidade**, **naturalidade**, **brevidade** e **inércia de tokenização (*inertness*)**. Como tokenizadores BPE não são aditivos — concatenar `"be"` ($1$ token) + `"am"` ($1$ token) produz `"beam"` ($1$ token), enquanto `"cat"` + `"tail"` produz $3$ tokens (`[c]`, `[att]`, `[ail]`) —, fragmentos dinâmicos devem iniciar com espaço ou quebra de linha padronizada para que seu custo em tokens seja invariante quando concatenados. Sob restrição de janela de contexto, aplicam-se **fragmentos elásticos (*elastic snippets*)** (versões do mesmo dado em diferentes graus de resolução) selecionados por algoritmos gulosos aditivos ou subtrativos segundo **posição**, **importância (tiers de prioridade)** e **dependências** (requisitos ou incompatibilidades mútuas).

O uso de delimitadores explícitos — especialmente **tags XML** (`<contexto>`, `<documento id="1">`, `<regras>`) recomendadas na documentação da Anthropic e cabeçalhos **Markdown** — isola instruções de dados brutos. Adicionalmente, a atenção eficaz ao longo da janela não é uniforme: experimentos de recuperação (*Lost in the Middle*, Liu et al., 2023) demonstram que a acurácia segue uma curva em U, sendo superior no início (*primacy*) e no final (*recency*) do prompt, com queda acentuada na região intermediária de contextos longos. Por isso, instruções críticas e a pergunta final devem ser posicionadas nas extremidades do documento.

Para problemas lógicos ou matemáticos, emitir a resposta diretamente no primeiro token falha porque a quantidade de computação matricial por token é fixa. Técnicas de raciocínio alocam computação em tempo de teste (*test-time compute*) gerando tokens intermediários nos quais o modelo condiciona as predições seguintes:
- **Chain-of-Thought (CoT — Wei et al., 2022; Kojima et al., 2022):** induz a geração de passos intermediários de derivação via demonstrações *few-shot* ou instrução explícita passo a passo antes do resultado.
- **Self-Consistency (Wang et al., 2022):** amostra $N$ cadeias CoT independentes (com $\tau > 0$) e seleciona a resposta final por voto majoritário.
- **Tree-of-Thought (ToT — Yao et al., 2023) e Least-to-Most:** ToT explora ramificações intermediárias com avaliação e poda; *Least-to-Most* decompõe o problema em subproblemas progressivos resolvidos em sequência.
- **Inner Monologue e Self-Critique:** confina o raciocínio em blocos demarcados (ex.: `<thinking>...</thinking>`) extraídos pela aplicação antes de exibir a resposta final, ou executa um passo subsequente de verificação contra critérios de correção.

---

## 2. Aplicação Prática

O código a seguir implementa um montador de prompt com orçamento estrito de tokens (respeitando obrigatoriedade, prioridade e inércia de tokenização), delimitação XML, posicionamento da instrução crítica ao final do contexto e extração de raciocínio oculto (`<thinking>`).

```python
from dataclasses import dataclass
import re
import tiktoken

@dataclass
class ElementoPrompt:
    id_elemento: str
    posicao: int          # Ordem estrutural no documento final
    prioridade: int       # Maior valor = maior importância
    texto: str
    obrigatorio: bool = False

def montar_prompt_com_orcamento(
    elementos: list[ElementoPrompt], max_tokens: int, codificacao: str = "cl100k_base"
) -> str:
    enc = tiktoken.get_encoding(codificacao)
    candidatos = sorted(elementos, key=lambda e: (e.obrigatorio, e.prioridade), reverse=True)
    selecionados: list[ElementoPrompt] = []
    tokens_acumulados = 0

    for item in candidatos:
        fragmento = item.texto if item.texto.startswith("\n") else "\n" + item.texto
        custo = len(enc.encode(fragmento))
        if item.obrigatorio or (tokens_acumulados + custo <= max_tokens):
            selecionados.append(item)
            tokens_acumulados += custo

    selecionados.sort(key=lambda e: e.posicao)
    return "\n".join(e.texto.strip() for e in selecionados)

def extrair_resposta_pos_raciocinio(saida_llm: str) -> dict[str, str]:
    pensamento = re.search(r"<thinking>(.*?)</thinking>", saida_llm, flags=re.DOTALL)
    resposta = re.search(r"<resposta>(.*?)</resposta>", saida_llm, flags=re.DOTALL)
    return {
        "raciocinio_interno": pensamento.group(1).strip() if pensamento else "",
        "resposta_final": resposta.group(1).strip() if resposta else saida_llm.strip(),
    }

elementos = [
    ElementoPrompt("instrucao_base", posicao=1, prioridade=100, obrigatorio=True,
                   texto="Você é um auditor financeiro. Analise estritamente os dados em <documentos>."),
    ElementoPrompt("doc_primario", posicao=2, prioridade=80,
                   texto="<documentos>\n<doc id='1'>Receita líquida Q3: R$ 14,2M. Despesa operacional: R$ 9,1M.</doc>"),
    ElementoPrompt("doc_secundario", posicao=3, prioridade=20,
                   texto="<doc id='2'>Histórico de marketing de períodos anteriores sem efeito no Q3.</doc>"),
    ElementoPrompt("fechamento_query", posicao=4, prioridade=100, obrigatorio=True,
                   texto="</documentos>\nCalcule a margem operacional do Q3. Escreva o desenvolvimento em <thinking></thinking> e o valor final em <resposta></resposta>."),
]

print(montar_prompt_com_orcamento(elementos, max_tokens=95))
```

---

## 3. Critério de Decisão

| Técnica de Prompting | Quando Utilizar | Quando Evitar (Custo / Limitação) |
| :--- | :--- | :--- |
| **Zero-Shot Estruturado (XML/Markdown)** | Tarefas padrão (resumo, tradução, extração direta) ou quando o contexto dinâmico já ocupa a maior parte da janela. | Quando a saída exige formato não padronizado ou calibração específica de fronteira de decisão. |
| **Few-Shot Prompting ($2$ a $5$ exemplos)** | Imposição de formato rigoroso, estilo específico ou tratamento de casos de borda (*edge cases*) difíceis de formalizar via regras. | Quando cada exemplo requer um documento longo (escala mal em tokens e dilui a atenção) ou sob restrição severa de latência sem *prompt caching*. |
| **Chain-of-Thought (CoT) / `<thinking>`** | Problemas matemáticos, lógicos, geração de código ou classificação com múltiplos critérios dependentes. | Extração simples ou roteamento de baixa latência, pois os tokens de raciocínio aumentam diretamente o *Time to Publish* e o custo de saída. |
| **Self-Consistency / Tree-of-Thought** | Problemas críticos de raciocínio fechado com resposta agregável por voto majoritário e orçamento computacional folgado. | Chamadas interativas síncronas de baixo custo, pois multiplica o consumo de tokens de saída pelo número de amostras $N$. |

---

## 4. Erros Comuns

1. **Induzir vieses de ancoragem e padrões espúrios de ordem em *Few-Shot Prompting*:** ordenar exemplos de forma monótona (ex.: três exemplos `POSITIVO` seguidos de um `NEGATIVO`, ou todos os casos válidos antes de um caso de erro) condiciona o modelo a repetir o padrão posicional; similarmente, exemplos cuja distribuição de classes diverge da distribuição real distorcem a probabilidade prévia assumida pelo modelo.
2. **Declarar instruções críticas apenas antes de dezenas de milhares de tokens de contexto bruto:** devido ao efeito *Lost in the Middle* e ao viés de recência, restrições de formato posicionadas apenas no início são frequentemente ignoradas após longos blocos de documentos.
3. **Formular regras apenas como restrições negativas sem fornecer estrutura positiva ou seção de descarte:** instruções como `"Não explique sua resposta"` sem definir o template exato ou um bloco separado para observações (*banishing fluff*) falham com frequência em modelos ajustados por RLHF.
4. **Acoplar prompts diretamente no código-fonte sem versionamento:** modificar strings de prompt sem registrar versão, modelo, temperatura e avaliação regressiva impede a reprodutibilidade e o diagnóstico de regressões em produção.
