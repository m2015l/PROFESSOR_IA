# Aula 07 — Controle de Versão e Colaboração com Git e GitHub

> **Fonte(s) desta aula:**
> - Livro: *Pro Git* (2ª Edição, Scott Chacon & Ben Straub) — Capítulos 1 (*Getting Started*, pp. 10–25), 2 (*Git Basics*, pp. 26–62), 3 (*Git Branching*, pp. 63–104), 5 (*Distributed Git*, pp. 126–165) e 6 (*GitHub*, pp. 166–217).
> - Documentação Oficial: *GitHub Docs — Collaborating with Pull Requests* ([https://docs.github.com/en/pull-requests/collaborating-with-pull-requests](https://docs.github.com/en/pull-requests/collaborating-with-pull-requests)).

---

## 1. Problema e Definição

Em projetos de análise e engenharia de dados, manter versões de scripts por meio de cópias manuais de pastas (`pipeline_v2.py`, `pipeline_final.py`) ou editar código diretamente na branch principal provoca perda de histórico, conflitos entre membros da equipe e incapacidade de reproduzir resultados anteriores. O **Git** resolve esse problema como um Sistema de Controle de Versão Distribuído (DVCS), enquanto o **GitHub** fornece hospedagem remota, revisão de código e integração entre colaboradores.

Diferente de sistemas baseados apenas em listas de diferenças entre arquivos, o Git armazena o histórico como uma sequência de **snapshots** completos do projeto, identificados por hashes SHA-1. Cada clone local contém o histórico integral do repositório, permitindo inspecionar diferenças, criar branches e registrar commits localmente sem latência de rede.

O ciclo de trabalho local opera sobre três estados principais:

1. **Diretório de Trabalho (*Working Directory*):** Contém os arquivos editados no disco. Arquivos novos começam como *untracked* (não rastreados); arquivos já conhecidos pelo Git alternam entre *unmodified* e *modified*.
2. **Área de Preparação (*Staging Area / Index*):** Lista explícita das alterações selecionadas via `git add` para compor o próximo snapshot. Permite dividir alterações de arquivos diferentes em commits separados e coesos.
3. **Repositório Local (`.git/`):** Armazena permanentemente os snapshots gravados pelo comando `git commit`.

Para desenvolvimento paralelo sem comprometer a estabilidade da linha principal (`main`), o Git utiliza **branches** — ponteiros móveis leves que referenciam um commit específico — e o ponteiro especial **`HEAD`**, que indica o branch ativo no diretório de trabalho. Quando dois branches divergem e precisam ser integrados, o Git executa um *merge* (avanço linear *fast-forward* quando não há divergência, ou *3-way merge* criando um commit de junção quando ambos os lados avançaram). Se duas alterações modificarem a mesma região do mesmo arquivo, o Git interrompe o merge e insere marcadores de conflito (`<<<<<<<`, `=======`, `>>>>>>>`) para resolução manual determinística.

No trabalho em equipe com o **GitHub**, a integração de código ocorre por meio de **Pull Requests (PRs)**:

- **Fluxo de Contribuição:** O desenvolvedor cria um branch de funcionalidade (*feature branch*) ou trabalha a partir de um *fork* (cópia do repositório em sua própria conta quando não possui permissão de escrita direta), publica o branch com `git push` e abre um PR comparando o *head branch* (alterações propostas) contra o *base branch* (geralmente `main`).
- **Revisão e Qualidade:** Na interface do PR, revisores inspecionam os arquivos alterados (*Files changed*), comentam linhas específicas e submetem uma decisão formal (*Comment*, *Approve* ou *Request changes*). Regras de proteção de branch podem exigir aprovações mínimas e aprovação de verificações automatizadas (*status checks*, como testes em `pytest` e linters) antes de habilitar o botão de merge.

---

## 2. Aplicação Prática

O roteiro abaixo demonstra o fluxo operacional completo para iniciar um projeto de dados Python versionado, isolar uma nova funcionalidade, sincronizar atualizações remotas e prepará-la para revisão via Pull Request no GitHub.

### Passo 1 — Configuração inicial e proteção de artefatos com `.gitignore`

```bash
# Identidade global associada aos commits (o e-mail deve corresponder ao da conta GitHub)
git config --global user.name "Seu Nome"
git config --global user.email "seu.email@itabr.org"
git config --global init.defaultBranch main
```

Crie um arquivo `.gitignore` na raiz do repositório antes do primeiro commit para impedir o rastreamento de ambientes virtuais, credenciais e bases de dados pesadas:

```gitignore
# Ambientes virtuais e cache Python
.venv/
__pycache__/
*.py[cod]

# Credenciais e segredos locais
.env
.streamlit/secrets.toml

# Dados brutos e artefatos binários grandes
data/raw/*.csv
data/raw/*.parquet
*.pkl
```

### Passo 2 — Desenvolvimento isolado em branch e commit atômico

```bash
# Clona o repositório remoto e verifica o estado inicial
git clone https://github.com/organizacao/projeto-dados.git
cd projeto-dados

# Cria e muda imediatamente para um novo branch de trabalho
git switch -c feat/validacao-vendas

# Após editar src/validacao.py e tests/test_validacao.py, inspecione o que mudou
git status
git diff

# Envia apenas os arquivos pertinentes para a staging area e valida o diff staged
git add src/validacao.py tests/test_validacao.py
git diff --staged

# Registra o snapshot com mensagem clara no imperativo
git commit -m "Adiciona validação de esquema Pydantic na ingestão de vendas"
```

### Passo 3 — Sincronização com `main` e resolução de conflitos

Antes de abrir ou concluir o Pull Request, traga atualizações recentes do repositório remoto sem sobrescrever seu trabalho diretamente:

```bash
# Baixa referências e commits do remoto sem alterar seus arquivos locais
git fetch origin

# Integra os novos commits da main remota no seu branch atual
git merge origin/main
```

Caso ocorra conflito em `src/validacao.py`, o Git exibirá `CONFLICT (content): Merge conflict in src/validacao.py` e inserirá no arquivo os blocos conflitantes:

```python
<<<<<<< HEAD
LIMITE_DESCONTO = 0.15
=======
LIMITE_DESCONTO = 0.20
>>>>>>> origin/main
```

Para resolver: edite o arquivo mantendo apenas o valor válido após alinhar com a regra de negócio, remova todos os marcadores (`<<<<<<<`, `=======`, `>>>>>>>`), execute os testes (`pytest`) e finalize o merge:

```bash
git add src/validacao.py
git commit -m "Resolve conflito de limite de desconto com origin/main"

# Publica o branch local criando o rastreamento remoto (-u)
git push -u origin feat/validacao-vendas
```

### Passo 4 — Abertura e revisão do Pull Request no GitHub

1. No GitHub, abra o Pull Request de `feat/validacao-vendas` (head) para `main` (base); utilize *Draft pull request* se desejar feedback preliminar antes de concluir os testes.
2. Descreva objetivamente o problema resolvido, os arquivos impactados e os comandos de verificação executados (como `pytest` e `streamlit run`).
3. Caso o repositório origine de um *fork*, mantenha o repositório original configurado como remoto `upstream` (`git remote add upstream <url-original>`) e sincronize periodicamente com `git fetch upstream && git merge upstream/main`.

---

## 3. Critério de Decisão

| Situação Operacional | Abordagem Recomendada | Abordagem a Evitar e Justificativa |
| :--- | :--- | :--- |
| Inspecionar mudanças remotas antes de alterar arquivos locais | `git fetch origin` seguido de `git log` / `git merge` | `git pull` cego em árvore com trabalho em andamento — aplica merge ou rebase automaticamente sem inspeção prévia. |
| Colaborar em repositório da própria equipe com acesso de escrita | Criar *feature branch* diretamente no repositório principal | Criar múltiplos *forks* internos sem necessidade — fragmenta pipelines de CI e dificulta revisão rápida entre membros. |
| Desfazer um commit já publicado em branch compartilhado (`main` ou PR revisado) | `git revert <hash-do-commit>` | `git reset --hard` seguido de `git push --force` — reescreve o histórico já baixado por outros colegas e quebra sincronizações. |
| Consolidar 15 commits de ajustes pequenos de um PR antes de integrar na `main` | *Squash and merge* na interface do GitHub | Preservar commits de depuração ("fix", "ajuste typo") na `main` — polui o log histórico e dificulta `git bisect`. |

---

## 4. Erros Comuns

1. **Commitar Credenciais, Chaves de API ou Arquivos de Dados Pesados:**
   - **Falha:** Executar `git add .` sem configurar `.gitignore`, enviando `.env`, `.streamlit/secrets.toml` ou arquivos CSV de centenas de megabytes ao GitHub. Apagar o arquivo em um commit posterior não o remove dos snapshots anteriores no histórico `.git/`.
   - **Correção:** Configurar `.gitignore` antes do primeiro commit e inspecionar `git status` antes de todo `git add`. Se uma credencial for enviada ao repositório remoto, revogue e rotacione a chave imediatamente na origem além de limpar o histórico com ferramentas dedicadas.

2. **Reescrever Histórico de Branches Compartilhados (`git rebase` + `git push --force`):**
   - **Falha:** Executar `git rebase` sobre commits que já foram enviados para um branch onde outros desenvolvedores também commitam, forçando o envio com `--force`. Isso gera commits duplicados e históricos divergentes impossíveis de conciliar automaticamente.
   - **Correção:** Utilizar `rebase` apenas em commits estritamente locais ainda não compartilhados; caso precise reenviar um branch individual de PR após correção, utilize `git push --force-with-lease` para evitar sobrescrever commits novos no remoto.

3. **Abrir Pull Requests Gigantes Misturando Múltiplas Tarefas:**
   - **Falha:** Acumular alterações de refatoração, novos gráficos, mudança de esquema SQL e correções de bug em um único branch com dezenas de arquivos modificados. Revisores perdem contexto e defeitos passam despercebidos.
   - **Correção:** Isolar cada escopo lógico em seu próprio branch pequeno e coeso, mantendo PRs focados e fáceis de auditar e reverter se necessário.

4. **Resolver Conflito de Merge Apagando Apenas os Marcadores sem Testar:**
   - **Falha:** Remover os caracteres `<<<<<<<`, `=======` e `>>>>>>>` apressadamente na interface ou editor, deixando código duplicado, imports faltantes ou lógica quebrada, e fazer commit imediato.
   - **Correção:** Ler ambos os blocos conflitantes, reconstruir a lógica coerente, rodar a suíte de testes (`pytest`) localmente e validar `git diff` antes de executar `git commit`.
