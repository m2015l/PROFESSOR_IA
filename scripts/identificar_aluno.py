import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import List, Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".aluno.env"
CACHE_PATH = ROOT_DIR / ".aluno.cache.json"
SESSION_PATH = ROOT_DIR / ".aula.session.json"
PROGRESSO_PATH = ROOT_DIR / "progresso.local.md"
PENDING_PATH = ROOT_DIR / "progresso.pending.json"
DEFAULT_API_BASE_URL = "https://professor-ia-web.vercel.app"
USER_AGENT = "PROFESSOR_IA-CLI/2.0"

ARQUIVOS_INTEGRIDADE = (
    ".agent/instrucoes-tutor.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    "scripts/identificar_aluno.py",
    "scripts/sync_progresso.py",
    "trilhas/00-grade-curricular.md",
)


class ErroAutenticacao(Exception):
    """Token ausente, inválido ou rejeitado pelo servidor."""


class ErroConexao(Exception):
    """Falha de comunicação com o servidor sem fallback local disponível."""


def carregar_env(env_path: Path = ENV_PATH) -> dict:
    if not env_path.exists():
        raise FileNotFoundError(f"Arquivo {env_path.name} não encontrado na raiz.")
    env = {}
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def extrair_token_valido(env: dict) -> str:
    token = env.get("ALUNO_TOKEN", "").strip()
    if not token or "substitua" in token.lower():
        return ""
    return token


def resolver_urls_api(api_url: str) -> Tuple[str, str, str]:
    raw = (api_url or "").strip().rstrip("/")
    if "seu-projeto.vercel.app" in raw:
        return "", "", ""
    if not raw:
        base_url = DEFAULT_API_BASE_URL
    else:
        for sufixo in ("/api/progresso", "/api/aluno", "/api/aula/iniciar"):
            if raw.endswith(sufixo):
                raw = raw[: -len(sufixo)]
                break
        base_url = raw.rstrip("/")
    return (
        f"{base_url}/api/aluno",
        f"{base_url}/api/progresso",
        f"{base_url}/api/aula/iniciar",
    )


def gerar_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def extrair_aulas_concluidas_md(md_text: str) -> List[str]:
    return sorted(
        set(re.findall(r"`?([0-9]{2}-[^/`\s]+/[0-9]{2}-[^`\s]+\.md)`?", md_text))
    )


def calcular_hash_integridade_cliente(root_dir: Path = ROOT_DIR) -> str:
    """Calcula SHA-256 determinístico (LF normalizado) dos arquivos de protocolo e scripts."""
    hasher = hashlib.sha256()
    for rel_path in sorted(ARQUIVOS_INTEGRIDADE):
        file_path = root_dir / rel_path
        hasher.update(rel_path.encode("utf-8"))
        hasher.update(b"\x00")
        if file_path.exists():
            conteudo = file_path.read_text(encoding="utf-8").replace("\r\n", "\n")
            hasher.update(conteudo.encode("utf-8"))
        else:
            hasher.update(b"<MISSING>")
        hasher.update(b"\x00")
    return hasher.hexdigest()


