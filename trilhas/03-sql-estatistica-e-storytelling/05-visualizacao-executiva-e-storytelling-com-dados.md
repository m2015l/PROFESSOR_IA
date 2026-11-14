# 05. Visualização Executiva e Storytelling com Dados

> **Fonte(s) desta aula:**
> - **Knaflic, Cole Nussbaumer.** *Storytelling with Data: A Data Visualization Guide for Business Professionals* (1ª Edição, Wiley, 2015) — **Cap. 1** (*The Importance of Context*, pp. 19–34), **Cap. 2** (*Choosing an Effective Visual*, pp. 35–70), **Cap. 3** (*Clutter Is Your Enemy!*, pp. 71–98), **Cap. 4** (*Focus Your Audience's Attention*, pp. 99–126), **Cap. 5** (*Think Like a Designer*, pp. 127–150) e **Cap. 7** (*Lessons in Storytelling*, pp. 165–186).

---

## 1. Problema e Definição

Análises estatísticas e extrações SQL perdem utilidade prática quando comunicadas de maneira desestruturada ou visualmente sobrecarregada. O erro primário consiste em confundir **análise exploratória** com **análise explanatória**:
1. **Análise Exploratória:** Fase de investigação interna em que o analista testa dezenas de hipóteses, cruza dimensões e inspeciona distribuições para descobrir padrões relevantes.
2. **Análise Explanatória:** Fase de comunicação executiva voltada a uma audiência específica, na qual se apresenta exclusivamente a conclusão validada e a recomendação de ação, ocultando os caminhos descartados durante a exploração.

### 1.1. Contexto, *3-Minute Story* e *Big Idea*

Antes de produzir qualquer gráfico ou slide, o analista deve especificar três dimensões de contexto:
- **Quem (*Who*):** Quem é o tomador de decisão específico e qual sua familiaridade com a métrica.
- **O quê (*What*):** Qual **ação concreta** a audiência deve tomar e qual o mecanismo de entrega: apresentação ao vivo (slides enxutos, com ritmo controlado pelo apresentador) ou documento escrito autossuficiente (relatório denso em contexto textual, evitando o híbrido disfuncional *slideument*).
- **Como (*How*):** Quais evidências quantitativas sustentam o ponto central, sem omitir dados contrários relevantes.

Toda comunicação explanatória deve ser condensável em uma **História de 3 Minutos (*3-Minute Story*)** e na **Grande Ideia (*Big Idea*)** — uma única frase completa que articula: (1) o ponto de vista específico do analista, (2) o que está em risco para o negócio e (3) a recomendação explícita.

### 1.2. Carga Cognitiva, Princípios da Gestalt e Atributos Pré-Atentivos

Cada elemento visual adicionado consome **carga cognitiva** (esforço na memória de trabalho da audiência, que retém cerca de quatro blocos visuais simultaneamente). Elementos sem valor informativo constituem ruído visual (*clutter*) e reduzem a razão sinal-ruído (*data-ink ratio*).

A remoção de elementos supérfluos baseia-se nos seis **Princípios da Percepção Visual da Gestalt**:
1. **Proximidade (*Proximity*):** Objetos fisicamente próximos são percebidos como um grupo (permite substituir grades de tabela por espaçamento e posicionar rótulos diretamente ao lado das linhas).
2. **Similaridade (*Similarity*):** Elementos de mesma cor, forma ou tamanho são associados automaticamente (como rotular a série na mesma cor da curva, dispensando legendas externas).
3. **Fechamento (*Closure*):** O sistema visual percebe formas completas sem bordas explícitas, tornando desnecessárias caixas de contorno e fundos sombreados.
4. **Continuidade (*Continuity*):** O olho segue o caminho espacial mais suave, permitindo remover a linha física do eixo vertical quando os rótulos estão alinhados às barras.
5. **Enclausuramento (*Enclosure*):** Delimitar uma região com sombreamento leve agrupa elementos (ex.: separar dados realizados de projeções futuras).
6. **Conexão (*Connection*):** Linhas conectando pontos estabelecem relação de ordem temporal ou contínua.

Após eliminar o ruído, direciona-se o foco imediato (memória icônica) utilizando **atributos pré-atentivos**: cor (matiz e saturação), tamanho, espessura de linha, posição espacial (leitura em "Z" do topo esquerdo para a base direita) e negrito. A regra do contraste estratégico determina destacar no máximo $10\%$ do design visual: desenha-se a base e o contexto em tons de cinza neutro e aplica-se uma única cor de alto contraste exclusivamente na série focal.

---

## 2. Aplicação Prática

O código Python (`matplotlib`) abaixo constrói uma visualização explanatória executiva aplicando remoção de bordas e grades, hierarquia visual em cinza com destaque pré-atentivo em azul escuro, rotulagem direta por proximidade e **título de ação (*Action Title*)** com a decisão recomendada:

```python
import matplotlib.pyplot as plt
import numpy as np

meses = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
recebidos = [160, 184, 241, 149, 180, 161, 132, 202, 160, 139, 149, 177]
processados = [160, 184, 237, 148, 181, 150, 123, 156, 126, 104, 124, 140]
x = np.arange(len(meses))

fig, ax = plt.subplots(figsize=(9.5, 5.2), dpi=150)

# 1. Remoção de ruído estrutural (Princípio de Fechamento da Gestalt)
for spine in ["top", "right"]:
    ax.spines[spine].set_visible(False)
ax.spines["left"].set_color("#888888")
ax.spines["bottom"].set_color("#888888")
ax.tick_params(axis="both", colors="#555555", labelsize=10)

# 2. Contexto em cinza neutro e série focal com destaque pré-atentivo (azul marinho)
cor_contexto = "#8C8C8C"
cor_foco = "#003366"
ax.plot(x, recebidos, color=cor_contexto, linewidth=2.2)
ax.plot(x, processados, color=cor_foco, linewidth=3.2)

# 3. Marcadores e rótulos diretos apenas nos pontos de divergência (Ago a Dez)
for i in range(7, 12):
    ax.scatter(x[i], recebidos[i], color=cor_contexto, s=35, zorder=3)
    ax.scatter(x[i], processados[i], color=cor_foco, s=45, zorder=3)
    ax.text(x[i], recebidos[i] + 10, f"{recebidos[i]}", ha="center", color=cor_contexto, fontsize=9)
    ax.text(x[i], processados[i] - 18, f"{processados[i]}", ha="center", color=cor_foco, fontsize=9, fontweight="bold")

# 4. Rotulagem direta das séries (Princípio de Proximidade e Similaridade)
ax.text(11.15, recebidos[-1], "Recebidos", va="center", color=cor_contexto, fontsize=10, fontweight="bold")
ax.text(11.15, processados[-1], "Processados", va="center", color=cor_foco, fontsize=10, fontweight="bold")

# 5. Enclausuramento (Gestalt) e anotação explicativa do evento gerador
ax.axvline(x=4, color="#CCCCCC", linestyle="--", linewidth=1.2)
ax.text(4.15, 265, "Saída de 2 analistas em Maio;\ndéficit acumulado a partir de Agosto.", color="#444444", fontsize=9)

ax.set_xticks(x)
ax.set_xticklabels(meses)
ax.set_ylim(0, 300)
ax.set_xlim(-0.3, 12.6)
ax.set_ylabel("Volume mensal de chamados", color="#555555", fontsize=10, loc="top")

# 6. Hierarquia textual: Título de Ação (Action Title) + Subtítulo descritivo + Fonte
fig.suptitle(
    "Aprovar contratação de 2 analistas para recompor capacidade de atendimento",
    x=0.06, y=0.97, ha="left", fontsize=13, fontweight="bold", color="#111111"
)
ax.set_title("Volume de chamados recebidos vs. processados ao longo de 2025", loc="left", fontsize=10.5, color="#555555", pad=15)
fig.text(0.06, 0.01, "Fonte: Sistema de Chamados Interno (dados consolidados até 31/12/2025).", fontsize=8, color="#777777")

plt.tight_layout(rect=[0.04, 0.04, 0.98, 0.92])
plt.savefig("capacidade_chamados_executivo.png")
plt.close()
```

---

## 3. Critério de Decisão

| Objetivo de Comunicação | Representação Visual Recomendada | Regra de Construção |
| :--- | :--- | :--- |
| **Comunicar 1 ou 2 números isolados de alto impacto** | **Texto Simples (*Simple Text*)** em destaque tipográfico | Um gráfico com apenas duas barras ou pontos adiciona elementos estruturais sem ganho analítico; exiba o número diretamente com uma frase de apoio. |
| **Consulta de valores exatos em múltiplas unidades por públicos diversos** | **Tabela com bordas mínimas** ou **Heatmap** (saturação de cor única) | Tabelas acionam o sistema verbal (leitura sequencial). Use apenas em relatórios escritos (nunca em apresentações ao vivo) e aplique saturação monocromática para destacar extremos. |
| **Comparação de magnitudes entre categorias discretas** | **Gráfico de Barras Horizontais** (ou Verticais) | **Obrigatoriamente com linha de base em zero ($y = 0$ ou $x = 0$)**. Prefira barras horizontais quando os nomes das categorias forem longos (evita texto diagonal) e ordene as categorias por grandeza ou ordem lógica natural. |
| **Evolução contínua no tempo ou variação entre exatamente 2 períodos** | **Gráfico de Linhas** (múltiplos períodos equidistantes) ou **Slopegraph** (2 períodos) | O *slopegraph* codifica simultaneamente o valor absoluto e a taxa de variação pela inclinação do segmento entre $t_0$ e $t_1$. |
| **Decomposição de total inicial, acréscimos, reduções e saldo final** | **Gráfico de Cascata (*Waterfall Chart*)** ou **Barras Empilhadas 100%** (escalas Likert) | Em barras empilhadas comuns, apenas a série apoiada na linha de base possui referência fixa para comparação visual direta. |

---

## 4. Erros Comuns

- **Truncar o eixo de gráficos de barras em valor diferente de zero:** Como o sistema visual humano compara o comprimento físico das barras a partir da base, iniciar um eixo em $34\%$ para comparar $35\%$ com $39{,}6\%$ produz uma distorção visual de $+460\%$ para um aumento real de $+13\%$.
- **Utilizar gráficos de setores (*Pie Charts*), rosca (*Donut Charts*) ou efeitos 3D:** O olho humano tem baixa precisão para quantificar ângulos, áreas bidimensionais e comprimentos de arco, e a projeção 3D distorce proporções pela perspectiva geométrica. Substitua sempre por barras horizontais ordenadas.
- **Empregar eixo vertical secundário (*Dual / Secondary Y-Axis*):** Sobrepor duas séries com unidades distintas confunde a leitura dos eixos e induz correlações visuais artificiais conforme o ajuste das escalas. Rotule os valores diretamente nas séries ou divida em dois painéis alinhados verticalmente sobre o mesmo eixo horizontal.
- **Inacessibilidade cromática e quebra de lógica narrativa (*Horizontal e Vertical Logic*):** Combinar vermelho e verde sem diferenciação secundária (sinais $+$/$-$, negrito ou saturação) prejudica leitores daltônicos (cerca de $8\%$ dos homens). Além disso, títulos meramente descritivos ("Orçamento 2025") em vez de títulos de ação ("Gasto estimado para 2025 supera orçamento em 12%") violam a **lógica horizontal** (a sequência de títulos dos slides deve narrar contexto, conflito e recomendação) e a **lógica vertical** (todos os elementos do slide devem reforçar o respectivo título).
