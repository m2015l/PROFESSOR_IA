# Aula 01 — Estruturas Nativas, Funções e Controle de Fluxo em Python

> **Fonte(s) desta aula:**
> - Livro: *Python for Data Analysis* (3ª Edição, Wes McKinney) — Capítulo 2 (*Python Language Basics, IPython, and Jupyter Notebooks*, pp. 17–46) e Capítulo 3 (*Built-In Data Structures, Functions, and Files*, pp. 47–82).
> - Livro: *Fluent Python* (2ª Edição, Luciano Ramalho) — Parte I, Capítulos 2, 3, 5 e 6 (*An Array of Sequences*, *Dictionaries and Sets*, *Data Class Builders*, *Object References, Mutability, and Recycling*, pp. 21–226) e Parte II, Capítulos 7 e 8 (*Functions as First-Class Objects*, *Type Hints in Functions*, pp. 231–302).

---

## 1. Problema, Fundamentos do Zero e Exemplos Passo a Passo

Antes de trabalhar com bibliotecas especializadas de análise de dados como NumPy ou pandas, todo script de processamento lê configurações, filtra registros e organiza coleções usando os recursos básicos da própria linguagem Python. Escrever código confiável exige compreender desde o início como o Python guarda dados na memória, como o fluxo de execução toma decisões e repete tarefas, como funcionam suas estruturas nativas de coleção e como funções são definidas com segurança.

---

### 1.1. Variáveis, Referências em Memória, Tipos Escalares e Mutabilidade

Em Python, **tudo é um objeto** alocado em algum endereço da memória RAM. Uma **variável** (por exemplo, `x = 10`) não é um compartimento que guarda o valor `10` dentro de si; ela é um **nome que aponta (referencia)** para o objeto `10` na memória. Você pode inspecionar o endereço numérico de qualquer objeto usando a função nativa `id(objeto)` e o tipo dele usando `type(objeto)`.

Os tipos unitários mais básicos (**tipos escalares**) do Python são:
- **`int` (inteiro):** números sem casas decimais (`42`, `-7`, `0`).
- **`float` (ponto flutuante):** números com casas decimais (`3.14`, `-0.5`, `10.0`).
- **`str` (string / texto):** sequência de caracteres delimitada por aspas simples `'...'` ou duplas `"..."`.
- **`bool` (booleano):** representa verdadeiro ou falso, com apenas dois valores possíveis: `True` ou `False`.
- **`None`:** valor especial único que representa ausência de dado ou valor nulo. Para testar se uma variável é `None`, usa-se `variavel is None` (ou `variavel is not None`).

A arquitetura de memória do Python divide todos os tipos em duas categorias:
1. **Objetos imutáveis (`int`, `float`, `str`, `bool`, `tuple`, `frozenset`):** depois de criados, seu valor interno nunca pode ser alterado no mesmo endereço de memória. Qualquer operação que gere outro valor cria um **novo objeto** em outro endereço e redireciona a variável para ele.
2. **Objetos mutáveis (`list`, `dict`, `set`):** permitem adicionar, remover ou alterar elementos internamente (*in-place*) mantendo o **mesmo endereço de memória (`id`)**.

```python
# Exemplo 1: Tipos escalares e comportamento imutável
idade = 25
preco = 19.90
cidade = "São Paulo"
ativo = True
observacao = None

print(type(idade), type(preco), type(cidade), type(ativo))
# Saída: <class 'int'> <class 'float'> <class 'str'> <class 'bool'>

x = 10
id_antes = id(x)
x = x + 5          # Cria um novo objeto int(15) e move o nome 'x' para ele
print(id_antes == id(x))  # Saída: False (outro endereço em memória)

# Exemplo 2: Duas variáveis apontando para o mesmo objeto mutável (aliasing)
a = [10, 20]       # 'a' aponta para uma lista criada na memória
b = a              # 'b' NÃO cria outra lista; apenas passa a apontar para a mesma lista de 'a'
b.append(30)       # Altera a lista no endereço compartilhado

print(a)           # Saída: [10, 20, 30]
print(b)           # Saída: [10, 20, 30]
print(a is b)      # Saída: True (ambos apontam para exatamente o mesmo objeto)
```

