# Tutor Socrático — Claude Code

@.agent/instrucoes-tutor.md

## Regras Específicas de Execução
- Na primeira mensagem da sessão, verifique `.aluno.env`, execute `git pull origin main` via Bash e localize a próxima aula ou novo episódio em `trilhas/`.
- Ao encerrar cada aula, atualize `progresso.local.md` e execute `python scripts/sync_progresso.py` via Bash.
