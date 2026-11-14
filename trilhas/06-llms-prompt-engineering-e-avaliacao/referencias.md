# Referências Bibliográficas e Guia de Consulta — Trilha 06

Este arquivo documenta todas as fontes primárias utilizadas na construção das quatro aulas da **Trilha 06 (`06-llms-prompt-engineering-e-avaliacao`)**, detalhando o mapeamento exato de capítulos por aula e listando os capítulos de consulta avançada que extrapolam o escopo direto das aulas.

---

## 1. Obras Primárias do Acervo Local (`biblioteca/`)

1. **HUYEN, Chip.** *AI Engineering: Building Applications with Foundation Models*. 1ª Edição. Sebastopol: O'Reilly Media, 2025 (Release Dezembro 2024). ISBN 978-1-098-16630-4.
   - **Arquivo local:** `biblioteca/AIEngineering.pdf` (Extraído em: `biblioteca/_processados/pdf_aiengineering/`).
   - **Capítulos integrados nas aulas desta trilha:**
     - Capítulo 1: *Introduction to Building AI Applications with Foundation Models* (pp. 1–48) $\to$ **Aula 01**.
     - Capítulo 2: *Understanding Foundation Models* (pp. 49–112) $\to$ **Aulas 01 e 03**.
     - Capítulo 3: *Evaluation Methodology* (pp. 113–158) $\to$ **Aula 04**.
     - Capítulo 4: *Evaluate AI Systems* (pp. 159–210) $\to$ **Aula 04**.
     - Capítulo 5: *Prompt Engineering* (pp. 211–252, incluindo *Defensive Prompt Engineering*) $\to$ **Aulas 02, 03 e 04**.
     - Capítulo 7: *Finetuning* (pp. 307–362, cobrindo *When to Finetune vs. RAG*, matemática de memória, formatos numéricos FP32/FP16/BF16/TF32/INT8/INT4, quantização e PEFT/LoRA/QLoRA) $\to$ **Aula 04**.
     - Capítulo 9: *Inference Optimization* (pp. 405–448, cobrindo gargalos *compute-bound* vs. *bandwidth-bound*, *prefill* vs. *decode*, TTFT, TPOT, *goodput*, MFU, MBU, *Speculative Decoding*, KV Cache, *PagedAttention*, *Continuous Batching* e *Prompt Caching*) $\to$ **Aula 04**.
   - **Capítulos reservados para a Trilha 07:** Capítulo 6 (*RAG and Agents*, pp. 253–306) e Capítulo 10 (*AI Engineering Architecture and User Feedback*, pp. 449–494).

2. **ALAMMAR, Jay; GROOTENDORST, Maarten.** *Hands-On Large Language Models: Language Understanding and Generation*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. ISBN 978-1-098-15096-9.
   - **Arquivo local:** `biblioteca/Hands-OnLLM.pdf` (Extraído em: `biblioteca/_processados/pdf_hands-onllm/`).
   - **Capítulos integrados nas aulas desta trilha:**
     - Part I (*Understanding Language Models*, pp. 1–107): Capítulo 1 (*An Introduction to Large Language Models*, pp. 3–35), Capítulo 2 (*Tokens and Embeddings*, pp. 37–71) e Capítulo 3 (*Looking Inside Large Language Models*, pp. 73–107) $\to$ **Aula 01**.
     - Part II (*Using Pretrained Language Models*, pp. 109–286): Capítulo 4 (*Text Classification*, pp. 111–135), Capítulo 5 (*Text Clustering and Topic Modeling*, pp. 137–164), Capítulo 6 (*Prompt Engineering*, pp. 167–198) e Capítulo 7 (*Advanced Text Generation Techniques and Tools*, pp. 199–224) $\to$ **Aulas 02, 03 e 04**.
   - **Capítulos reservados para a Trilha 07:** Capítulo 8 (*Semantic Search and Retrieval-Augmented Generation*, pp. 225–258) e Capítulo 9 (*Multimodal Large Language Models*, pp. 259–286).

3. **BERRYMAN, John; ZIEGLER, Albert.** *Prompt Engineering for LLMs: The Art and Science of Building Large Language Model–Based Applications*. 1ª Edição. Sebastopol: O'Reilly Media, 2024 (Copyright 2025). ISBN 978-1-098-15615-2.
   - **Arquivo local:** `biblioteca/PromptEng.pdf` (Extraído em: `biblioteca/_processados/pdf_prompteng/`).
   - **Capítulos integrados nas aulas desta trilha (obra integralmente convertida):**
     - Part I (*Foundations*): Capítulo 1 (*Introduction to Prompt Engineering*, pp. 1–14), Capítulo 2 (*Understanding LLMs*, pp. 15–44), Capítulo 3 (*Moving to Chat*, pp. 45–64) e Capítulo 4 (*Designing LLM Applications*, pp. 65–84) $\to$ **Aulas 01 e 02**.
     - Part II (*Core Techniques*): Capítulo 5 (*Prompt Content*, pp. 87–121), Capítulo 6 (*Assembling the Prompt*, pp. 123–146) e Capítulo 7 (*Taming the Model*, pp. 147–166) $\to$ **Aulas 02, 03 e 04**.
     - Part III (*An Expert of the Craft*): Capítulo 8 (*Conversational Agency*, pp. 169–198), Capítulo 9 (*LLM Workflows*, pp. 199–221), Capítulo 10 (*Evaluating LLM Applications*, pp. 223–244) e Capítulo 11 (*Looking Ahead*, pp. 245–252) $\to$ **Aulas 02, 03 e 04**.