---

### 1.2. Controle de Fluxo Básico (`if / elif / else`, `for`, `while`, `range`)

Ao contrário de linguagens que usam chaves `{}` para delimitar blocos de código, o Python usa **dois-pontos (`:`)** ao final do cabeçalho seguido de **indentação** (4 espaços à direita em cada linha do bloco).

- **Condicionais (`if`, `elif`, `else`):** avaliam expressões booleanas (usando comparações `==`, `!=`, `>`, `<`, `>=`, `<=` e operadores lógicos `and`, `or`, `not`) e executam apenas o primeiro bloco cuja condição for verdadeira (`True`).
- **Laço `for` e função `range()`:** percorre cada item de uma sequência ou gerador de números. A função `range(inicio, fim_exclusivo, passo)` produz inteiros sequenciais sem incluir o limite final (por exemplo, `range(0, 4)` gera `0, 1, 2, 3`; `range(3)` equivale a `range(0, 3)`).
- **Laço `while`, `break` e `continue`:** `while condicao:` repete o bloco enquanto a condição continuar verdadeira. Dentro de qualquer laço, `continue` pula imediatamente para a próxima iteração e `break` encerra o laço por completo.

```python
# Exemplo 1: Condicional if / elif / else
valor_venda = 1200.0
if valor_venda >= 2000.0:
    faixa = "ALTA"
elif valor_venda >= 500.0:
    faixa = "MEDIA"
else:
    faixa = "BAIXA"
print(faixa)  # Saída: MEDIA

# Exemplo 2: Laço for com range, continue e break
for numero in range(1, 7):  # Gera 1, 2, 3, 4, 5, 6
    if numero == 2:
        continue            # Pula o 2 e vai para o 3
    if numero == 5:
        break               # Para o laço ao chegar no 5
    print(numero)
# Saída: 1, depois 3, depois 4

# Exemplo 3: Laço while
tentativas = 0
while tentativas < 3:
    tentativas += 1         # Soma 1 ao valor atual
print(tentativas)           # Saída: 3
```

---

### 1.3. Sequências (`list` e `tuple`), Indexação, Fatiamento (*Slicing*), Cópias e Complexidade

#### Listas (`list`) e Indexação
Uma **`list`** é uma coleção **ordenada** e **mutável**, escrita entre colchetes `[item1, item2, ...]`. Como a sequência é ordenada, cada elemento ocupa uma posição numérica (**índice**), que em Python **sempre começa em `0`**:
- Índice positivo conta da esquerda para a direita: `lista[0]` é o primeiro item, `lista[1]` é o segundo.
- Índice negativo conta da direita para a esquerda: `lista[-1]` é o último item, `lista[-2]` é o penúltimo.

Principais operações de alteração *in-place* em `list`:
- `lista.append(x)`: adiciona `x` ao final da lista.
- `lista.pop()`: remove e retorna o último item (ou `lista.pop(0)` para remover do índice `0`).
- `lista.insert(i, x)`: insere `x` exatamente na posição `i`, empurrando os itens seguintes para a direita.
- `lista.remove(x)`: procura a primeira ocorrência do valor `x` e a remove.

```python
nomes = ["Ana", "Bruno", "Carla", "Diego"]
print(nomes[0])    # Saída: Ana
print(nomes[-1])   # Saída: Diego

nomes.append("Eva")
print(nomes)       # Saída: ['Ana', 'Bruno', 'Carla', 'Diego', 'Eva']

ultimo = nomes.pop()
print(ultimo, nomes)  # Saída: Eva ['Ana', 'Bruno', 'Carla', 'Diego']
```

#### Fatiamento (*Slicing*): O que significa `lista[inicio:fim]` e `lista[:]`
O **fatiamento (*slicing*)** extrai uma sublista criando uma **nova lista** com base em um intervalo de índices separados por dois-pontos (`:`):
- `lista[inicio:fim]` pega os elementos desde o índice `inicio` (incluso) até o índice `fim - 1` (o índice `fim` fica de fora).
- Se `inicio` for omitido (`lista[:fim]`), o Python começa automaticamente do índice `0`.
- Se `fim` for omitido (`lista[inicio:]`), o Python vai até o último elemento da lista.
- Se **ambos** forem omitidos (`lista[:]`), o Python percorre do índice `0` até o final inteiro e cria uma **nova lista com todos os elementos da original**.

