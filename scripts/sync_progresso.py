import base64
import hashlib
import hmac
import json
import os
import re
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from identificar_aluno import (  # noqa: E402
    PENDING_PATH,
    PROGRESSO_PATH,
    SESSION_PATH,
    USER_AGENT,
    ErroAutenticacao,
    ErroConexao,
    calcular_hash_integridade_cliente,
    carregar_env,
    extrair_aulas_concluidas_md,
    extrair_erro_http,
    extrair_token_valido,
    identificar_aluno,
    ler_cache_identidade,
    ler_sessao_local,
    resolver_urls_api,
    salvar_cache_identidade,
)

PUB_KEY_PATH = SCRIPTS_DIR / "public_key.pem"


def cifrar_conteudo(texto: str) -> dict:
    raw = texto.encode("utf-8")
    if PUB_KEY_PATH.exists():
        try:
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import padding
            from cryptography.hazmat.primitives.ciphers.aead import AESGCM

            pub_key = serialization.load_pem_public_key(PUB_KEY_PATH.read_bytes())
            aes_key = os.urandom(32)
            nonce = os.urandom(12)
            ciphertext = AESGCM(aes_key).encrypt(nonce, raw, None)
            enc_key = pub_key.encrypt(
                aes_key,
                padding.OAEP(
                    mgf=padding.MGF1(algorithm=hashes.SHA256()),
                    algorithm=hashes.SHA256(),
                    label=None,
                ),
            )
            return {
                "modo": "rsa_aes256_gcm",
                "chave_cifrada": base64.b64encode(enc_key).decode("ascii"),
                "nonce": base64.b64encode(nonce).decode("ascii"),
                "dados": base64.b64encode(ciphertext).decode("ascii"),
            }
        except ImportError:
            pass

    return {
        "modo": "tls_base64",
        "dados": base64.b64encode(raw).decode("ascii"),
    }


def extrair_bloco_aula_detalhado(md_text: str, aula_caminho: str) -> Dict[str, str]:
    """Extrai timestamp, percentual de acerto e parecer comportamental apenas da aula atual."""
    pattern_header = re.compile(
        rf"^###\s+`?{re.escape(aula_caminho)}`?\s*$", re.MULTILINE
    )
    match = pattern_header.search(md_text)
    if match:
        start = match.start()
        next_heading = re.search(r"^###\s+", md_text[match.end():], re.MULTILINE)
        end = match.end() + next_heading.start() if next_heading else len(md_text)
        bloco = md_text[start:end].strip()
    else:
        bloco = ""

    ts_match = re.search(
        r"\*\*Data/Hora UTC:\*\*\s*([^\r\n]+)", bloco
    )
    pct_match = re.search(
        r"\*\*Percentual de Acerto:\*\*\s*([^\r\n]+)", bloco
    )
    parecer_match = re.search(
        r"\*\*Parecer Comportamental Objetivo:\*\*\s*(.+?)(?=\n- \*\*|\n### |\Z)",
        bloco,
        re.DOTALL,
    )

    percentual_acerto = pct_match.group(1).strip() if pct_match else ""
    if not percentual_acerto:
        mapa_match = re.search(
            rf"`?{re.escape(aula_caminho)}`?[^\r\n]*Acerto:\s*([^)\r\n]+)",
            md_text,
        )
        if mapa_match:
            percentual_acerto = mapa_match.group(1).strip()

    timestamp_utc = (
        ts_match.group(1).strip()
        if ts_match
        else datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    )
    parecer = parecer_match.group(1).strip() if parecer_match else ""

    if not parecer:
        raise ValueError(
            f"Bloco detalhado ou 'Parecer Comportamental Objetivo' ausente para '{aula_caminho}' em progresso.local.md."
        )

    return {
        "aula_concluida": aula_caminho,
        "timestamp_utc": timestamp_utc,
        "percentual_acerto": percentual_acerto or "Não informado",
        "parecer_comportamental": parecer,
        "registro_markdown": bloco,
    }


def _resolver_identidade_atual(env: dict, aluno_token: str) -> dict:
    cache = ler_cache_identidade(aluno_token)
    if cache:
        return cache
    return identificar_aluno(env, permitir_cache_offline=False)


