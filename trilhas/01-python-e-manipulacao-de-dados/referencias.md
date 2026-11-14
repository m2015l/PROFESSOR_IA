# Referências e Consulta Avançada — Trilha 01

Este documento consolida as obras e documentações oficiais utilizadas nas aulas da **Trilha 01 — Python e Manipulação de Dados**, bem como os capítulos avançados das obras de referência recomendados para consulta sob demanda durante os projetos da Diretoria de Análise de Dados da ITAJr.

---

## 1. Bibliografia Principal Utilizada nas Aulas

1. **McKinney, Wes.** *Python for Data Analysis: Data Wrangling with pandas, NumPy, and Jupyter*. 3ª Edição. O'Reilly Media, 2022.
   - **Capítulos cobertos nas aulas:**
     - Capítulo 2: *Python Language Basics, IPython, and Jupyter Notebooks* (pp. 17–46) — Aula 01.
     - Capítulo 3: *Built-In Data Structures, Functions, and Files* (pp. 47–82) — Aula 01.
     - Capítulo 4: *NumPy Basics: Arrays and Vectorized Computation* (pp. 83–122) — Aula 02.
     - Capítulo 5: *Getting Started with pandas* (pp. 123–174) — Aula 02.
     - Capítulo 6: *Data Loading, Storage, and File Formats* (pp. 175–202) — Aulas 03 e 05.
     - Capítulo 7: *Data Cleaning and Preparation* (pp. 203–246) — Aula 03.
     - Capítulo 8: *Data Wrangling: Join, Combine, and Reshape* (pp. 247–280) — Aula 03.
     - Capítulo 10: *Data Aggregation and Group Operations* (pp. 319–356) — Aula 04.
     - Capítulo 11: *Time Series* (pp. 357–404) — Aula 04.

2. **Ramalho, Luciano.** *Fluent Python: Clear, Concise, and Effective Programming*. 2ª Edição. O'Reilly Media, 2022.
   - **Capítulos cobertos nas aulas:**
     - Capítulo 2: *An Array of Sequences* (pp. 21–76) — Aula 01.
     - Capítulo 3: *Dictionaries and Sets* (pp. 77–116) — Aula 01.
     - Capítulo 5: *Data Class Builders* (pp. 163–200) — Aula 01.
     - Capítulo 6: *Object References, Mutability, and Recycling* (pp. 201–226) — Aula 01.
     - Capítulo 7: *Functions as First-Class Objects* (pp. 231–252) — Aula 01.
     - Capítulo 8: *Type Hints in Functions* (pp. 253–302) — Aula 01.

3. **Ramírez, Sebastián.** *FastAPI Documentation — Tutorial / User Guide*.
   - **URL Oficial:** [https://fastapi.tiangolo.com/tutorial/](https://fastapi.tiangolo.com/tutorial/) — Aula 05.

4. **Snowflake / Streamlit.** *Streamlit Documentation — Get Started & Development Concepts*.
   - **URLs Oficiais:**
     - [https://docs.streamlit.io/get-started](https://docs.streamlit.io/get-started) — Aula 06.
     - [https://docs.streamlit.io/develop/concepts](https://docs.streamlit.io/develop/concepts) — Aula 06.

5. **Chacon, Scott; Straub, Ben.** *Pro Git*. 2ª Edição. Apress, 2014 (edição atualizada).
   - **Capítulos cobertos nas aulas:**
     - Capítulo 1: *Getting Started* (pp. 10–25) — Aula 07.
     - Capítulo 2: *Git Basics* (pp. 26–62) — Aula 07.
     - Capítulo 3: *Git Branching* (pp. 63–104) — Aula 07.
     - Capítulo 5: *Distributed Git* (pp. 126–165) — Aula 07.
     - Capítulo 6: *GitHub* (pp. 166–217) — Aula 07.

6. **GitHub.** *GitHub Docs — Collaborating with Pull Requests*.
   - **URL Oficial:** [https://docs.github.com/en/pull-requests/collaborating-with-pull-requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests) — Aula 07.

---

## 2. Capítulos Avançados para Consulta Sob Demanda

Os tópicos abaixo não exigem estudo prévio obrigatório para iniciar os projetos da Diretoria, mas devem ser consultados quando um projeto demandar otimização de baixo nível, concorrência, depuração avançada de histórico ou arquitetura de bibliotecas:

- **Em *Python for Data Analysis* (Wes McKinney):**
  - **Capítulo 13 (*Data Analysis Examples*, pp. 425–472):** Estudos de caso completos integrando limpeza, agregação e séries temporais em bases reais (Bitly, MovieLens, USDA e FEC).
  - **Apêndice A (*Advanced NumPy*, pp. 473–508):** Layout interno de memória de `ndarray` (ordem C vs Fortran/strides), regras gerais de *broadcasting* multidimensional, arrays estruturados, arquivos mapeados em memória (`memmap`) e compilação JIT com Numba.
  - **Apêndice B (*More on the IPython System*, pp. 509–534):** Depuração interativa (`%debug`), medição de tempo (`%timeit`) e profiling de desempenho (`%prun`).

- **Em *Fluent Python* (Luciano Ramalho):**
  - **Capítulo 4 (*Unicode Text Versus Bytes*, pp. 117–162):** Diagnóstico de problemas de codificação (`UnicodeEncodeError`/`UnicodeDecodeError`), normalização Unicode (`unicodedata.normalize`) e tratamento de acentuação em textos.
  - **Capítulo 9 (*Decorators and Closures*, pp. 303–340):** Escopo de variáveis, closures e memoização com `functools.cache` e `functools.lru_cache`.
  - **Parte III (*Classes and Protocols*, Capítulos 11 a 16, pp. 363–588):** Protocolos estáticos (`typing.Protocol`), herança, mixins e sobrecarga de operadores.
  - **Parte IV (*Control Flow*, Capítulos 17 a 21, pp. 589–830):** Implementação de iteradores customizados, geradores avançados, gerenciadores de contexto (`with` / `@contextmanager`) e programação concorrente com `concurrent.futures` (threads/processos) e `asyncio`.
  - **Parte V (*Metaprogramming*, Capítulos 22 a 24, pp. 831–988):** Atributos dinâmicos, descritores (`__get__`, `__set__`) e metaclasses (útil apenas na construção de frameworks ou ORMs internos).

- **Em *Pro Git* (Scott Chacon & Ben Straub):**
  - **Capítulo 4 (*Git on the Server*, pp. 105–125):** Protocolos de transferência (SSH, Smart HTTP), geração de chaves e hospedagem própria.
  - **Capítulo 7 (*Git Tools*, pp. 218–335):** Seleção avançada de revisões, *interactive staging* (`git add -p`), *stashing*, assinatura GPG, busca binária de regressões (`git bisect`), `rerere` e submódulos.
  - **Capítulo 8 (*Customizing Git*, pp. 336–366):** Atributos Git (`.gitattributes`) e *Git Hooks* (`pre-commit`, `pre-receive`) para validação automatizada.
  - **Capítulo 10 (*Git Internals*, pp. 414–452):** Objetos internos (*blobs*, *trees*, *commits*), *packfiles*, *refspec* e recuperação de dados perdidos com `git reflog`.