```python
nums = [10, 20, 30, 40, 50]
print(nums[1:4])   # Índices 1, 2 e 3 -> Saída: [20, 30, 40]
print(nums[:2])    # Do início até índice 1 -> Saída: [10, 20]
print(nums[3:])    # Do índice 3 até o fim -> Saída: [40, 50]

copia = nums[:]    # Cria uma NOVA lista com todos os itens de nums
copia.append(60)
print(nums)        # Saída: [10, 20, 30, 40, 50] (original intacta!)
print(copia)       # Saída: [10, 20, 30, 40, 50, 60]
```

#### Cópia Rasa (`a.copy()`, `a[:]`) vs Cópia Profunda (`copy.deepcopy(a)`)
Tanto `b = a.copy()` quanto `b = a[:]` ou `b = list(a)` executam exatamente a mesma operação: uma **cópia rasa (*shallow copy*)**.
- Se a lista `a` contém apenas objetos imutáveis (como números ou strings), `b = a.copy()` ou `b = a[:]` torna `b` totalmente independente de `a`.
- Porém, se `a` contém **listas ou dicionários internos (estruturas aninhadas)**, a cópia rasa cria um novo contêiner externo para `b`, mas copia apenas as **referências** para as listas internas. Assim, alterar o conteúdo de uma lista interna através de `b` também altera `a`.
- Para copiar também todas as estruturas internas de forma independente, importa-se o módulo padrão `copy` e usa-se `copy.deepcopy(a)`.

```python
import copy

# Exemplo 1: Cópia rasa em lista aninhada (os elementos internos continuam compartilhados)
a = [[1, 2], [3, 4]]
b = a.copy()       # Equivalente a b = a[:]
b.append([5, 6])   # Altera apenas o contêiner externo de 'b'
b[0].append(99)    # Altera a lista interna [1, 2], que é compartilhada com 'a'

print(a)           # Saída: [[1, 2, 99], [3, 4]]  <-- 'a[0]' foi afetado!
print(b)           # Saída: [[1, 2, 99], [3, 4], [5, 6]]

# Exemplo 2: Cópia profunda isola tudo
c = [[1, 2], [3, 4]]
d = copy.deepcopy(c)
d[0].append(99)

print(c)           # Saída: [[1, 2], [3, 4]]      <-- 'c' permanece intacto
print(d)           # Saída: [[1, 2, 99], [3, 4]]
```

#### Noção de Complexidade ($O(1)$ vs $O(n)$) em `list`
Para medir o custo de uma operação conforme a quantidade $n$ de itens cresce, usa-se a notação **Big-O**:
- **$O(1)$ (tempo constante):** o tempo para executar a operação não depende do tamanho da coleção. Exemplo: `lista.append(x)` e `lista.pop()` (no final) ou ler `lista[3]` pelo índice.
- **$O(n)$ (tempo linear):** no pior caso, o Python precisa percorrer ou deslocar todos os $n$ elementos. Exemplo: `x in lista` (busca elemento por elemento do início ao fim), `lista.insert(0, x)`, `lista.pop(0)` e `lista.remove(x)`.

#### Tuplas (`tuple`) e Desempacotamento
Uma **`tuple`** é uma sequência **ordenada e imutável**, geralmente escrita entre parênteses `(item1, item2, ...)`. Depois de criada, não é possível adicionar, remover ou trocar os elementos em seus slots (tentar `tup[0] = 9` gera `TypeError`). Ela é ideal para registros curtos de tamanho fixo, como coordenadas ou pares `(uf, cidade)`.
Você pode extrair os valores de uma tupla ou lista diretamente para variáveis separadas (**desempacotamento**):

```python
registro = ("SP", "Campinas", 2026)
uf, cidade, ano = registro
print(uf, cidade, ano)  # Saída: SP Campinas 2026
```

---

### 1.4. Dicionários (`dict`), Conjuntos (`set`), `defaultdict` e Tabelas Hash (`__hash__`)

