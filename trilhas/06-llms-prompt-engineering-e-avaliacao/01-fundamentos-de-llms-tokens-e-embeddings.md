# Aula 01 — Fundamentos de LLMs, Tokens e Embeddings

**Fonte(s) desta aula:**
- HUYEN, Chip. *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2025. Caps. 1–2 (pp. 1–112).
- ALAMMAR, Jay; GROOTENDORST, Maarten. *Hands-On Large Language Models: Language Understanding and Generation*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Part I — Caps. 1–3 (pp. 3–107).
- BERRYMAN, John; ZIEGLER, Albert. *Prompt Engineering for LLMs*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Cap. 2 (pp. 15–44).
- PHOENIX, James; TAYLOR, Mike. *Prompt Engineering for Generative AI*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. Cap. 2 (pp. 41–56).
- KARPATHY, Andrej. *[1hr Talk] Intro to Large Language Models*. YouTube, 2023. URL: `https://www.youtube.com/watch?v=zjkBMFhNj_g` (`biblioteca/_processados/youtube/yt_zjkBMFhNj_g.txt`).
- OPENAI. *OpenAI Cookbook: How to Count Tokens with Tiktoken*. URL: `https://cookbook.openai.com/`.

---

## 1. Problema e Definição

Modelos de fundação superam a necessidade de anotação manual massiva mediante aprendizado autossupervisionado (*self-supervision*), extraindo sinais de supervisão diretamente de sequências brutas de texto. Existem duas formulações principais para modelagem de linguagem:

1. **Modelos de Linguagem Mascarados (*Masked Language Models* — MLM / *Encoder-only*, ex.: BERT, RoBERTa, DeBERTa):** estimam a probabilidade condicional de um token oculto $x_t$ dado o contexto bidirecional $P(x_t \mid x_1, \dots, x_{t-1}, x_{t+1}, \dots, x_n)$. São otimizados para tarefas não generativas de representação, extração e classificação.
2. **Modelos de Linguagem Autorregressivos ou Causais (*Causal Language Models* / *Decoder-only*, ex.: GPT, Llama, Claude, Mistral, Phi):** fatorizam a probabilidade conjunta de uma sequência $(x_1, x_2, \dots, x_T)$ como o produto das probabilidades condicionais da esquerda para a direita:
   $$P(x_1, x_2, \dots, x_T) = \prod_{t=1}^{T} P(x_t \mid x_1, x_2, \dots, x_{t-1})$$

Para processamento neural, o texto passa por **tokenização**, que particiona a string em unidades discretas mapeadas para inteiros de um vocabulário fixo $V$ (tipicamente entre $32.000$ e $200.000$ entradas) operando sobre subpalavras (*subwords*) ou bytes:
- **Byte-Pair Encoding (BPE) e Byte-level BPE:** inicializa o vocabulário com caracteres ou bytes UTF-8 ($256$ valores) e funde iterativamente os pares adjacentes mais frequentes no corpus (usado em GPT-2, GPT-4 `cl100k_base` / `o200k_base`, Llama 3).
- **WordPiece:** seleciona o par adjacente que maximiza a verossimilhança do corpus segundo um modelo unigrama (usado em BERT e DistilBERT, marcando sufixos com `##`).
- **Unigram / SentencePiece:** inicializa um vocabulário amplo e remove iterativamente tokens cuja exclusão menos aumenta a perda de um modelo unigrama, tratando espaços em branco como caracteres explícitos (`\u2581`) sem depender de pré-tokenização específica de idioma.

Cada ID de token $i \in \{1, \dots, |V|\}$ é mapeado para um vetor denso $\mathbf{e}_i \in \mathbb{R}^{d_{\text{model}}}$ por uma matriz de *embeddings* $E \in \mathbb{R}^{|V| \times d_{\text{model}}}$. Enquanto *embeddings* estáticos (Word2Vec, GloVe) atribuem um único vetor fixo por palavra independentemente de polissemia, blocos Transformer geram **embeddings contextualizados**, atualizando o vetor de cada token em função do contexto. Para busca semântica e agrupamento de documentos, modelos bi-encoder (Sentence-BERT / `all-mpnet-base-v2`) são treinados com perda contrastiva (*contrastive learning*) e *pooling* sobre as saídas do codificador.