def main():
    try:
        env = carregar_env()
    except FileNotFoundError:
        print("[ERRO] Arquivo .aluno.env não encontrado na raiz.")
        sys.exit(1)

    aluno_token = extrair_token_valido(env)
    if not aluno_token:
        print("[ERRO] ALUNO_TOKEN inválido ou ausente em .aluno.env.")
        sys.exit(1)

    _, api_url, _ = resolver_urls_api(env.get("PROFESSOR_API_URL", ""))

    if PENDING_PATH.exists():
        body_bytes = PENDING_PATH.read_bytes()
        try:
            pending_data = json.loads(body_bytes.decode("utf-8"))
            aula_concluida = str(pending_data.get("aula_concluida") or "")
            aluno_id = str(pending_data.get("aluno_id") or "")
        except Exception:
            print("[ERRO] Arquivo progresso.pending.json corrompido.")
            sys.exit(1)
        if not aula_concluida or not pending_data.get("session_nonce"):
            print(
                "[ERRO] progresso.pending.json está em formato legado incompatível. "
                "Remova progresso.pending.json e execute python scripts/identificar_aluno.py."
            )
            sys.exit(1)
    else:
        sessao = ler_sessao_local(aluno_token)
        if not sessao:
            print(
                "[ERRO] Nenhuma sessão de aula ativa encontrada (.aula.session.json). "
                "Execute 'python scripts/identificar_aluno.py' no início da aula."
            )
            sys.exit(1)

        if not PROGRESSO_PATH.exists():
            print("[ERRO] Arquivo progresso.local.md não encontrado.")
            sys.exit(1)

        try:
            identidade = _resolver_identidade_atual(env, aluno_token)
        except (ErroAutenticacao, ErroConexao) as exc:
            print(f"[ERRO] {exc}")
            sys.exit(1)

        aluno_id = str(identidade["aluno_id"])
        aluno_nome = str(identidade["nome"])
        aulas_nuvem = {
            str(a).strip() for a in (identidade.get("aulas_concluidas") or []) if str(a).strip()
        }

        conteudo_md = PROGRESSO_PATH.read_text(encoding="utf-8")
        aulas_locais = extrair_aulas_concluidas_md(conteudo_md)
        aulas_novas = [a for a in aulas_locais if a not in aulas_nuvem]

        if not aulas_novas:
            print("[ERRO] Nenhuma nova aula concluída encontrada em progresso.local.md.")
            sys.exit(1)

        if len(aulas_novas) > 1:
            print(
                "[ERRO] Bloqueado: mais de 1 aula nova detectada em progresso.local.md "
                f"({len(aulas_novas)} aulas). Apenas 1 aula por sessão é permitida."
            )
            sys.exit(1)

        aula_concluida = aulas_novas[0]
        if aula_concluida != sessao["aula_caminho"]:
            print(
                f"[ERRO] Bloqueado: a aula '{aula_concluida}' diverge da aula obrigatória "
                f"da sessão atual ('{sessao['aula_caminho']}')."
            )
            sys.exit(1)

        try:
            dados_bloco = extrair_bloco_aula_detalhado(conteudo_md, aula_concluida)
        except ValueError as exc:
            print(f"[ERRO] {exc}")
            sys.exit(1)

        payload = {
            "aluno_id": aluno_id,
            "aluno_nome": aluno_nome,
            "aula_concluida": aula_concluida,
            "session_nonce": sessao["session_nonce"],
            "timestamp_utc": dados_bloco["timestamp_utc"],
            "client_integrity_hash": calcular_hash_integridade_cliente(),
            "relatorio_criptografado": cifrar_conteudo(
                json.dumps(dados_bloco, ensure_ascii=False)
            ),
        }
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")

    assinatura = hmac.new(
        aluno_token.encode("utf-8"), body_bytes, hashlib.sha256
    ).hexdigest()

    if not api_url:
        PENDING_PATH.write_bytes(body_bytes)
        print(
            "[AVISO] PROFESSOR_API_URL não configurada. Relatório incremental salvo em progresso.pending.json."
        )
        sys.exit(0)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        "X-Aluno-Signature": assinatura,
        "X-Aluno-Token": aluno_token,
    }
    if aluno_id:
        headers["X-Aluno-ID"] = aluno_id

    req = urllib.request.Request(
        api_url,
        data=body_bytes,
        method="POST",
        headers=headers,
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            resp_raw = resp.read().decode("utf-8", errors="replace").strip()
            if 200 <= resp.status < 300:
                if PENDING_PATH.exists():
                    PENDING_PATH.unlink()
                if SESSION_PATH.exists():
                    SESSION_PATH.unlink()

                total_registradas = None
                if resp_raw:
                    try:
                        resp_json = json.loads(resp_raw)
                        total_registradas = resp_json.get("total_aulas_concluidas")
                    except Exception:
                        pass

                cache = ler_cache_identidade(aluno_token)
                if cache:
                    aulas_cache = list(cache.get("aulas_concluidas") or [])
                    if aula_concluida not in aulas_cache:
                        aulas_cache.append(aula_concluida)
                    cache["aulas_concluidas"] = aulas_cache
                    cache["total_aulas_concluidas"] = (
                        total_registradas
                        if isinstance(total_registradas, int)
                        else len(aulas_cache)
                    )
                    salvar_cache_identidade(aluno_token, cache)

                total_msg = (
                    f"{total_registradas} aulas registradas"
                    if total_registradas is not None
                    else "progresso atualizado"
                )
                print(
                    f"[OK] Aula '{aula_concluida}' sincronizada com sucesso ({total_msg})."
                )
            else:
                PENDING_PATH.write_bytes(body_bytes)
                print(
                    f"[AVISO] Resposta inesperada ({resp.status}). Salvo em progresso.pending.json."
                )
    except urllib.error.HTTPError as exc:
        msg = extrair_erro_http(exc)
        if exc.code in (400, 401, 403, 409, 429):
            print(f"[ERRO] Envio rejeitado pelo servidor (HTTP {exc.code}): {msg}")
            sys.exit(1)
        PENDING_PATH.write_bytes(body_bytes)
        print(
            f"[AVISO] Erro no servidor (HTTP {exc.code}: {msg}). Salvo em progresso.pending.json para reenvio."
        )
    except urllib.error.URLError as exc:
        PENDING_PATH.write_bytes(body_bytes)
        print(
            f"[AVISO] Falha de conexão ({exc.reason}). Salvo em progresso.pending.json para reenvio."
        )


if __name__ == "__main__":
    main()