#### Dicionários (`dict`) e `defaultdict`
Um **`dict`** armazena pares **chave -> valor** entre chaves `{}`, no formato `{chave1: valor1, chave2: valor2}` (preservando a ordem de inserção desde o Python 3.7):
- `d[chave]` lê o valor da chave, mas lança `KeyError` se a chave não existir.
- `d.get(chave, padrao)` lê com segurança, devolvendo `padrao` (ou `None`) se a chave não existir.
- `d.items()` percorre todos os pares `(chave, valor)` em um laço `for`.
- Quando precisamos agrupar vários itens em listas por chave, `collections.defaultdict(list)` cria automaticamente uma lista vazia `[]` na primeira vez que uma chave nova é acessada.

```python
from collections import defaultdict

# Exemplo 1: dict básico e .get()
estoque = {"mouse": 15, "teclado": 8}
estoque["monitor"] = 4
print(estoque.get("teclado", 0))  # Saída: 8
print(estoque.get("webcam", 0))   # Saída: 0 (sem gerar KeyError)

# Exemplo 2: defaultdict(list) para agrupar valores por categoria
vendas = [("cloud", 400.0), ("dados", 200.0), ("cloud", 150.0)]
agrupado = defaultdict(list)
for categoria, valor in vendas:
    agrupado[categoria].append(valor)

print(dict(agrupado))  # Saída: {'cloud': [400.0, 150.0], 'dados': [200.0]}
```

#### Conjuntos (`set`)
Um **`set`** armazena **elementos únicos sem duplicatas e sem ordem fixa**, escrito com chaves `{a, b, c}` (para criar um conjunto vazio usa-se `set()`, pois `{}` cria um dicionário vazio). O `set` suporta operações matemáticas de conjuntos:
- União (`|`): elementos que estão em `A` ou em `B`.
- Interseção (`&`): elementos que estão em `A` e em `B` simultaneamente.
- Diferença (`-`): elementos de `A` que não estão em `B`.
- Diferença simétrica (`^`): elementos que estão em apenas um dos dois conjuntos.

```python
a = {"c1", "c2", "c3"}
b = {"c2", "c3", "c4"}
print(a | b)   # União -> {'c1', 'c2', 'c3', 'c4'}
print(a & b)   # Interseção -> {'c2', 'c3'}
print(a - b)   # Diferença -> {'c1'}
```

#### Como Funcionam Tabelas Hash (`__hash__`) e o Erro `unhashable type`
Diferente da `list`, que verifica pertinência (`x in lista`) comparando item a item em $O(n)$, o `dict` e o `set` são implementados sobre **tabelas hash** (*hash tables*), alcançando buscas, inserções e remoções em tempo médio constante **$O(1)$**:
1. Quando você insere uma chave em um `dict` ou item em um `set`, o Python chama o método interno **`__hash__`** daquele objeto (acessível via `hash(objeto)`) para calcular um número inteiro fixo chamado **código hash**.
2. Esse código hash aponta diretamente para a posição onde o dado deve ser guardado ou procurado na tabela interna, sem percorrer os demais elementos.
3. **Por que apenas objetos imutáveis são *hashables*:** Se o valor de uma chave pudesse ser modificado depois que ela entrou na tabela hash, o código hash dela mudaria e o `dict` ou `set` nunca mais conseguiria encontrá-la. Por isso, objetos mutáveis (`list`, `dict`, `set`) **não possuem `__hash__`** e geram `TypeError: unhashable type` se usados como chave de `dict` ou item de `set`.
4. **Regra para `tuple`:** Uma `tuple` só é *hashable* quando **todos os seus elementos internos também são imutáveis e *hashables***. Por exemplo: `("SP", 10)` possui `__hash__` e funciona como chave de `dict`, mas `("SP", [1, 2])` contém uma `list` mutável interna e lança **`TypeError: unhashable type: 'list'`**.

```python
print(hash("cliente_01"))       # Funciona: str é imutável (hashable)
print(hash(("SP", 10)))         # Funciona: tupla só com imutáveis

mapa_valido = {("SP", 10): "Capital"}
# mapa_invalido = {("SP", [1, 2]): "Erro"}  # TypeError: unhashable type: 'list'
```

---

### 1.5. Compreensões (*Comprehensions*) e Geradores (`yield`)

