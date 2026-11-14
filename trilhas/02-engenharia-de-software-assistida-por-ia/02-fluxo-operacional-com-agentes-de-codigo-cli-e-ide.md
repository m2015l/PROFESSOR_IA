# Aula 02 — Fluxo Operacional com Agentes de Código em CLI e IDE

> **Fonte(s) desta aula:**
> - Livro: *Beyond Vibe Coding: From Coder to AI-Era Developer* (Addy Osmani) — Parte III, Capítulo 10 (*Autonomous Background Coding Agents*, pp. 187–204).
> - Documentação Oficial: *Google Antigravity Documentation — Getting Started* ([https://antigravity.google/docs/getting-started](https://antigravity.google/docs/getting-started)).
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
