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
from typing import Tuple

SCRIPTS_DIR = Path(__file__).resolve().parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from identificar_aluno import (  # noqa: E402
    PROGRESSO_PATH,
    ROOT_DIR,
    USER_AGENT,
    ErroAutenticacao,
    ErroConexao,
    carregar_env,
    extrair_erro_http,
    extrair_token_valido,
    identificar_aluno,
    ler_cache_identidade,
    resolver_urls_api,
    salvar_cache_identidade,
)

PENDING_PATH = ROOT_DIR / "progresso.pending.json"
PUB_KEY_PATH = SCRIPTS_DIR / "public_key.pem"


def extrair_aulas_concluidas(md_text: str) -> list:
    return sorted(
        set(re.findall(r"`?([0-9]{2}-[^/`\s]+/[0-9]{2}-[^`\s]+\.md)`?", md_text))
    )


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


def resolver_identidade_para_sync(env: dict, aluno_token: str) -> Tuple[str, str]:
    cache = ler_cache_identidade(aluno_token)
    if cache:
        return str(cache["aluno_id"]), str(cache["nome"])

    try:
        identidade = identificar_aluno(env, permitir_cache_offline=True)
        return str(identidade["aluno_id"]), str(identidade["nome"])
    except ErroConexao:
        return "", ""


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

    try:
        aluno_id, aluno_nome = resolver_identidade_para_sync(env, aluno_token)
    except ErroAutenticacao as exc:
        print(f"[ERRO] {exc}")
        sys.exit(1)

    _, api_url = resolver_urls_api(env.get("PROFESSOR_API_URL", ""))

    if PROGRESSO_PATH.exists():
        conteudo_md = PROGRESSO_PATH.read_text(encoding="utf-8")
        aulas_concluidas = extrair_aulas_concluidas(conteudo_md)
        timestamp = datetime.now(timezone.utc).isoformat()

        payload = {
            "aluno_id": aluno_id or "pendente_resolucao_por_token",
            "aluno_nome": aluno_nome or aluno_id or "Aluno",
            "timestamp_utc": timestamp,
            "total_aulas_concluidas": len(aulas_concluidas),
            "aulas_concluidas": aulas_concluidas,
            "relatorio_criptografado": cifrar_conteudo(conteudo_md),
        }
        body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        total_aulas = len(aulas_concluidas)
    elif PENDING_PATH.exists():
        body_bytes = PENDING_PATH.read_bytes()
        try:
            pending_data = json.loads(body_bytes.decode("utf-8"))
            total_aulas = int(pending_data.get("total_aulas_concluidas") or 0)
        except Exception:
            total_aulas = 0
    else:
        print("[ERRO] Arquivo progresso.local.md não encontrado.")
        sys.exit(1)

    assinatura = hmac.new(
        aluno_token.encode("utf-8"), body_bytes, hashlib.sha256
    ).hexdigest()

    if not api_url:
        PENDING_PATH.write_bytes(body_bytes)
        print(
            "[AVISO] PROFESSOR_API_URL ainda não configurada. Relatório salvo localmente em progresso.pending.json."
        )
        sys.exit(0)

    headers = {
        "Content-Type": "application/json",
        "Accept": "application/json",
        "User-Agent": USER_AGENT,
        "X-Aluno-Signature": assinatura,
    }
    if aluno_id:
        headers["X-Aluno-ID"] = aluno_id
    else:
        headers["X-Aluno-Token"] = aluno_token

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
                if not aluno_id and resp_raw:
                    try:
                        resp_json = json.loads(resp_raw)
                        if resp_json.get("aluno_id") and resp_json.get("nome"):
                            salvar_cache_identidade(aluno_token, resp_json)
                    except Exception:
                        pass
                print(
                    f"[OK] Progresso sincronizado com sucesso ({total_aulas} aulas registradas)."
                )
            else:
                PENDING_PATH.write_bytes(body_bytes)
                print(
                    f"[AVISO] Resposta inesperada ({resp.status}). Salvo em progresso.pending.json."
                )
    except urllib.error.HTTPError as exc:
        msg = extrair_erro_http(exc)
        if exc.code in (400, 401, 403):
            print(f"[ERRO] Envio rejeitado pelo servidor (HTTP {exc.code}): {msg}")
            sys.exit(1)
        PENDING_PATH.write_bytes(body_bytes)
        print(
            f"[AVISO] Erro no servidor (HTTP {exc.code}: {msg}). Progresso salvo em progresso.pending.json para reenvio."
        )
    except urllib.error.URLError as exc:
        PENDING_PATH.write_bytes(body_bytes)
        print(
            f"[AVISO] Falha de conexão ({exc.reason}). Progresso salvo em progresso.pending.json para reenvio."
        )


if __name__ == "__main__":
    main()
