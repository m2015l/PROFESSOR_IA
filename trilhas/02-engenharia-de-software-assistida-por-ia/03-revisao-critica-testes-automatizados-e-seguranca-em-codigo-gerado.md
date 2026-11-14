# Aula 03 — Revisão Crítica, Testes Automatizados e Segurança em Código Gerado

> **Fonte(s) desta aula:**
> - Livro: *Beyond Vibe Coding: From Coder to AI-Era Developer* (Addy Osmani) — Parte II, Capítulo 5 (*Understanding Generated Code: Review, Refine, Own*, pp. 97–108) e Parte III, Capítulos 8 e 9 (*Security, Maintainability, and Reliability*, *The Ethical Implications of Vibe Coding*, pp. 143–186).
> - Livro: *AI-Assisted Programming* (Tom Taulli) — Capítulo 8 (*Coding*, Seção *Refactoring*, pp. 162–166) e Capítulo 9 (*Debugging, Testing, and Deployment*, pp. 179–192).

---

## 1. Problema e Definição

Modelos de linguagem são treinados em vastos repositórios públicos que contêm tanto implementações seguras quanto padrões obsoletos, vulnerabilidades de segurança e tratamento incompleto de erros. Estudos empíricos sobre assistentes de código demonstram que entre 25% e 33% dos trechos gerados sem restrições explícitas de segurança podem apresentar fragilidades catalogadas como CWE (*Common Weakness Enumeration*), além de falhas silenciosas em casos de borda.

Por essa razão, a regra fundamental da engenharia assistida por IA é a **responsabilidade integral do autor humano**: nunca registrar em controle de versão (`git commit`) código que não tenha sido compreendido, revisado contra vulnerabilidades e validado por testes automatizados determinísticos.

A revisão crítica de código gerado por IA concentra-se em três dimensões:

1. **Auditoria de Segurança (Prevenção de Vulnerabilidades):**
   - **Injeção de SQL e Comandos:** Modelos frequentemente geram consultas concatenando strings formatadas (`f"SELECT * FROM usuarios WHERE id = '{user_id}'"`). Toda interação com banco de dados deve exigir consultas parametrizadas (*prepared statements*).
   - **Exposição de Segredos e Dados Sensíveis:** Assistentes podem inserir chaves de API fictícias ou reais diretamente no código-fonte (*hardcoded secrets*) ou expor *stack traces* internos e caminhos de servidor nas respostas de erro HTTP. Além disso, dados reais de clientes (PII) e credenciais nunca devem ser enviados em prompts para modelos em nuvem.
   - **Autenticação, Autorização e Configurações Inseguras:** Código gerado para rotas de API frequentemente valida apenas o caminho de sucesso, omitindo verificações de propriedade do recurso (*Broken Object Level Authorization*), desabilitando verificação de certificados TLS (`verify=False`), abrindo políticas CORS irrestritas (`allow_origins=["*"]` com credenciais) ou utilizando algoritmos criptográficos obsoletos (como MD5/SHA-1 em vez de Argon2/bcrypt ou `hmac.compare_digest` em tempo constante).
   - **Alucinação e Obsolescência de Pacotes:** O modelo pode importar bibliotecas descontinuadas, versões com CVEs conhecidos ou pacotes inexistentes (vetor explorado em ataques de *slopsquatting* / *typosquatting*).

2. **Manutenibilidade e Refatoração:**
   - Código gerado por IA tende a ser prolixo, repetindo blocos de validação em múltiplas funções em vez de reutilizar abstrações existentes no projeto. A revisão humana deve aplicar extração de funções puras, simplificação de condicionais e remoção de código morto (*dead code*).

3. **Malha de Testes Automatizados (`pytest`):**
   - A geração de código por IA aumenta a velocidade de escrita; consequentemente, a barreira de contenção contra regressões deve ser uma suíte de testes automatizados cobrindo quatro categorias: (a) caminho padrão (*happy path*), (b) casos de fronteira e coleções vazias, (c) entradas inválidas que devem disparar exceções específicas (`pytest.raises`), e (d) propriedades de segurança e idempotência.

---

## 2. Aplicação Prática