def ler_cache_identidade(token: str, cache_path: Path = CACHE_PATH) -> Optional[dict]:
    if not cache_path.exists():
        return None
    try:
        data = json.loads(cache_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("token_sha256") != gerar_token_hash(token):
        return None
    if not data.get("aluno_id") or not data.get("nome"):
        return None
    return data


def salvar_cache_identidade(
    token: str, identidade: dict, cache_path: Path = CACHE_PATH
) -> None:
    aulas = [str(a) for a in (identidade.get("aulas_concluidas") or [])]
    payload = {
        "token_sha256": gerar_token_hash(token),
        "aluno_id": str(identidade["aluno_id"]),
        "nome": str(identidade["nome"]),
        "total_aulas_concluidas": int(identidade.get("total_aulas_concluidas") or len(aulas)),
        "aulas_concluidas": aulas,
    }
    cache_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def salvar_sessao_local(
    token: str,
    aluno_id: str,
    sessao_remota: dict,
    session_path: Path = SESSION_PATH,
) -> None:
    payload = {
        "token_sha256": gerar_token_hash(token),
        "aluno_id": aluno_id,
        "session_nonce": str(sessao_remota["session_nonce"]),
        "aula_caminho": str(sessao_remota["proxima_aula"]),
        "iniciada_em": str(sessao_remota.get("iniciada_em") or ""),
        "min_segundos": int(sessao_remota.get("min_segundos") or 30),
    }
    session_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def ler_sessao_local(
    token: str, session_path: Path = SESSION_PATH
) -> Optional[dict]:
    if not session_path.exists():
        return None
    try:
        data = json.loads(session_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict):
        return None
    if data.get("token_sha256") != gerar_token_hash(token):
        return None
    if not data.get("session_nonce") or not data.get("aula_caminho"):
        return None
    return data


def extrair_erro_http(exc: urllib.error.HTTPError) -> str:
    try:
        raw = exc.read().decode("utf-8", errors="replace").strip()
        if raw:
            data = json.loads(raw)
            if isinstance(data, dict) and data.get("error"):
                return str(data["error"])
            return raw
    except Exception:
        pass
    return f"HTTP {exc.code}"


def buscar_identidade_remota(aluno_url: str, token: str) -> dict:
    req = urllib.request.Request(
        aluno_url,
        method="GET",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, dict) or not data.get("aluno_id") or not data.get("nome"):
        raise ValueError("Resposta inválida do servidor ao identificar aluno.")
    return data


def iniciar_sessao_aula_remota(
    iniciar_url: str, token: str, integrity_hash: str
) -> dict:
    body = json.dumps({"client_integrity_hash": integrity_hash}).encode("utf-8")
    req = urllib.request.Request(
        iniciar_url,
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    if not isinstance(data, dict) or not data.get("ok"):
        raise ValueError("Resposta inválida do servidor ao iniciar sessão de aula.")
    return data


def _montar_markdown_oficial(identidade: dict, aulas: List[str]) -> str:
    relatorio_md = str(identidade.get("relatorio_markdown") or "").strip()
    if relatorio_md:
        return relatorio_md + "\n"

    linhas = [
        "# Progresso Local do Aluno — ITAJr",
        "",
        f"- **Aluno ID:** `{identidade['aluno_id']}`",
        f"- **Nome:** `{identidade['nome']}`",
        "",
        "## Mapa de Aulas Concluídas",
    ]
    for aula in aulas:
        linhas.append(f"- [x] `{aula}` (Sincronizada previamente na nuvem)")
    linhas.extend(["", "## Histórico Detalhado e Parecer Comportamental", ""])
    return "\n".join(linhas)


def reconciliar_progresso_local(
    identidade: dict, progresso_path: Path = PROGRESSO_PATH
) -> Tuple[bool, bool]:
    """
    Garante que progresso.local.md reflita exatamente o estado oficial do Supabase.
    Retorna (arquivo_atualizado, divergencia_local_detectada).
    """
    aulas_nuvem = sorted(
        {
            str(a).strip()
            for a in (identidade.get("aulas_concluidas") or [])
            if str(a).strip()
        }
    )

    if progresso_path.exists():
        texto_local = progresso_path.read_text(encoding="utf-8")
        aulas_locais = extrair_aulas_concluidas_md(texto_local)
        if aulas_locais == aulas_nuvem:
            return False, False

        if aulas_nuvem or str(identidade.get("relatorio_markdown") or "").strip():
            progresso_path.write_text(
                _montar_markdown_oficial(identidade, aulas_nuvem), encoding="utf-8"
            )
        else:
            progresso_path.unlink()
        return True, True

    if aulas_nuvem or str(identidade.get("relatorio_markdown") or "").strip():
        progresso_path.write_text(
            _montar_markdown_oficial(identidade, aulas_nuvem), encoding="utf-8"
        )
        return True, False

    return False, False


def identificar_aluno(
    env: dict, permitir_cache_offline: bool = False
) -> dict:
    token = extrair_token_valido(env)
    if not token:
        raise ErroAutenticacao(
            "ALUNO_TOKEN ausente ou inválido em .aluno.env. Informe apenas o token da Diretoria."
        )

    aluno_url, _, _ = resolver_urls_api(env.get("PROFESSOR_API_URL", ""))
    motivo_falha = "PROFESSOR_API_URL não configurada"

    if aluno_url:
        try:
            identidade = buscar_identidade_remota(aluno_url, token)
            salvar_cache_identidade(token, identidade)
            atualizado, divergencia = reconciliar_progresso_local(identidade)
            identidade["origem"] = "supabase"
            identidade["progresso_restaurado"] = atualizado
            identidade["divergencia_local_corrigida"] = divergencia
            return identidade
        except urllib.error.HTTPError as exc:
            msg = extrair_erro_http(exc)
            if exc.code in (400, 401, 403):
                raise ErroAutenticacao(
                    f"Token rejeitado pelo servidor (HTTP {exc.code}): {msg}"
                ) from exc
            motivo_falha = f"HTTP {exc.code}: {msg}"
        except (urllib.error.URLError, ValueError) as exc:
            motivo_falha = str(getattr(exc, "reason", exc))

    if permitir_cache_offline:
        cache = ler_cache_identidade(token)
        if cache:
            cache["origem"] = "cache_local"
            cache["aviso"] = motivo_falha
            return cache

    raise ErroConexao(
        f"Conexão obrigatória com o servidor falhou ({motivo_falha}). Verifique a internet antes de iniciar a aula."
    )


def main():
    if "--print-integrity-hash" in sys.argv:
        print(calcular_hash_integridade_cliente())
        sys.exit(0)

    if PENDING_PATH.exists():
        print(
            "[ERRO] Existe progresso pendente offline em progresso.pending.json. "
            "Execute 'python scripts/sync_progresso.py' antes de iniciar uma nova aula."
        )
        sys.exit(1)

    try:
        env = carregar_env()
    except FileNotFoundError:
        print("[ERRO] Arquivo .aluno.env não encontrado na raiz.")
        sys.exit(1)

    try:
        identidade = identificar_aluno(env, permitir_cache_offline=False)
    except (ErroAutenticacao, ErroConexao) as exc:
        print(f"[ERRO] {exc}")
        sys.exit(1)

    token = extrair_token_valido(env)
    _, _, iniciar_url = resolver_urls_api(env.get("PROFESSOR_API_URL", ""))
    integrity_hash = calcular_hash_integridade_cliente()

    try:
        sessao = iniciar_sessao_aula_remota(iniciar_url, token, integrity_hash)
    except urllib.error.HTTPError as exc:
        print(f"[ERRO] Falha ao abrir sessão de aula (HTTP {exc.code}): {extrair_erro_http(exc)}")
        sys.exit(1)
    except (urllib.error.URLError, ValueError) as exc:
        motivo = str(getattr(exc, "reason", exc))
        print(f"[ERRO] Falha de conexão ao abrir sessão de aula ({motivo}).")
        sys.exit(1)

    print("[OK] Aluno identificado com sucesso via Supabase.")
    print(f"ALUNO_ID: {identidade['aluno_id']}")
    print(f"ALUNO_NOME: {identidade['nome']}")

    aulas = identidade.get("aulas_concluidas") or []
    print(f"TOTAL_AULAS_CONCLUIDAS: {identidade.get('total_aulas_concluidas', len(aulas))}")
    if aulas:
        print("AULAS_CONCLUIDAS:")
        for aula in aulas:
            print(f"- {aula}")
    else:
        print("AULAS_CONCLUIDAS: nenhuma")

    if identidade.get("divergencia_local_corrigida"):
        print(
            "[AVISO] Divergência detectada em progresso.local.md; "
            "arquivo reconciliado com o histórico oficial da nuvem."
        )
    elif identidade.get("progresso_restaurado"):
        print("[OK] progresso.local.md sincronizado com o histórico oficial da nuvem.")

    if sessao.get("curso_concluido"):
        if SESSION_PATH.exists():
            SESSION_PATH.unlink()
        print("PROXIMA_AULA_OBRIGATORIA: CURSO_CONCLUIDO")
    else:
        salvar_sessao_local(token, str(identidade["aluno_id"]), sessao)
        print(f"PROXIMA_AULA_OBRIGATORIA: {sessao['proxima_aula']}")
        print(f"SESSAO_MINIMO_SEGUNDOS: {sessao.get('min_segundos', 30)}")


if __name__ == "__main__":
    main()