4. **PHOENIX, James; TAYLOR, Mike.** *Prompt Engineering for Generative AI: Future-Proof Inputs for Reliable AI Outputs*. 1ª Edição. Sebastopol: O'Reilly Media, 2024. ISBN 978-1-098-15343-4.
   - **Arquivo local:** `biblioteca/PromptEngineering.pdf` (Extraído em: `biblioteca/_processados/pdf_promptengineering/`).
   - **Capítulos integrados nas aulas desta trilha:**
     - Capítulo 1: *The Five Principles of Prompting* (pp. 1–40) $\to$ **Aula 02**.
     - Capítulo 2: *Introduction to Large Language Models for Text Generation* (pp. 41–56) $\to$ **Aula 01**.
     - Capítulo 3: *Standard Practices for Text Generation with ChatGPT* (pp. 57–124) $\to$ **Aulas 02 e 03**.
   - **Capítulos reservados para a Trilha 07:** Capítulos 4–6 (*Advanced Techniques for Text Generation with LangChain*, *Vector Databases with Pinecone*, *Autonomous Agents with AutoGPT*, pp. 125–266).

---

## 2. Fontes Complementares Web e Vídeo Integradas

5. **KARPATHY, Andrej.** *[1hr Talk] Intro to Large Language Models*. YouTube, 2023.
   - **URL:** `https://www.youtube.com/watch?v=zjkBMFhNj_g`
   - **Transcrição local processada:** `biblioteca/_processados/youtube/yt_zjkBMFhNj_g.txt` $\to$ **Aula 01** (estágios de pré-treinamento vs. ajuste fino de assistente, RLHF, escalonamento de computação em tempo de teste / *System 1 vs. System 2* e segurança/jailbreaks/prompt injection).

6. **ANTHROPIC.** *Prompt Engineering Overview — Claude Documentation*.
   - **URL:** `https://docs.anthropic.com/en/docs/build-with-claude/prompt-engineering/overview` $\to$ **Aula 02** (clareza direta, estruturação com tags XML, exemplos *multishot*, encadeamento de prompts, *extended thinking* / `<thinking>` e pré-preenchimento do turno `assistant`).

7. **OPENAI.** *OpenAI Cookbook*.
   - **URL:** `https://cookbook.openai.com/` $\to$ **Aulas 01 e 03** (contagem e manipulação de tokens com `tiktoken`, *Function Calling* e *Structured Outputs* com JSON Schema / Pydantic).

---

## 3. Consulta Avançada Fora das Aulas (Leitura Complementar Especializada)

Os capítulos abaixo pertencem às obras do acervo, mas tratam de subdomínios especializados (geração de imagens por difusão, engenharia pesada de datasets de pré-treinamento/SFT e receitas completas de treinamento contrastivo/RLHF em GPU) que ficam registrados como **consulta avançada fora das aulas**:

1. **PHOENIX, James; TAYLOR, Mike.** *Prompt Engineering for Generative AI* (O'Reilly, 2024) — **Capítulos 7 a 9 (pp. 267–366): Geração de Imagem com Modelos de Difusão**:
   - **Capítulo 7 (*Introduction to Diffusion Models for Image Generation*, pp. 267–282):** fundamentos de modelos de difusão latente, CLIP text encoders, condicionamento texto-para-imagem e espaço latente.
   - **Capítulo 8 (*Standard Practices for Image Generation with Midjourney*, pp. 283–318):** parametrização de prompts visuais, modificadores de estilo, razão de aspecto, pesos de prompt e consistência estética.
   - **Capítulo 9 (*Advanced Techniques for Image Generation with Stable Diffusion*, pp. 319–366):** *negative prompts*, ControlNet, Inpainting/Outpainting, ajuste fino com DreamBooth e LoRA para difusão.

2. **ALAMMAR, Jay; GROOTENDORST, Maarten.** *Hands-On Large Language Models* (O'Reilly, 2024) — **Part III: *Training and Fine-Tuning Language Models* (Capítulos 10 a 12, pp. 287–390): Treinamento e Fine-Tuning/RLHF Profundo**:
   - **Capítulo 10 (*Creating Text Embedding Models*, pp. 289–321):** treinamento contrastivo (*contrastive learning*), *Multiple Negatives Ranking Loss*, *Augmented SBERT* e *finetuning* de modelos bi-encoder com `sentence-transformers`.
   - **Capítulo 11 (*Fine-Tuning Representation Models for Classification*, pp. 323–353):** ajuste fino supervisionado completo de arquiteturas BERT, classificação *few-shot* eficiente com **SetFit** (*Sentence Transformer Fine-Tuning*), ajuste com congelamento parcial de camadas e avaliação em nível de token (*Named Entity Recognition* — NER).
   - **Capítulo 12 (*Fine-Tuning Generation Models*, pp. 355–389):** implementação prática passo a passo de SFT e QLoRA com `peft` e `trl` (`SFTTrainer`), formatação de datasets de instrução, fusão de adaptadores e alinhamento de preferência por **DPO (*Direct Preference Optimization*, `DPOTrainer`)** e PPO.

3. **HUYEN, Chip.** *AI Engineering* (O'Reilly, 2025) — **Capítulo 8 (*Dataset Engineering*, pp. 363–404): Engenharia e Curadoria de Datasets para Treinamento e Ajuste Fino**:
   - Curadoria de dados em escala (qualidade, cobertura, diversidade e quantidade), síntese e aumento de dados (*data synthesis*, destilação de modelos maiores, verificação de dados sintéticos), limpeza, desduplicação baseada em *hashes* (MinHash/LSH), *embeddings* e perplexidade, e filtragem de contaminação de benchmarks.
