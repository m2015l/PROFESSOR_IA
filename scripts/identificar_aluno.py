import hashlib
import json
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional, Tuple

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".aluno.env"
CACHE_PATH = ROOT_DIR / ".aluno.cache.json"
PROGRESSO_PATH = ROOT_DIR / "progresso.local.md"
DEFAULT_API_BASE_URL = "https://professor-ia-web.vercel.app"
USER_AGENT = "PROFESSOR_IA-CLI/1.0"


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


def resolver_urls_api(api_url: str) -> Tuple[str, str]:
    raw = (api_url or "").strip().rstrip("/")
    if "seu-projeto.vercel.app" in raw:
        return "", ""
    if not raw:
        base_url = DEFAULT_API_BASE_URL
    elif raw.endswith("/api/progresso"):
        base_url = raw[: -len("/api/progresso")]
    elif raw.endswith("/api/aluno"):
        base_url = raw[: -len("/api/aluno")]
    else:
        base_url = raw
    return f"{base_url}/api/aluno", f"{base_url}/api/progresso"


def gerar_token_hash(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


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
    payload = {
        "token_sha256": gerar_token_hash(token),
        "aluno_id": str(identidade["aluno_id"]),
        "nome": str(identidade["nome"]),
        "total_aulas_concluidas": int(identidade.get("total_aulas_concluidas") or 0),
        "aulas_concluidas": [str(a) for a in (identidade.get("aulas_concluidas") or [])],
    }
    cache_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )


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


def restaurar_progresso_local_se_ausente(
    identidade: dict, progresso_path: Path = PROGRESSO_PATH
) -> bool:
    """Restaura progresso.local.md apenas se ele ainda não existir localmente."""
    if progresso_path.exists():
        return False

    relatorio_md = str(identidade.get("relatorio_markdown") or "").strip()
    aulas = [str(a) for a in (identidade.get("aulas_concluidas") or []) if str(a).strip()]

    if relatorio_md:
        progresso_path.write_text(relatorio_md + "\n", encoding="utf-8")
        return True

    if aulas:
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
        progresso_path.write_text("\n".join(linhas), encoding="utf-8")
        return True

    return False


def identificar_aluno(env: dict, permitir_cache_offline: bool = True) -> dict:
    token = extrair_token_valido(env)
    if not token:
        raise ErroAutenticacao(
            "ALUNO_TOKEN ausente ou inválido em .aluno.env. Informe apenas o token da Diretoria."
        )

    aluno_url, _ = resolver_urls_api(env.get("PROFESSOR_API_URL", ""))
    motivo_falha = "PROFESSOR_API_URL não configurada"

    if aluno_url:
        try:
            identidade = buscar_identidade_remota(aluno_url, token)
            salvar_cache_identidade(token, identidade)
            restaurado = restaurar_progresso_local_se_ausente(identidade)
            identidade["origem"] = "supabase"
            identidade["progresso_restaurado"] = restaurado
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

        legacy_id = env.get("ALUNO_ID", "").strip()
        legacy_nome = env.get("ALUNO_NOME", "").strip()
        if legacy_id and legacy_nome:
            return {
                "aluno_id": legacy_id,
                "nome": legacy_nome,
                "total_aulas_concluidas": 0,
                "aulas_concluidas": [],
                "origem": "env_legado",
                "aviso": motivo_falha,
            }

    raise ErroConexao(
        f"Não foi possível conectar ao servidor ({motivo_falha}) para descobrir o nome do aluno a partir do token."
    )


def main():
    try:
        env = carregar_env()
    except FileNotFoundError:
        print("[ERRO] Arquivo .aluno.env não encontrado na raiz.")
        sys.exit(1)

    try:
        identidade = identificar_aluno(env, permitir_cache_offline=True)
    except (ErroAutenticacao, ErroConexao) as exc:
        print(f"[ERRO] {exc}")
        sys.exit(1)

    if identidade.get("origem") == "supabase":
        print("[OK] Aluno identificado com sucesso via Supabase.")
    else:
        print(
            f"[AVISO] Falha ao consultar servidor ({identidade.get('aviso')}). "
            f"Usando identidade local ({identidade.get('origem')})."
        )

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

    if identidade.get("progresso_restaurado"):
        print("[OK] progresso.local.md restaurado a partir do histórico na nuvem.")


if __name__ == "__main__":
    main()
