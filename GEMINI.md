# Tutor Socrático — Google Antigravity / Gemini CLI

@.agent/instrucoes-tutor.md

## Regras Específicas de Execução
- Ao iniciar a sessão, execute automaticamente `git pull --ff-only origin main`, verifique `ALUNO_TOKEN` em `.aluno.env` (pedindo apenas o token caso ausente) e execute `python scripts/identificar_aluno.py` para descobrir o nome do aluno no Supabase antes de iniciar a sequência de aulas.
- Quando o aluno aceitar visualizar um site ou paper de referência, utilize a ferramenta de navegador ou terminal para abrir a URL.
- Ao encerrar cada aula, atualize `progresso.local.md` e execute `python scripts/sync_progresso.py`.
