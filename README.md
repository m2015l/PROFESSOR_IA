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

- **Grade curricular sequencial:** 1 aula inaugural (`00`) + 7 trilhas técnicas (`01` a `07`), totalizando **33 aulas** descritas em [`trilhas/00-grade-curricular.md`](trilhas/00-grade-curricular.md).
- **Aula inaugural expositiva:** na primeira aula (`00-introducao-ao-curso/01-visao-geral-do-curso-e-trilhas.md`), você conhecerá de forma exclusivamente expositiva (sem perguntas) a estrutura do curso, todas as trilhas e conteúdos que serão estudados e o fluxo operacional das sessões.
- **Uma aula por chat (chat novo obrigatório):** cada aula deve ser feita em um **chat novo e limpo**. Ao finalizar e sincronizar uma aula, encerre a conversa atual e abra um novo chat (nova conversa no Antigravity ou nova sessão no Claude Code / Codex CLI / Gemini CLI) para fazer a aula seguinte — o tutor identificará automaticamente onde você parou e recusará iniciar duas aulas no mesmo chat para garantir que o contexto do modelo nunca se perca.
- **Ensino socrático progressivo:** nas trilhas técnicas (`01` a `07`), cada aula é conduzida uma etapa curta por vez, com perguntas de verificação ao final de cada etapa — o tutor sempre aguarda sua resposta antes de avançar; caso a resposta esteja errada ou incompleta, ele corrige/completa o raciocínio diretamente e segue para a etapa seguinte sem repetir a pergunta.
- **Sincronização automática e silenciosa:** ao iniciar cada sessão, o agente atualiza automaticamente o repositório (`git pull --ff-only origin main`) e identifica seu histórico; ao concluir cada aula, registra seu avanço de forma transparente na nuvem.

## Regras Importantes

- **Abra sempre um chat novo** para cada aula iniciada.
- **Não use autocomplete / sugestões prévias (`Tab`) na caixa de resposta:** o repositório já desativa esse recurso automaticamente no Claude Code (`.claude/settings.json`) e no Gemini CLI (`.gemini/settings.json`). Caso a sua interface ainda exiba respostas prévias em cinza na caixa de texto (ex.: apps desktop ou Codex), desative manualmente (`/config` → **Prompt suggestions** no Claude; `/settings` → **Prompt completion** no Gemini) e nunca aceite respostas automáticas com `Tab`.
- **Não altere** nenhum arquivo dentro da pasta `trilhas/`.
- **Não execute `git push`** neste repositório — o envio do seu progresso é feito exclusivamente via `python scripts/sync_progresso.py`.
- **Não compartilhe** seu `ALUNO_TOKEN` nem o arquivo `.aluno.env`.
