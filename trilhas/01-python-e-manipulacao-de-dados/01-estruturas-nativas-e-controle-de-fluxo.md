# Aula 01 — Estruturas Nativas, Funções e Controle de Fluxo em Python

> **Fonte(s) desta aula:**
> - Livro: *Python for Data Analysis* (3ª Edição, Wes McKinney) — Capítulo 2 (*Python Language Basics, IPython, and Jupyter Notebooks*, pp. 17–46) e Capítulo 3 (*Built-In Data Structures, Functions, and Files*, pp. 47–82).
> - Livro: *Fluent Python* (2ª Edição, Luciano Ramalho) — Parte I, Capítulos 2, 3, 5 e 6 (*An Array of Sequences*, *Dictionaries and Sets*, *Data Class Builders*, *Object References, Mutability, and Recycling*, pp. 21–226) e Parte II, Capítulos 7 e 8 (*Functions as First-Class Objects*, *Type Hints in Functions*, pp. 231–302).

---

## 1. Problema e Definição

Antes de carregar dados em bibliotecas externas como NumPy ou pandas, qualquer pipeline de dados realiza operações de pré-processamento, configuração, filtragem de metadados e validação de registros usando objetos nativos do Python. A escolha inadequada entre as estruturas de dados embutidas ou o desconhecimento do modelo de referências de memória do Python causa degradação severa de desempenho (complexidade quadrática em buscas repetidas) e efeitos colaterais silenciosos por mutação involuntária de estado.

No modelo de dados do Python, variáveis não armazenam valores isolados em blocos fixos, mas referências para objetos alocados em memória. Essa arquitetura define duas propriedades operacionais críticas:

1. **Mutabilidade versus Imutabilidade:** Objetos imutáveis (`int`, `float`, `str`, `tuple`, `frozenset`) não permitem alteração de seu valor interno após a criação; qualquer operação de modificação gera um novo objeto em memória. Objetos mutáveis (`list`, `dict`, `set`) permitem inserção, remoção e substituição de elementos in-place mantendo o mesmo endereço de memória (`id`).
2. **Estrutura de Armazenamento e Complexidade de Busca:**
   - **`tuple`:** Sequência imutável de tamanho fixo. Atua como registro posicional heterogêneo ou lista imutável. Por ser imutável (desde que todos os seus elementos internos também sejam imutáveis), possui valor de hash (`__hash__`) e pode ser utilizada como chave de dicionário ou elemento de conjunto.
   - **`list`:** Array dinâmico de referências mutável. A anexação no final (`append`) e a remoção no final (`pop()`) têm custo amortizado $O(1)$. Entretanto, inserções ou remoções no início ou meio da lista (`insert(0, x)`, `pop(0)`, `remove(x)`) exigem deslocamento de ponteiros com custo $O(n)$, e a verificação de pertinência (`x in lista`) percorre os elementos sequencialmente em $O(n)$.
   - **`dict` e `set`:** Estruturas baseadas em tabelas hash (*hash tables*). Um `dict` armazena pares chave-valor preservando a ordem de inserção (garantido desde o Python 3.7), enquanto um `set` armazena chaves únicas sem valores associados. Em ambos, a verificação de pertinência (`k in estrutura`), inserção e remoção possuem tempo médio constante $O(1)$, além de o `set` suportar operações algébricas de conjuntos (união `|`, interseção `&`, diferença `-` e diferença simétrica `^`).

Para transformar e filtrar coleções de forma concisa, o Python oferece *list comprehensions*, *dict comprehensions*, *set comprehensions* e *generator expressions*. Enquanto uma *comprehension* materializa toda a coleção em memória imediatamente, uma *generator expression* (ou função geradora com `yield`) produz um iterador preguiçoso (*lazy evaluation*), emitindo um elemento por vez sob demanda e mantendo consumo de memória constante $O(1)$ independentemente do volume total de registros.