Internamente, um LLM *decoder-only* empilha $L$ blocos Transformer. Em cada bloco, a entrada $\mathbf{X} \in \mathbb{R}^{S \times d_{\text{model}}}$ passa por normalização prévia (**Pre-RMSNorm**) e **Atenção Multi-Cabeça Mascarada (*Causal Multi-Head Self-Attention*)**. Matrizes aprendidas $W_Q, W_K, W_V$ projetam consultas ($\mathbf{Q}$), chaves ($\mathbf{K}$) e valores ($\mathbf{V}$):
$$\text{Attention}(\mathbf{Q}, \mathbf{K}, \mathbf{V}) = \text{softmax}\left(\frac{\mathbf{Q}\mathbf{K}^\top + \mathbf{M}}{\sqrt{d_k}}\right)\mathbf{V}$$
onde $d_k$ é a dimensão da cabeça e $\mathbf{M}$ é a máscara triangular superior com $-\infty$ para $j > i$, impedindo acesso a tokens futuros. A posição relativa é codificada via **Rotary Position Embeddings (RoPE)**, aplicando rotações dependentes do índice posicional aos vetores $\mathbf{Q}$ e $\mathbf{K}$. Para reduzir a memória do **KV Cache** — que armazena $\mathbf{K}$ e $\mathbf{V}$ dos tokens passados para evitar recálculo quadrático $O(S^2)$ a cada passo de geração —, substitui-se a atenção multi-cabeça padrão (MHA) por **Multi-Query Attention (MQA)** (um único par $\mathbf{K}, \mathbf{V}$ compartilhado) ou **Grouped-Query Attention (GQA)** ($\mathbf{K}$ e $\mathbf{V}$ compartilhados por grupos de cabeças de consulta). Em seguida, uma rede *feedforward* com ativação **SwiGLU** processa cada posição e a projeção final (*LM head*) emite o vetor de *logits* $\mathbf{z} \in \mathbb{R}^{|V|}$.

O treinamento de um LLM compreende três estágios:
1. **Pré-treinamento (*Pretraining*):** minimização da perda de entropia cruzada na predição do próximo token sobre trilhões de tokens. Pelas leis de escala de **Chinchilla** (Hoffmann et al., 2022), para um orçamento computacional fixo em FLOPs, o número de parâmetros $N$ e os tokens de treino $D$ devem escalar proporcionalmente ($D \approx 20 N$).
2. **Ajuste Fino Supervisionado (*Supervised Fine-Tuning* — SFT):** treinamento em pares `(instrução, resposta)` curados, adaptando o modelo da continuação bruta de documento para o cumprimento de instruções.
3. **Alinhamento de Preferência (*RLHF* ou *DPO*):** no **RLHF**, comparações humanas `(prompt, resposta_vencedora, resposta_perdedora)` treinam um Modelo de Recompensa $R_\phi(x, y)$ (modelo de Bradley-Terry) e o gerador é ajustado via **PPO** com penalidade de divergência $\text{KL}$. Na **Direct Preference Optimization (DPO)**, a política é otimizada diretamente sobre os pares de preferência sem modelo de recompensa separado.

Na inferência, os *logits* $\mathbf{z}$ são convertidos em probabilidades via *softmax* com **temperatura** $\tau > 0$:
$$P(x_t = i \mid x_{<t}) = \frac{\exp(z_i / \tau)}{\sum_{j=1}^{|V|} \exp(z_j / \tau)}$$
Para $\tau \to 0$, ocorre decodificação gulosa ($\arg\max_i z_i$). Para $\tau > 0$, a amostragem estocástica é truncada por **Top-$k$** (retém os $k$ tokens mais prováveis), **Top-$p$ (*nucleus sampling*)** (retém o menor conjunto cuja probabilidade acumulada soma $p$) ou **Min-$p$** (descarta tokens com probabilidade menor que uma fração $p_{\text{base}}$ da probabilidade máxima $p_{\max}$).

---

## 2. Aplicação Prática

O código a seguir contabiliza tokens localmente com `tiktoken` para comparar a razão caracteres/token entre idiomas e código indentado, e extrai *embeddings* densos com `sentence-transformers` para cálculo de similaridade de cosseno.

