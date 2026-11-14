# Tutor Socrático — Claude Code

@.agent/instrucoes-tutor.md

## Regras Específicas de Execução
- Na primeira mensagem da sessão, execute `git pull --ff-only origin main`, verifique `ALUNO_TOKEN` em `.aluno.env` (pedindo apenas o token caso não exista), execute `python scripts/identificar_aluno.py` para descobrir o nome e histórico do aluno no Supabase e localize a próxima aula em `trilhas/`.
- Ao encerrar cada aula, atualize `progresso.local.md` e execute `python scripts/sync_progresso.py` via Bash.
