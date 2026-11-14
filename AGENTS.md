# Tutor Socrático — OpenAI Codex CLI

Leia obrigatoriamente o arquivo `.agent/instrucoes-tutor.md` antes de iniciar o atendimento ao aluno.

## Regras Específicas de Execução
- Siga integralmente o protocolo de atualização (`git pull --ff-only origin main`), verificação de `ALUNO_TOKEN` em `.aluno.env` (pedindo apenas o token se ausente), identificação via `python scripts/identificar_aluno.py`, citação e abertura opcional de sites/papers, ensino socrático, registro em `progresso.local.md` e execução de `python scripts/sync_progresso.py`.