Por fim, funções em Python são objetos de primeira classe: podem ser atribuídas a variáveis, passadas como argumento (como no parâmetro `key` de `sorted()`) e retornadas por outras funções. Em código de produção, a assinatura de funções e estruturas de registros deve ser documentada explicitamente com anotações de tipo (*Type Hints* — PEP 484) e classes de dados (`@dataclass`), facilitando a verificação estática e a leitura do contrato de entrada e saída.

---

## 2. Aplicação Prática

O exemplo abaixo demonstra um fluxo de deduplicação, filtragem por conjunto de exclusão em $O(1)$, processamento sob demanda com geradores e agregação em dicionários tipados para registros de eventos brutos antes da conversão tabular:

```python
from collections import defaultdict
from dataclasses import dataclass
from typing import Iterable, Iterator


@dataclass(frozen=True)
class EventoTransacao:
    transacao_id: str
    cliente_id: str
    categoria: str
    valor: float


def filtrar_eventos_validos(
    registros_brutos: Iterable[dict],
    clientes_bloqueados: set[str],
    valor_minimo: float = 0.0,
) -> Iterator[EventoTransacao]:
    """
    Filtra e converte dicionários brutos em objetos imutáveis sob demanda.
    Usa um set local para deduplicar transações em tempo O(1) por item.
    """
    transacoes_vistas: set[str] = set()

    for reg in registros_brutos:
        tx_id = reg.get("id")
        cli_id = reg.get("cliente")
        valor = reg.get("valor")

        # Descarta registros incompletos ou com valor inválido
        if not tx_id or not cli_id or valor is None or valor <= valor_minimo:
            continue

        # Verificação O(1) em tabelas hash (set)
        if tx_id in transacoes_vistas or cli_id in clientes_bloqueados:
            continue

        transacoes_vistas.add(tx_id)
        yield EventoTransacao(
            transacao_id=str(tx_id),
            cliente_id=str(cli_id),
            categoria=str(reg.get("categoria", "INDEFINIDO")).strip().upper(),
            valor=float(valor),
        )


def consolidar_por_categoria(
    eventos: Iterable[EventoTransacao],
) -> dict[str, dict[str, float | int]]:
    """Agrega contagem e soma financeira por categoria."""
    acumulador: dict[str, list[float]] = defaultdict(list)

    for ev in eventos:
        acumulador[ev.categoria].append(ev.valor)

    # Dict comprehension construindo o resumo final ordenado pela receita total
    resumo = {
        cat: {
            "quantidade": len(valores),
            "total": round(sum(valores), 2),
            "ticket_medio": round(sum(valores) / len(valores), 2),
        }
        for cat, valores in sorted(
            acumulador.items(), key=lambda item: sum(item[1]), reverse=True
        )
    }
    return resumo


if __name__ == "__main__":
    lote_bruto = [
        {"id": "tx_01", "cliente": "c_10", "categoria": "cloud", "valor": 450.0},
        {"id": "tx_01", "cliente": "c_10", "categoria": "cloud", "valor": 450.0},  # Duplicado
        {"id": "tx_02", "cliente": "c_99", "categoria": "licenca", "valor": 1200.0},  # Bloqueado
        {"id": "tx_03", "cliente": "c_20", "categoria": "cloud", "valor": 850.5},
        {"id": "tx_04", "cliente": "c_30", "categoria": "dados", "valor": -10.0},  # Valor inválido
        {"id": "tx_05", "cliente": "c_40", "categoria": "dados", "valor": 2100.0},
    ]
    lista_bloqueio = {"c_99", "c_100"}

    fluxo_limpo = filtrar_eventos_validos(
        registros_brutos=lote_bruto,
        clientes_bloqueados=lista_bloqueio,
        valor_minimo=0.0,
    )
    resultado = consolidar_por_categoria(fluxo_limpo)
    print(resultado)
    # Saída:
    # {'DADOS': {'quantidade': 1, 'total': 2100.0, 'ticket_medio': 2100.0},
    #  'CLOUD': {'quantidade': 2, 'total': 1300.5, 'ticket_medio': 650.25}}
```

---

## 3. Critério de Decisão

