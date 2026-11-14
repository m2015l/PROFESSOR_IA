# PROFESSOR_IA — Tutor Socrático da Diretoria de Análise de Dados (ITAJr)

Repositório oficial de estudos guiados por IA para membros da Diretoria de Análise de Dados da ITAJr. O tutor conduz aulas individuais em método socrático com base nas trilhas em [`trilhas/`](trilhas/00-grade-curricular.md) e sincroniza seu progresso automaticamente com o painel da Diretoria.

## Pré-requisitos

- **Git** e **Python 3** instalados na máquina.
- Um dos agentes compatíveis: **Google Antigravity**, **Gemini CLI**, **Claude Code** ou **OpenAI Codex CLI**.
- Seu **`ALUNO_TOKEN`** individual fornecido pela Diretoria.

## Como Começar (Passo a Passo)

### 1. Clone este repositório
No terminal, execute:

```bash
git clone https://github.com/m2015l/PROFESSOR_IA.git
cd PROFESSOR_IA
```

### 2. Crie um projeto / abra a pasta no seu agente
Para que o agente carregue automaticamente o protocolo de tutoria, abra a pasta **`PROFESSOR_IA`** como projeto/workspace:

- **Google Antigravity (IDE):** abra o Antigravity, selecione **Abrir Pasta / Novo Projeto** e aponte para a pasta `PROFESSOR_IA` clonada. O agente lerá [`GEMINI.md`](GEMINI.md) e [`.agent/instrucoes-tutor.md`](.agent/instrucoes-tutor.md) automaticamente.
- **Via terminal (Claude Code, OpenAI Codex CLI ou Gemini CLI):** dentro da pasta `PROFESSOR_IA`, inicie o agente (`claude`, `codex` ou `gemini`). Os arquivos [`CLAUDE.md`](CLAUDE.md), [`AGENTS.md`](AGENTS.md) e [`GEMINI.md`](GEMINI.md) configuram o comportamento automaticamente.

### 3. Inicie a conversa informando apenas o seu token
Envie uma mensagem inicial no chat (por exemplo: *"Quero começar as aulas"*):

1. O agente vai verificar o arquivo `.aluno.env` e pedir **apenas o seu `ALUNO_TOKEN`** (não é necessário informar nome completo nem ID).
2. Ao receber o token, o agente cria o `.aluno.env` localmente e executa `python scripts/identificar_aluno.py`.
3. O script conecta-se ao servidor da Diretoria (Supabase) usando apenas o token, descobre automaticamente o seu nome e o histórico de aulas concluídas e inicia as aulas na sequência correta.

> **Configuração manual opcional:** se preferir, copie [`.aluno.env.example`](.aluno.env.example) para `.aluno.env` antes de abrir o chat e substitua apenas o valor de `ALUNO_TOKEN`.

## Como Funcionam as Aulas

- **Grade curricular sequencial:** 7 trilhas (32 aulas) descritas em [`trilhas/00-grade-curricular.md`](trilhas/00-grade-curricular.md).
- **Ensino socrático:** cada aula é dividida em blocos técnicos curtos com perguntas de verificação; você avança após demonstrar domínio do raciocínio de cada bloco.
- **Sincronização automática:** ao concluir cada aula, o agente atualiza `progresso.local.md` (arquivo local ignorado pelo Git) e executa `python scripts/sync_progresso.py` para registrar seu progresso na nuvem.
- **Atualizações contínuas:** no início de cada sessão, o agente executa `git pull --ff-only origin main` para baixar novas aulas ou trilhas publicadas pela Diretoria.

## Regras Importantes

- **Não altere** nenhum arquivo dentro da pasta `trilhas/`.
- **Não execute `git push`** neste repositório — o envio do seu progresso é feito exclusivamente via `python scripts/sync_progresso.py`.
- **Não compartilhe** seu `ALUNO_TOKEN` nem o arquivo `.aluno.env`.
