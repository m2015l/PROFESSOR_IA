# Trilha 02 — Engenharia de Software Assistida por IA

## Objetivos da Trilha
Capacitar o membro da Diretoria de Análise de Dados da ITAJr a utilizar assistentes de código e agentes autônomos de engenharia de software (Google Antigravity, Claude Code e OpenAI Codex) sob rigor técnico. Ao concluir esta trilha, o aluno saberá substituir a geração exploratória desestruturada pela engenharia orientada a especificação, configurar arquivos de contexto determinísticos (`GEMINI.md`, `CLAUDE.md`, `AGENTS.md`), operar fluxos de trabalho síncronos (IDE/CLI) e assíncronos (background sandboxes), e auditar segurança, testes automatizados e manutenibilidade em código gerado por modelos de linguagem.

## Pré-requisitos
- Conclusão da **Trilha 01 (`01-python-e-manipulacao-de-dados/`)**.
- Domínio básico de Git (`branch`, `diff`, `commit`, `pull request`) e execução de testes com `pytest`.

## Sequência de Aulas

1. **`01-do-vibe-coding-a-engenharia-orientada-a-especificacao.md`**
   - Diferença operacional entre geração exploratória (*vibe coding*) e engenharia assistida por IA (*plan-first*), o problema dos 70% de completude, decomposição modular de tarefas e estruturação de arquivos de regras de repositório (`GEMINI.md`, `CLAUDE.md`, `AGENTS.md`).
2. **`02-fluxo-operacional-com-agentes-de-codigo-cli-e-ide.md`**
   - Arquitetura de agentes de código interativos e em segundo plano (*plan-execute-verify-report*), operação prática no Google Antigravity, Claude Code e OpenAI Codex, higiene de janela de contexto e isolamento de ambientes de execução.
3. **`03-revisao-critica-testes-automatizados-e-seguranca-em-codigo-gerado.md`**
   - Auditoria de código gerado por IA, mitigação de vulnerabilidades comuns (SQL Injection, credenciais expostas, falhas de autorização, dependências obsoletas), suítes de testes determinísticos com `pytest` e controle de regressões.

## Material de Referência e Consulta Avançada
Consulte o arquivo `referencias.md` desta pasta para acessar os links diretos das documentações oficiais (Google Antigravity, Claude Code e OpenAI Codex) e o mapeamento completo das obras de Addy Osmani (*Beyond Vibe Coding*) e Tom Taulli (*AI-Assisted Programming*).