| Cenário Operacional | Estrutura ou Recurso Recomendado | Estrutura a Evitar e Justificativa Técnica |
| :--- | :--- | :--- |
| Verificação repetida de existência (`item in colecao`) em coleções com mais de 100 elementos | `set` ou chaves de `dict` (busca por hash em $O(1)$) | `list` ou `tuple` (busca linear $O(n)$, transformando um loop de cruzamento em $O(n \times m)$). |
| Representação de registro estruturado com campos fixos e semântica clara | `@dataclass(frozen=True)` ou `typing.NamedTuple` | `tuple` posicional com mais de 3 campos acessados por índice numérico (`reg[4]`), que reduz a legibilidade e facilita erros de posição. |
| Transformação simples de sequência que cabe inteiramente na memória e será lida múltiplas vezes | *List comprehension* (`[f(x) for x in seq if cond(x)]`) | `list(map(lambda x: ..., filter(lambda x: ..., seq)))`, que adiciona sobrecarga de chamadas de função `lambda` e prejudica a leitura. |
| Leitura e filtragem sequencial de arquivos grandes (logs, JSON Lines) ou fluxos de rede | Funções geradoras (`yield`) ou *generator expressions* `(f(x) for x in stream)` | Materializar toda a entrada com `list(...)` antes de filtrar, o que pode esgotar a memória RAM disponível. |
| Acumulação de múltiplos itens sob uma mesma chave de agrupamento em Python puro | `collections.defaultdict(list)` ou `dict.setdefault(chave, []).append(val)` | Verificação manual `if chave not in d: d[chave] = []` seguida de segunda busca de hash `d[chave].append(val)`. |

---

## 4. Erros Comuns

1. **Argumentos Padrão Mutáveis em Definições de Função:**
   - **Falha:** Declarar `def adicionar_tag(tag: str, tags: list[str] = []) -> list[str]:`. Em Python, os valores padrão são avaliados uma única vez no momento em que o módulo é carregado (`def`). Chamadas subsequentes que omitirem o argumento `tags` compartilharão a mesma lista em memória, acumulando dados de execuções anteriores.
   - **Correção:** Utilizar `None` como valor sentinela imutável e instanciar o objeto mutável dentro do escopo da função:
     ```python
     def adicionar_tag(tag: str, tags: list[str] | None = None) -> list[str]:
         lista_final = [] if tags is None else list(tags)
         lista_final.append(tag)
         return lista_final
     ```

2. **Aliasing e Cópia Rasa (*Shallow Copy*) de Estruturas Aninhadas:**
   - **Falha:** Atribuir `b = a` esperando copiar uma lista ou dicionário, ou usar `b = a.copy()` / `b = a[:]` quando `a` contém listas ou dicionários internos. A atribuição simples apenas cria um segundo nome apontando para o mesmo objeto; a cópia rasa duplica apenas o contêiner externo, mantendo referências compartilhadas para os objetos internos.
   - **Correção:** Para estruturas planas, use `list(a)` ou `a.copy()`. Para estruturas aninhadas mutáveis, utilize `copy.deepcopy(a)` ou construa novos objetos imutáveis durante a transformação.

3. **Multiplicação de Sequências Contendo Objetos Mutáveis:**
   - **Falha:** Inicializar uma matriz com `grade = [[0] * 3] * 3`. O operador `*` replica a referência para a mesma lista interna três vezes; alterar `grade[0][0] = 9` modificará a primeira coluna de todas as três linhas simultaneamente.
   - **Correção:** Utilizar uma *list comprehension* para instanciar uma nova lista a cada iteração: `grade = [[0] * 3 for _ in range(3)]`.

4. **Exaustão Silenciosa de Iteradores e Geradores:**
   - **Falha:** Passar o retorno de um gerador (ou de `open()`, `zip()`, `map()`) para duas funções consecutivas, como `soma = sum(fluxo)` seguido de `media = sum(fluxo) / qtd`. Na segunda passagem, o iterador já estará exaurido e `sum(fluxo)` retornará `0` sem lançar exceção.
   - **Correção:** Se os elementos precisarem ser percorridos mais de uma vez, converta explicitamente para `list` ou `tuple` (caso caibam em memória) ou calcule todas as métricas em uma única passagem sobre o iterador.