O exemplo a seguir contrasta um trecho vulnerável tipicamente gerado por IA sem restrições com sua versão refatorada e auditada para produção, acompanhada da respectiva suíte de testes unitários em `pytest`:

```python
import hmac
import os
import sqlite3
from dataclasses import dataclass
import pytest


# --- EXEMPLO INSEGURO (NÃO UTILIZAR EM PRODUÇÃO) ---
# Problemas presentes no trecho abaixo:
# 1. Credencial hardcoded no código-fonte.
# 2. Vulnerabilidade crítica de SQL Injection via f-string.
# 3. Comparação de token vulnerável a ataque de tempo (timing attack).
# 4. Fechamento de conexão ausente em caso de exceção.
def buscar_relatorio_inseguro(db_path: str, cliente_id: str, token: str) -> list:
    if token != "segredo_fixo_123":
        raise PermissionError("Token inválido para o cliente " + cliente_id)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    query = f"SELECT id, valor FROM faturas WHERE cliente_id = '{cliente_id}'"
    return cursor.execute(query).fetchall()


# --- IMPLEMENTAÇÃO AUDITADA E SEGURA PARA PRODUÇÃO ---
@dataclass(frozen=True)
class Fatura:
    fatura_id: int
    cliente_id: str
    valor: float


def autenticar_token_constante(token_recebido: str, variavel_ambiente: str = "APP_API_TOKEN") -> None:
    """Valida token em tempo constante lendo o segredo exclusivamente do ambiente."""
    token_esperado = os.environ.get(variavel_ambiente)
    if not token_esperado:
        raise RuntimeError("Configuração de segurança ausente no ambiente do servidor.")

    if not token_recebido or not hmac.compare_digest(
        token_recebido.encode("utf-8"), token_esperado.encode("utf-8")
    ):
        # Mensagem genérica que não vaza informações internas
        raise PermissionError("Credenciais de autenticação inválidas.")


def listar_faturas_por_cliente(
    db_path: str, cliente_id: str, token_recebido: str
) -> list[Fatura]:
    """Consulta faturas usando parâmetros vinculados (prepared statements) e context manager."""
    autenticar_token_constante(token_recebido)

    cliente_limpo = cliente_id.strip()
    if not cliente_limpo:
        raise ValueError("O identificador cliente_id não pode ser vazio.")

    query = "SELECT id, cliente_id, valor FROM faturas WHERE cliente_id = ? ORDER BY id ASC"
    with sqlite3.connect(db_path) as conn:
        cursor = conn.execute(query, (cliente_limpo,))
        linhas = cursor.fetchall()

    return [Fatura(fatura_id=int(r[0]), cliente_id=str(r[1]), valor=float(r[2])) for r in linhas]


# --- SUÍTE DE TESTES AUTOMATIZADOS (PYTEST) ---
@pytest.fixture
def banco_temporario(tmp_path, monkeypatch):
    monkeypatch.setenv("APP_API_TOKEN", "tok_seguro_producao_99")
    caminho_db = str(tmp_path / "teste.db")
    with sqlite3.connect(caminho_db) as conn:
        conn.execute("CREATE TABLE faturas (id INTEGER PRIMARY KEY, cliente_id TEXT, valor REAL)")
        conn.executemany(
            "INSERT INTO faturas (id, cliente_id, valor) VALUES (?, ?, ?)",
            [(1, "CLI_01", 250.0), (2, "CLI_01", 500.0), (3, "CLI_02", 900.0)],
        )
    return caminho_db


def test_listar_faturas_caminho_padrao(banco_temporario):
    faturas = listar_faturas_por_cliente(banco_temporario, "CLI_01", "tok_seguro_producao_99")
    assert len(faturas) == 2
    assert sum(f.valor for f in faturas) == 750.0


def test_bloqueio_tentativa_sql_injection(banco_temporario):
    # Payload clássico de SQL Injection deve ser tratado literalmente como string e retornar lista vazia
    payload_malicioso = "CLI_01' OR '1'='1"
    faturas = listar_faturas_por_cliente(
        banco_temporario, payload_malicioso, "tok_seguro_producao_99"
    )
    assert faturas == []


def test_rejeicao_token_invalido_e_id_vazio(banco_temporario):
    with pytest.raises(PermissionError):
        listar_faturas_por_cliente(banco_temporario, "CLI_01", "token_incorreto")

    with pytest.raises(ValueError):
        listar_faturas_por_cliente(banco_temporario, "   ", "tok_seguro_producao_99")
```

