# Aula 02 — Fluxo Operacional com Agentes de Código em CLI e IDE

> **Fonte(s) desta aula:**
> - Livro: *Beyond Vibe Coding: From Coder to AI-Era Developer* (Addy Osmani) — Parte III, Capítulo 10 (*Autonomous Background Coding Agents*, pp. 187–204).
> - Documentação Oficial: *Google Antigravity Documentation — Getting Started & CLI Reference* ([https://antigravity.google/docs/getting-started](https://antigravity.google/docs/getting-started) e [https://antigravity.google/docs/cli/reference](https://antigravity.google/docs/cli/reference)).
> - Documentação Oficial: *Claude Code Documentation — Overview* ([https://code.claude.com/docs/en/overview](https://code.claude.com/docs/en/overview)).
> - Documentação Oficial: *OpenAI Codex / ChatGPT Cloud Documentation* ([https://learn.chatgpt.com/docs/cloud](https://learn.chatgpt.com/docs/cloud)).

---

## 1. Problema e Definição

Assistentes tradicionais de autocompletar em linha operam de forma reativa e restrita ao arquivo aberto no editor, sendo incapazes de pesquisar referências em todo o repositório, executar suítes de testes no terminal ou coordenar refatorações em múltiplos módulos. Para superar essa limitação, a engenharia de software moderna utiliza **agentes de código** integrados ao terminal (CLI), à IDE ou a ambientes de execução isolados em nuvem.

Diferentemente de um chat passivo, um agente de código opera em um ciclo autônomo composto por quatro estágios (**Plan → Execute → Verify → Report**):

1. **Planejamento (*Plan*):** O agente analisa a solicitação do engenheiro, lê os arquivos de configuração do projeto (`GEMINI.md`, `CLAUDE.md`, `AGENTS.md`) e realiza buscas textuais e estruturais no repositório (`grep`/`ripgrep`, listagem de diretórios, leitura de arquivos) para mapear os módulos impactados e formular um plano de execução antes de editar o código.
2. **Execução (*Execute*):** O agente aplica edições cirúrgicas nos arquivos de código-fonte, cria novos módulos quando necessário e gerencia dependências usando ferramentas nativas de manipulação de arquivos e execução de shell.
3. **Verificação (*Verify*):** O diferencial técnico central de um agente é fechar o ciclo de validação executando diretamente compiladores, verificadores de tipo (`mypy`, `pyright`), linters (`ruff`) e suítes de testes (`pytest`). Se um teste falha, o agente lê o *traceback* real do terminal e itera na correção antes de devolver a resposta.
4. **Relatório e Revisão (*Report*):** Ao concluir a tarefa e validar os testes, o agente apresenta o resumo técnico das alterações e o *diff* (ou abre um Pull Request) para revisão humana.

As três principais plataformas utilizadas no fluxo da Diretoria possuem características operacionais complementares:
- **Google Antigravity (`GEMINI.md`):** Ambiente agêntico integrado que combina edição de código, execução de comandos em terminal, gerenciamento de artefatos estruturados (planos de implementação, relatórios e listas de tarefas) e invocação de subagentes especializados (pesquisa de código, automação de navegador).
- **Claude Code (`CLAUDE.md`):** Agente de linha de comando que opera diretamente no terminal local sobre o repositório Git do desenvolvedor. Permite navegação profunda na base de código, execução controlada de comandos Bash com aprovação granular de permissões e compactação de histórico para controle de contexto.
- **OpenAI Codex CLI e Cloud (`AGENTS.md`):** Opera tanto localmente via terminal quanto como agente assíncrono em segundo plano (*background agent*), instanciando contêineres isolados (*sandboxes*) pré-carregados com o repositório para executar tarefas em paralelo, rodar testes repetidamente e entregar patches prontos para revisão.

---

## 2. Aplicação Prática

Para que um agente de código opere com precisão e sem degradar a janela de contexto, o engenheiro deve estruturar o ambiente do repositório e conduzir a sessão por meio de prompts operacionais verificáveis. O exemplo abaixo demonstra um script utilitário de pré-verificação local (`scripts/check_agent_task.py`) que os agentes devem ser instruídos a executar ao final de cada subtarefa:

```python
import subprocess
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent


def executar_etapa(nome: str, comando: list[str]) -> bool:
    print(f"=== [VERIFICACAO] {nome}: {' '.join(comando)} ===")
    proc = subprocess.run(
        comando,
        cwd=ROOT_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if proc.stdout:
        print(proc.stdout.strip())
    if proc.stderr:
        print(proc.stderr.strip(), file=sys.stderr)

    if proc.returncode != 0:
        print(f"[FALHA] A etapa '{nome}' retornou código {proc.returncode}.")
        return False

    print(f"[OK] {nome} concluída sem erros.\n")
    return True


def main() -> None:
    # Sequência determinística de validação para agentes de código (CLI/IDE/Sandbox)
    etapas = [
        ("Sintaxe e Compilacao Python", [sys.executable, "-m", "compileall", "-q", "src"]),
        ("Linter e Formatacao (Ruff)", [sys.executable, "-m", "ruff", "check", "src", "tests"]),
        ("Suite de Testes Unitarios", [sys.executable, "-m", "pytest", "tests", "-q"]),
    ]

    for nome, cmd in etapas:
        if not executar_etapa(nome, cmd):
            sys.exit(1)

    print("[SUCESSO] Todas as verificações passaram. Código pronto para revisão de git diff.")


if __name__ == "__main__":
    main()
```

Abaixo, o protocolo de prompt estruturado para delegar uma tarefa multi-arquivo a qualquer um dos três agentes (Antigravity, Claude Code ou Codex):

```markdown
Tarefa: Implementar validação de schema no módulo `src/ingestao/clientes.py`.

1. Contexto e Arquivos Alvo:
   - Leia apenas `src/ingestao/clientes.py`, `src/schemas/contratos.py` e `tests/test_clientes.py`.
   - Não altere nenhum arquivo fora desses três caminhos.

2. Especificação da Mudança:
   - Substitua o dicionário bruto na função `carregar_clientes_json()` pela validação com o modelo Pydantic `ClienteContrato` definido em `src/schemas/contratos.py`.
   - Registros que lançarem `ValidationError` devem ser salvos na lista de rejeitados retornada como segundo elemento da tupla `(df_validos, lista_rejeitados)`.

3. Critério de Conclusão (Verificação):
   - Adicione dois testes em `tests/test_clientes.py`: um para lote 100% válido e outro contendo CPF nulo e limite negativo.
   - Execute `python scripts/check_agent_task.py` e só encerre a tarefa quando o comando retornar código 0.
```

---

## 3. Critério de Decisão

| Cenário de Engenharia | Modo e Ferramenta Recomendados | Abordagem a Evitar e Justificativa Técnica |
| :--- | :--- | :--- |
| Implementação de lógica central complexa com decisões arquiteturais passo a passo | Sessão interativa síncrona na IDE/CLI (Antigravity ou Claude Code) com aprovação de plano antes da edição | Disparar um agente assíncrono em segundo plano sem especificação detalhada, gerando um Pull Request extenso com premissas arquiteturais incorretas. |
| Tarefas bem delimitadas, independentes e paralelizáveis (atualizar chamadas de API depreciadas, criar testes para módulo existente, corrigir avisos de linter) | Delegação assíncrona para agente em sandbox isolado (Codex Cloud / subagentes em branch separada) | Executar essas tarefas sequencialmente na mesma conversa principal, poluindo a janela de contexto com logs de dezenas de arquivos. |
| Transição entre duas tarefas sem relação temática (ex.: terminar ajuste de SQL e iniciar endpoint FastAPI) | Limpar ou iniciar nova sessão de contexto (`/clear` ou nova conversa) após realizar o commit da tarefa concluída | Manter uma única sessão contínua por horas, acumulando arquivos antigos no contexto, o que aumenta o custo de tokens e reduz a precisão do modelo. |
| Execução de comandos pelo agente no ambiente de desenvolvimento | Permitir leitura e execução de testes locais (`pytest`, `ruff`, `git status`, `git diff`) e exigir confirmação humana para comandos destrutivos ou de rede | Executar agentes em modo de aprovação irrestrita (`--dangerously-skip-permissions` ou equivalente) fora de um contêiner/sandbox isolado. |

---

## 4. Erros Comuns

1. **Poluição da Janela de Contexto (*Context Rot*):**
   - **Falha:** Acumular em uma única sessão de agente a leitura de dezenas de arquivos grandes, saídas brutas de CSVs ou múltiplos assuntos distintos. À medida que o histórico cresce, o modelo passa a confundir requisitos antigos com os atuais e perde precisão nas edições de código.
   - **Correção:** Restringir no prompt os diretórios ou arquivos relevantes, limpar o contexto entre tarefas independentes e utilizar subagentes de pesquisa quando for necessário explorar uma base de código desconhecida.

2. **Ambiente de Execução do Agente Desalinhado com o Projeto (*Environment Mismatch*):**
   - **Falha:** Solicitar que o agente implemente e valide uma funcionalidade quando o ambiente virtual (`.venv`) não contém o `pytest` ou as dependências do projeto instaladas. Sem conseguir rodar os testes na etapa *Verify*, o agente entrega código não testado que falha na integração contínua (CI).
   - **Correção:** Garantir que o ambiente virtual esteja ativo e documentar nos arquivos `GEMINI.md`, `CLAUDE.md` e `AGENTS.md` o caminho exato do interpretador Python e dos comandos de teste do repositório.

3. **Delegação sem Estado Limpo no Controle de Versão (`git status` Sujo):**
   - **Falha:** Acionar um agente para realizar uma refatoração ampla enquanto o repositório local já possui dezenas de arquivos modificados e não commitados. Se o agente cometer um erro estrutural, torna-se difícil reverter apenas as alterações da IA sem perder o trabalho manual anterior.
   - **Correção:** Antes de iniciar qualquer tarefa com agente de código, confirmar que a árvore de trabalho está limpa (`git status` sem pendências) ou criar uma branch dedicada para a tarefa.

4. **Dilema do Custo Afundado (*Sunk Cost*) em Patches de Agentes:**
   - **Falha:** Gastar horas tentando consertar manualmente um Pull Request complexo gerado por um agente que partiu de uma abordagem arquitetural equivocada.
   - **Correção:** Se a estrutura gerada pelo agente violar o design do sistema, descarte o patch imediatamente (`git checkout -- .`), refine a especificação técnica corrigindo a ambiguidade do prompt e execute uma nova geração limpa.

---

## 5. Aprofundamento Interativo por Plataforma (Antigravity, Claude Code e Codex)

> **Protocolo Interativo Obrigatório desta Aula:**
> Durante a condução desta aula, o tutor deve perguntar explicitamente ao aluno em qual(is) plataforma(s) de coding ele deseja se aprofundar — **Google Antigravity**, **Claude Code** ou **OpenAI Codex** (permitindo que o aluno escolha **uma, duas ou todas as três opções**) — e aguardar a resposta. Em seguida, o tutor deve explicar integralmente todas as capacidades de cada plataforma escolhida com base nas subseções abaixo (superfícies, configurações, comandos, artefatos, integrações, orquestração e segurança).

### 5.1 Google Antigravity

1. **Superfícies de Execução e Interfaces:**
   - **Antigravity IDE:** ambiente de desenvolvimento baseado no VS Code com três modalidades operacionais integradas:
     - *Antigravity Tab* (passiva): autocompletar em linha, *Supercomplete* (proposta de *diffs* maiores em janelas flutuantes), *Tab to Jump* (navegação antecipada para o próximo ponto de edição) e *Tab to Import* (adição automática de importações).
     - *Inline Command* (`Cmd+I` no macOS / `Ctrl+I` no Windows e Linux): edições direcionadas em blocos selecionados, geração de código no cursor e inserção rápida de *docstrings*.
     - *Sidebar Chat, Agent Mode & Planning Mode*: painel colaborativo para planejamento passo a passo antes da edição, leitura e escrita de múltiplos arquivos, execução no terminal e uso de ferramentas externas.
     - Recursos visuais do editor: *Inline Code Lenses* acima de classes e funções (`Refactor`, `Write Tests`, `Explain Code`), *Visual Diff Overlays* para aceitar ou rejeitar alterações em linha e *Diagnostic Auto-Fix* a partir de erros de compilação ou linter.
   - **Antigravity App (Desktop / Antigravity 2.0):** aplicativo desktop paralelo para orquestração de conversas e múltiplos projetos/workspaces independentemente da IDE, incluindo painel de *Scheduled Tasks* (tarefas recorrentes via cron e timers), gerenciador de *Skills & Customizations*, menções contextuais via `@` (arquivos, pastas, conversas anteriores, sessões de terminal, regras e servidores MCP) e upload direto de imagens e arquivos na conversa.
   - **Antigravity CLI (`agy`):** interface de terminal para interação rápida e automação (`agy --help` para flags e subcomandos, `/help` dentro da TUI, `/exit`, `/quit` ou `Ctrl+D Ctrl+D` para encerrar, e configuração em `~/.gemini/antigravity-cli/settings.json`).
   - **Antigravity Python SDK (`pip install google-antigravity`):** biblioteca oficial para instanciar e orquestrar agentes programaticamente em pipelines Python usando `Agent`, `LocalAgentConfig` (somente leitura por padrão) e `CapabilitiesConfig` (habilitação explícita de escrita/comandos), com suporte a streaming assíncrono de tokens, `response.thoughts` e `response.tool_calls`.

2. **Configuração, Regras e Descoberta Hierárquica:**
   - **Regras Persistentes:** o agente percorre a árvore de diretórios do diretório de trabalho até a raiz do repositório Git carregando `GEMINI.md`, `AGENTS.md` e `.agents/rules/*.md` (também suporta `.agent/`, `_agents/`, `_agent/`), além do escopo global da máquina em `~/.gemini/AGENTS.md` e `~/.gemini/config/`.
   - **Precedência e Ativação:** configurações do workspace têm prioridade sobre declarações em `skills.json`/`plugins.json` e sobre configurações globais. Regras podem usar ativação `always_on` (sempre carregadas) ou `model_decision` (carregamento sob demanda, com deduplicação por caminho resolvido).

3. **Comandos e *Slash Commands* (`/`):**
   - `/plan`: força planejamento estruturado antes de executar modificações em código.
   - `/goal`: modo de execução contínua voltado a atingir um objetivo complexo até a verificação final.
   - `/grill-me`: entrevista interativa prévia para esclarecer requisitos e decisões arquiteturais antes da execução.
   - `/compact`: resume a conversa atual para liberar espaço na janela de contexto.
   - `/browser`: encaminha a tarefa diretamente para o subagente de navegador.
   - `/schedule`: cria timers pontuais ou tarefas cron recorrentes em segundo plano.
   - `/swarm` e `/teamwork`: coordena múltiplos agentes trabalhando em paralelo em um quadro de mensagens compartilhado.
   - `/boost`: direciona o agente para planejamento estratégico aprofundado e verificação rigorosa.
   - `/plugin`, `/learn` e `/migrate-workflows`: gerenciam plugins, registram padrões aprendidos e convertem fluxos legados (`.agents/workflows/`) em *Skills*.

4. **Artefatos e Superfícies de Revisão:**
   - Gera **artefatos estruturados em Markdown e mídia** para revisão assíncrona (*human-in-the-loop*): planos de implementação executáveis (com botão de aprovação ou solicitação de ajustes), relatórios de análise, listas de tarefas, *diffs* de código, diagramas Mermaid, capturas de tela e gravações de sessões do navegador, além de widgets HTML interativos.
   - No Antigravity App e na IDE, os artefatos aparecem em painéis auxiliares dedicados (Artefatos, Subagentes, Tarefas em Segundo Plano, Arquivos Modificados e Terminais).

5. **Integrações e Extensibilidade:**
   - **Agent Skills (`skills/<nome>/SKILL.md`):** módulos com instruções, scripts auxiliares e referências que utilizam **carregamento progressivo** (*progressive disclosure*): apenas nome e descrição entram no contexto inicial; o conteúdo completo só é lido quando a tarefa exige.
   - **Plugins (`plugins/<nome>/plugin.json`):** empacotam *skills*, regras, subagentes, *hooks* e servidores MCP em uma unidade instalável e versionável.
   - **Hooks (`hooks.json`):** executam scripts determinísticos em eventos explícitos do ciclo de vida do agente (como pré-execução de ferramentas).
   - **MCP (*Model Context Protocol*):** configurado em `mcp_config.json` ou `.antigravity/settings.json` para conectar o agente a bancos de dados, APIs, documentações e serviços externos (como GitHub ou servidores corporativos).
   - **Automação de Navegador:** subagente especializado com abas paralelas, interação em aplicações web autenticadas, envio/download de arquivos em área isolada (`browser_sandbox`) e integração com Chrome DevTools MCP para inspeção de rede, acessibilidade, cookies e desempenho (LCP e memória).

6. **Orquestração, Permissões e Segurança:**
   - **Subagentes, Workflows e Swarms:** permite definir subagentes customizados, executar scripts de orquestração em Python (`run_workflow`) para paralelizar ou encadear chamadas em lote e coordenar *swarms* com workspaces isolados (`inherit`, `share` em cópia de trabalho compartilhada no repositório ou `branch` em clone isolado).
   - **Controles de Segurança:** *Terminal Sandbox* para isolamento de comandos de shell, políticas configuráveis por projeto e globais para execução de ferramentas (`always-proceed`, `request-review`, `strict`, `proceed-in-sandbox`), políticas de acesso a arquivos fora do workspace (`allow`, `ask`, `deny`), política de acesso à internet, *allowlist/denylist* de comandos de terminal e *allowlist* de domínios no navegador.

---

### 5.2 Claude Code

1. **Superfícies de Execução e Interfaces:**
   - **CLI no Terminal (`claude`):** agente da Anthropic executado diretamente no terminal do repositório Git local, com leitura de base de código, edição direta de arquivos, execução de comandos Bash e integração com `git` e `gh` CLI.
   - **Integrações Complementares:** disponível também por extensões de IDE (VS Code e JetBrains), aplicativo desktop e interface web/remota, mantendo o mesmo modelo de projeto e ferramentas.

2. **Configuração, Regras e Memória Persistente:**
   - **`CLAUDE.md`:** arquivo Markdown carregado automaticamente no início de cada sessão (na raiz do projeto, em subdiretórios relevantes ou no diretório do usuário), registrando comandos de build, suíte de testes, padrões arquiteturais, convenções e restrições obrigatórias.
   - **Descoberta Automática e Edição:** o comando `/init` aciona um subagente interno para analisar a estrutura do repositório e gerar um `CLAUDE.md` inicial; o comando `/memory` abre os arquivos `CLAUDE.md` para edição manual e controla as opções de memória automática entre sessões.

3. **Comandos e *Slash Commands* (`/`):**
   - `/clear` (ou `/reset`): limpa todo o histórico da conversa atual e reinicia a sessão com janela de contexto limpa, aceitando argumento opcional de foco (ex.: `/clear refatoracao-autenticacao`).
   - `/compact`: resume o histórico da conversa e substitui o contexto atual pelo resumo gerado, aceitando instruções de preservação (ex.: `/compact manter nomes dos testes que falharam`).
   - `/init`: gera automaticamente um rascunho inicial de `CLAUDE.md` a partir do repositório.
   - `/memory`: gerencia arquivos `CLAUDE.md` e configurações de memória persistente.
   - `/plan`: ativa o modo de planejamento para estruturar a estratégia técnica antes de editar qualquer arquivo.
   - `/review`: executa revisão local das alterações não commitadas ou modificações recentes no repositório.
   - `/permissions` (alias `/allowed-tools`): visualiza e edita regras de permissão (`allow`, `ask`, `deny`) para ferramentas locais, Bash e servidores MCP.
   - `/mcp`: gerencia conexões com servidores MCP, diagnósticos e fluxos de autenticação OAuth.
   - Comandos e *skills* nativas de qualidade como `/verify` e `/simplify` para verificação e simplificação antes de commits.

4. **Artefatos, Planos e Superfícies de Revisão:**
   - Produz **planos de execução** no modo `/plan` para validação prévia antes da alteração de código.
   - Exibe *diffs* explícitos no terminal/IDE a cada edição proposta para aprovação granular, além de relatórios de análise de código via `/review` e geração estruturada de mensagens de commit e descrições de Pull Request integradas ao fluxo Git.

5. **Integrações e Extensibilidade:**
   - **Skills e Comandos Customizados (`.claude/skills/` e `.claude/commands/`):** fluxos e prompts repetíveis salvos em Markdown e acionados via `/nome-da-skill`. Suportam parametrização dinâmica com o marcador `$ARGUMENTS` (por exemplo, para triagem de bugs ou revisão arquitetural) e podem ser configurados para execução automática antes de commits.
   - **Hooks (Automação Determinística por Eventos):** comandos shell ou scripts vinculados a eventos explícitos do ciclo de vida (`PreToolUse`, `PostToolUse`, `SubagentStop`). Diferentemente de instruções no prompt, *hooks* executam de forma garantida sempre que o evento ocorre — usados para formatar código automaticamente após edições, rodar linters (`ruff`) ou bloquear comandos destrutivos antes da execução. Podem ser definidos nas configurações globais/do projeto ou no *frontmatter* de *skills* e subagentes.
   - **MCP (*Model Context Protocol*):** conecta o Claude Code a sistemas externos (GitHub, PostgreSQL, Sentry, serviços em nuvem e APIs internas). Além de ferramentas externas, servidores MCP podem expor *MCP Prompts* reutilizáveis como comandos na sessão.

6. **Orquestração, Permissões e Segurança:**
   - **Subagentes (`.claude/agents/`):** assistentes especializados definidos em arquivos Markdown com prompt de sistema próprio, janela de contexto isolada e permissões restritas de ferramentas (ex.: `@debugger` ou `@code-reviewer`). Podem ser acionados manualmente por menção `@` ou delegados automaticamente pelo agente principal para evitar poluição da sessão principal.
   - **Permissões Granulares e Sandbox:** por padrão exige confirmação humana para gravações de arquivos e comandos Bash; regras em `/permissions` permitem liberar comandos seguros de leitura/teste (`pytest`, `git diff`) e bloquear ações destrutivas. O modo `--dangerously-skip-permissions` deve ser restringido exclusivamente a contêineres ou *sandboxes* descartáveis sem acesso a credenciais sensíveis.

---

### 5.3 OpenAI Codex (CLI e Codex Cloud)

1. **Superfícies de Execução e Interfaces:**
   - **Codex CLI (`codex`):** agente de código open-source (licença Apache 2.0) executado no terminal via TUI interativa. Lê o repositório local, aplica patches cirúrgicos e executa comandos de terminal em ambiente isolado. Suporta autenticação via assinatura ChatGPT (Plus, Pro ou Team) ou chave de API (`OPENAI_API_KEY`).
   - **Codex Cloud (Agente Assíncrono em Nuvem):** interface web e serviço em segundo plano que executa tarefas de engenharia em contêineres gerenciados na nuvem, pré-carregados com o repositório e suas dependências, permitindo disparar múltiplas tarefas em paralelo sem bloquear a máquina local.

2. **Configuração, Regras e Planos Persistentes:**
   - **`AGENTS.md`:** arquivo padrão de instruções operacionais para agentes de código. O Codex combina instruções globais em `~/.codex/AGENTS.md` com instruções hierárquicas encontradas na árvore de diretórios do projeto (comandos de setup, build, testes e estilo).
   - **`PLANS.md`:** convenção de planos de execução detalhados (frequentemente referenciada em `AGENTS.md`) para estruturar refatorações extensas em marcos verificáveis antes da implementação.
   - **`~/.codex/config.toml`:** arquivo central de configuração em formato TOML para seleção de modelo, políticas de aprovação, parâmetros de *sandbox* e declaração de servidores MCP.

3. **Comandos e *Slash Commands* (`/`):**
   - `/init`: gera um arquivo `AGENTS.md` inicial adaptado à estrutura do repositório atual.
   - `/plan`: ativa o *Plan Mode*, exigindo que o agente apresente o plano passo a passo para aprovação antes de modificar arquivos ou rodar comandos de escrita.
   - `/compact`: resume o histórico da conversa para reduzir o consumo de tokens e preservar espaço útil na janela de contexto.
   - `/diff`: mostra o status Git e o *diff* completo da árvore de trabalho local (incluindo arquivos novos ainda não rastreados).
   - `/review`: executa uma revisão técnica focada nas alterações locais pendentes ou em *stage*.
   - `/permissions`: ajusta dinamicamente o modo de autonomia durante a sessão (alternando entre modos como *Read Only* e *Auto*).
   - `/model`: troca o modelo subjacente ativo na sessão e ajusta o nível de esforço de raciocínio.
   - `/status`: exibe o estado atual da sessão, diretório ativo e métricas de uso de contexto.
   - `/mcp`: lista servidores e ferramentas MCP conectados (com opção `/mcp verbose` para diagnóstico completo).

4. **Artefatos, Diffs e Fluxo de Pull Requests:**
   - No **Codex CLI**, os principais artefatos operacionais são planos de execução (`/plan` e `PLANS.md`), patches inspecionáveis localmente via `/diff` e relatórios de auditoria via `/review`.
   - No **Codex Cloud**, cada tarefa assíncrona produz um ambiente de execução auditável contendo o log completo de comandos e testes executados no contêiner, o *diff* consolidado dos arquivos alterados e ação direta na interface web para abrir um **Pull Request** (*Create PR* / *Draft PR*) no GitHub.

5. **Integrações e Extensibilidade:**
   - **GitHub Connectors e Acionamento em Pull Requests:** a integração nativa com o GitHub permite que o Codex Cloud leia branches, crie PRs diretamente a partir de tarefas concluídas e seja acionado em comentários de Pull Requests (por exemplo, mencionando `@codex` para investigar e corrigir falhas de CI ou executar revisões automatizadas de código e segurança).
   - **Agent Skills (`.agents/skills/`):** diretórios modulares contendo guias de procedimento e scripts auxiliares carregados sob demanda conforme o contexto da tarefa.
   - **MCP (*Model Context Protocol*):** declarado em `~/.codex/config.toml` sob seções `[mcp_servers.<nome>]` (com `url` ou comando local e variáveis de ambiente para tokens de autenticação) e gerenciado pelo subcomando `codex mcp` ou `/mcp` na TUI.

6. **Orquestração, Permissões e Segurança:**
   - **Sandbox em Nível de Sistema Operacional:** escrita de arquivos e execução de comandos de shell no Codex CLI e no Codex Cloud ocorrem dentro de um *sandbox* restrito por política de sistema operacional, com acesso à rede desabilitado ou limitado por configuração para evitar exfiltração de dados ou modificações fora do diretório permitido.
   - **Modos de Aprovação:** controle progressivo de autonomia entre *Read Only / Suggest* (todas as edições e comandos exigem confirmação explícita) e *Auto / Full-Auto* dentro dos limites do *sandbox*.
   - **Execução Paralela Assíncrona:** tarefas independentes (correção de bugs isolados, criação de testes unitários, atualização de dependências ou triagem de issues) podem ser enviadas simultaneamente para contêineres do Codex Cloud, mantendo a árvore Git local e a janela de contexto da sessão interativa intactas.