Em vez de criar uma lista vazia e preenchê-la dentro de um laço `for` com `.append()`, o Python permite escrever expressões compactas chamadas **compreensões (*comprehensions*)**:
- **List comprehension:** `[expressao for item in sequencia if condicao]` (entre colchetes `[]`).
- **Dict comprehension:** `{chave: valor for item in sequencia}` (entre chaves `{}`).
- **Set comprehension:** `{expressao for item in sequencia}` (entre chaves `{}`, sem `:`).

```python
valores = [10.0, -5.0, 25.0, 0.0, 40.0]

# Forma tradicional com for:
positivos_for = []
for v in valores:
    if v > 0:
        positivos_for.append(v * 2)

# Forma equivalente com list comprehension:
positivos_comp = [v * 2 for v in valores if v > 0]
print(positivos_comp)  # Saída: [20.0, 50.0, 80.0]

# Dict comprehension:
dobros_dict = {v: v * 2 for v in valores if v > 0}
print(dobros_dict)     # Saída: {10.0: 20.0, 25.0: 50.0, 40.0: 80.0}
```

#### Avaliação Preguiçosa (*Lazy Evaluation*), `yield` e Exaustão de Iteradores
Uma *list comprehension* calcula e guarda **todos** os resultados na memória RAM imediatamente (*eager evaluation*). Quando lidamos com arquivos muito grandes ou milhões de registros, podemos gerar um elemento por vez sob demanda (*lazy evaluation*), mantendo o consumo de memória constante $O(1)$:
- **Generator expression:** usa parênteses `(...)` no lugar de colchetes: `gen = (v * 2 for v in valores if v > 0)`.
- **Função geradora (`yield`):** em vez de `return` (que encerra a função devolvendo tudo de uma vez), usa **`yield valor`**, que entrega um item por vez e pausa a execução da função até o próximo passo do `for` ou chamada de `next()`.
- **Cuidado — Exaustão de iteradores:** Um gerador funciona como um fluxo de leitura única. Depois de percorrido uma vez (por exemplo, dentro de `sum(gen)`), ele fica vazio (*exaurido*); percorrê-lo uma segunda vez não retorna nada sem lançar erro. Se precisar ler os dados mais de uma vez, converta antes para `list(gen)` (caso caibam em memória) ou calcule tudo em uma única passagem.

```python
def gerar_positivos(numeros):
    for n in numeros:
        if n > 0:
            yield n * 10   # Entrega um valor por vez sob demanda

fluxo = gerar_positivos([1, -2, 3])
print(sum(fluxo))   # Primeira passagem: consome 10 + 30 -> Saída: 40
print(sum(fluxo))   # Segunda passagem: o gerador já esgotou -> Saída: 0
```

---

### 1.6. Funções (`def`), `lambda`, *Type Hints* e `@dataclass`

Uma **função** agrupa um bloco reutilizável de código definido com `def nome(parametros):` e devolve um resultado com `return`.

1. **Anotações de Tipo (*Type Hints* — PEP 484):**
   Permitem declarar explicitamente o tipo esperado de cada parâmetro (`param: tipo`) e o tipo do valor retornado pela função (`-> tipo_retorno`). O operador `|` indica união de tipos possíveis (por exemplo, `float | None` aceita um `float` ou `None`). O Python não bloqueia tipos errados em tempo de execução apenas pelas anotações, mas ferramentas de verificação estática e colegas de equipe passam a conhecer exatamente o contrato de entrada e saída.
2. **Funções como Objetos de Primeira Classe e `lambda`:**
   Em Python, funções podem ser guardadas em variáveis e passadas como argumento para outras funções. No parâmetro `key=` de `sorted()`, costumamos passar uma pequena função anônima de uma linha escrita com `lambda entrada: expressao_saida`.
3. **Classes de Dados (`@dataclass`):**
   Quando registros possuem vários campos nomeados, acessar posições por número em uma tupla (`reg[2]`) gera confusão. O decorador `@dataclass(frozen=True)` do módulo `dataclasses` cria automaticamente uma classe estruturada com atributos nomeados (acessíveis via `evento.valor`), comparação de igualdade e imutabilidade (`frozen=True` impede alterações após a criação e torna o objeto *hashable* se seus campos forem imutáveis).