```python
import numpy as np
import tiktoken
from sentence_transformers import SentenceTransformer

# 1. Tokenização BPE e eficiência entre idiomas/código (OpenAI Cookbook)
encoding = tiktoken.get_encoding("cl100k_base")
amostras = {
    "ingles": "The autoregressive model predicts the next token.",
    "portugues": "O modelo autorregressivo prediz o próximo token.",
    "python": "def somar(a: int, b: int) -> int:\n    return a + b",
}

for rotulo, texto in amostras.items():
    ids = encoding.encode(texto)
    subwords = [encoding.decode_single_token_bytes(t).decode("utf-8", errors="replace") for t in ids]
    print(f"[{rotulo}] Tokens: {len(ids)} | Chars/Token: {len(texto)/len(ids):.2f} | Subwords: {subwords}")

# 2. Embeddings contextualizados de sentença e similaridade de cosseno
modelo_emb = SentenceTransformer("sentence-transformers/all-mpnet-base-v2")
sentencas = [
    "O banco de dados relacional rejeitou a transação por violação de chave estrangeira.",
    "Erro de integridade referencial impediu o commit SQL na tabela destino.",
    "A taxa básica de juros foi mantida pelo banco central nesta quarta-feira.",
]

vetores = modelo_emb.encode(sentencas, normalize_embeddings=True)
sim = np.matmul(vetores, vetores.T)
print("\nSimilaridade (0 vs 1 - mesmo domínio):", round(float(sim[0, 1]), 4))
print("Similaridade (0 vs 2 - polissemia de 'banco'):", round(float(sim[0, 2]), 4))
```

---

## 3. Critério de Decisão

| Cenário de Engenharia | Escolha Recomendada | Justificativa Técnica |
| :--- | :--- | :--- |
| **Classificação em alto volume, extração de entidades ou busca vetorial** | Modelos **Encoder-only** (DeBERTa-v3, RoBERTa) ou Bi-Encoders (`all-mpnet-base-v2`, `text-embedding-3-small`) | Atenção bidirecional processa a sequência inteira em uma única passagem *forward*, com menor latência e menor custo computacional que modelos geradores. |
| **Geração aberta, raciocínio multi-etapas, síntese ou conversão texto-para-código** | Modelos **Decoder-only** pós-treinados com SFT + RLHF/DPO (*Instruct/Chat*) | A perda autorregressiva aliada ao ajuste de instruções permite condicionamento flexível e geração sequencial aberta. |
| **Tarefas determinísticas (extração JSON, geração de SQL, classificação)** | Decodificação gulosa: `temperature = 0` (ou $\tau \le 0.1$) | Seleciona o token de maior probabilidade marginal a cada passo, minimizando a variância sintática. |
| **Geração com diversidade controlada ou amostragem múltipla (*Best-of-N*)** | `temperature` entre $0.6$ e $0.8$ com `top_p = 0.9` ou `min_p = 0.05` (um controlador ativo por vez) | Adapta dinamicamente o suporte amostral conforme a entropia da distribuição de *logits*, cortando a cauda de baixa probabilidade. |

---

## 4. Erros Comuns

1. **Utilizar um modelo *Base* (apenas pré-treinado) esperando comportamento de assistente sem SFT:** modelos base apenas continuam documentos estatisticamente; ao receberem uma pergunta, frequentemente geram uma lista de novas perguntas em vez de respondê-la.
2. **Assumir paridade de contagem de tokens entre diferentes idiomas e formatos:** vocabulários BPE treinados majoritariamente em inglês fragmentam palavras em português, JSON indentado ou strings Base64 em mais tokens, elevando custo, latência de *prefill* e consumo da janela de contexto.
3. **Extrair a média da última camada de um modelo *Decoder-only* bruto como vetor de busca semântica:** devido à máscara causal $\mathbf{M}$, cada token atende apenas aos anteriores, gerando representações anisotrópicas inferiores às de modelos *Encoder-only* ou bi-encoders treinados com perda contrastiva.
4. **Combinar simultaneamente valores agressivos de `temperature` alta, `top_k` e `top_p`:** empilhar múltiplos truncamentos distorce a distribuição aprendida e degrada a coerência sintática em passos de alta entropia.