---

## 3. Critério de Decisão

| Etapa do Ciclo de Vida | Prática Obrigatória de Engenharia | Prática Inaceitável e Risco Associado |
| :--- | :--- | :--- |
| Elaboração de prompts para depuração de erros com dados de clientes | Anonimizar e substituir registros reais por dados sintéticos representativos antes de enviar ao modelo | Colar dumps reais de banco de dados, tokens `.env` ou CPFs/e-mails de clientes em ferramentas de IA. |
| Adição de novas bibliotecas sugeridas por um agente de código | Verificar existência real do pacote no PyPI, manutenção ativa, licença compatível (MIT/BSD/Apache 2.0) e fixar versão | Executar `pip install` cegamente em pacotes sugeridos pela IA sem verificar se o nome é legítimo ou se possui vulnerabilidades conhecidas. |
| Geração de testes unitários com auxílio de IA | Escrever ou revisar as asserções garantindo que testam a regra de negócio e falham quando o código de produção está incorreto | Solicitar que a IA gere os testes a partir do próprio código defeituoso que ela acabou de criar, validando apenas o comportamento atual (inclusive os bugs). |
| Revisão de Pull Requests contendo código gerado por IA | Aplicar checklist de segurança (SQL parametrizado, variáveis de ambiente, autorização, tratamento de nulos) e exigir cobertura de casos de borda | Aprovar PRs grandes baseando-se apenas no fato de o código compilar ou funcionar para um único exemplo manual. |

---

## 4. Erros Comuns

1. **Testes Unitários Tautológicos Gerados após a Implementação:**
   - **Falha:** Pedir ao mesmo modelo que escreveu uma função com erro lógico que "gere testes unitários para esta função". O modelo lê a implementação defeituosa e cria asserções (`assert`) que esperam exatamente o resultado incorreto produzido pelo bug, gerando 100% de aprovação falsa na suíte de testes.
   - **Correção:** Especificar os casos de teste e os valores esperados a partir dos requisitos de negócio (abordagem TDD) antes da implementação, ou revisar manualmente cada valor esperado nas asserções (`assert resultado == valor_esperado_pela_regra`).

2. **Vazamento de Segredos e Informações de Infraestrutura em Logs e Erros:**
   - **Falha:** Aceitar blocos `except Exception as e: return {"erro": str(e)}` sugeridos por assistentes de IA em APIs de produção. Isso expõe ao cliente externo a estrutura de tabelas do banco de dados, caminhos internos de diretórios e versões de drivers.
   - **Correção:** Registrar os detalhes técnicos internamente via módulo `logging` estruturado e retornar ao cliente HTTP apenas mensagens padronizadas e códigos de status adequados (`400`, `401`, `403`, `404`, `500`).

3. **Duplicação Silenciosa de Utilitários já Existentes no Repositório:**
   - **Falha:** Quando o agente não conhece todos os módulos utilitários do projeto, ele cria uma nova função de conexão com banco ou formatação de datas dentro do arquivo que está editando, gerando múltiplas implementações divergentes da mesma regra no repositório.
   - **Correção:** Indicar explicitamente no prompt os módulos compartilhados que devem ser reutilizados e verificar na revisão de código se nenhuma função utilitária existente foi reimplementada.

4. **Violação de Licenças de Software Livre Restritivas (Copyleft):**
   - **Falha:** Aceitar trechos extensos de código gerados literalmente a partir de projetos sob licenças restritivas (como GPL/AGPL) dentro de repositórios proprietários de consultoria sem verificar a origem.
   - **Correção:** Caso um trecho gerado apresente comentários específicos de autoria externa ou estrutura idêntica a código de terceiros, verificar a licença da biblioteca original e preferir importar o pacote oficial licenciado permissivamente ou reescrever a implementação seguindo a especificação interna.