```python
from dataclasses import dataclass


# Exemplo 1: Função com Type Hints explícitos
def calcular_total(preco: float, quantidade: int, desconto: float = 0.0) -> float:
    return (preco * quantidade) * (1.0 - desconto)


print(calcular_total(100.0, 2, 0.10))  # Saída: 180.0

# Exemplo 2: Função anônima lambda no sorted()
produtos = [("mouse", 80.0), ("monitor", 950.0), ("cabo", 25.0)]
ordenados = sorted(produtos, key=lambda item: item[1], reverse=True)
print(ordenados)  # Saída: [('monitor', 950.0), ('mouse', 80.0), ('cabo', 25.0)]


# Exemplo 3: @dataclass(frozen=True) para registros estruturados e imutáveis
@dataclass(frozen=True)
class ItemPedido:
    sku: str
    valor: float


item = ItemPedido(sku="SKU_01", valor=150.0)
print(item.sku, item.valor)  # Saída: SKU_01 150.0
```

---

## 2. Aplicação Prática

Agora que todos os blocos básicos foram apresentados, o script abaixo integra essas peças em um fluxo real de pré-processamento de eventos antes da análise tabular: usa `@dataclass(frozen=True)` para representar cada registro validado, `set[str]` para verificação $O(1)$ de duplicatas e bloqueios, uma função geradora com `yield` (`Iterator[EventoTransacao]`) para processar eventos sob demanda e `defaultdict(list)` com `sorted(..., key=lambda ...)` e *dict comprehension* para consolidar os totais por categoria.

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
   - **Falha:** Declarar `def adicionar_tag(tag: str, tags: list[str] = []) -> list[str]:`. Em Python, os valores padrão dos parâmetros são criados uma única vez no momento em que a instrução `def` é carregada na memória. Todas as chamadas seguintes que omitirem `tags` compartilharão a mesma lista, acumulando itens de execuções anteriores.
   - **Correção:** Utilizar `None` como valor padrão imutável e criar uma nova lista dentro do corpo da função:
     ```python
     def adicionar_tag(tag: str, tags: list[str] | None = None) -> list[str]:
         lista_final = [] if tags is None else list(tags)
         lista_final.append(tag)
         return lista_final
     ```

2. **Aliasing e Cópia Rasa (*Shallow Copy*) de Estruturas Aninhadas:**
   - **Falha:** Atribuir `b = a` esperando criar uma cópia independente, ou usar `b = a.copy()` / `b = a[:]` quando `a` contém listas ou dicionários internos. Como visto na Seção 1.3, `b = a` apenas cria outro nome para o mesmo objeto, enquanto `.copy()` e `[:]` duplicam somente o contêiner externo, mantendo compartilhadas as referências internas.
   - **Correção:** Para listas ou dicionários sem subníveis mutáveis, use `a.copy()`, `list(a)` ou `a[:]`. Para estruturas aninhadas mutáveis, utilize `copy.deepcopy(a)`.

3. **Multiplicação de Sequências Contendo Objetos Mutáveis:**
   - **Falha:** Inicializar uma matriz usando o operador de repetição `*`, como `grade = [[0] * 3] * 3`. A multiplicação replica a referência para a **mesma** lista interna três vezes; alterar `grade[0][0] = 9` modificará o primeiro elemento das três linhas simultaneamente.
   - **Correção:** Utilizar uma *list comprehension* para criar uma lista interna nova a cada iteração: `grade = [[0] * 3 for _ in range(3)]`.

4. **Exaustão Silenciosa de Iteradores e Geradores:**
   - **Falha:** Passar o retorno de um gerador (ou de `open()`, `zip()`, `map()`) para duas operações seguidas, como `soma = sum(fluxo)` seguido de `media = sum(fluxo) / qtd`. Na segunda leitura, o iterador já foi consumido até o fim e `sum(fluxo)` retornará `0` sem lançar exceção.
   - **Correção:** Se os elementos precisarem ser lidos mais de uma vez, converta antes para `list` ou `tuple` (caso caibam em memória) ou calcule todas as métricas em uma única passagem pelo iterador.
