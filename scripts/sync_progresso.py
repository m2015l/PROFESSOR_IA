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

ROOT_DIR = Path(__file__).resolve().parent.parent
ENV_PATH = ROOT_DIR / ".aluno.env"
PROGRESSO_PATH = ROOT_DIR / "progresso.local.md"
PENDING_PATH = ROOT_DIR / "progresso.pending.json"
PUB_KEY_PATH = ROOT_DIR / "scripts" / "public_key.pem"


def carregar_env() -> dict:
    if not ENV_PATH.exists():
        print("[ERRO] Arquivo .aluno.env não encontrado na raiz.")
        sys.exit(1)
    env = {}
    for line in ENV_PATH.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def extrair_aulas_concluidas(md_text: str) -> list:
    return sorted(set(re.findall(r"`([0-9]{2}-[^/`]+/[0-9]{2}-[^`]+\.md)`", md_text)))


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


def main():
    env = carregar_env()
    aluno_id = env.get("ALUNO_ID", "")
    aluno_token = env.get("ALUNO_TOKEN", "")
    api_url = env.get("PROFESSOR_API_URL", "")

    if not aluno_id or not aluno_token or "substitua" in aluno_token:
        print("[ERRO] ALUNO_ID ou ALUNO_TOKEN inválidos em .aluno.env.")
        sys.exit(1)

    if not PROGRESSO_PATH.exists():
        print("[ERRO] Arquivo progresso.local.md não encontrado.")
        sys.exit(1)

    conteudo_md = PROGRESSO_PATH.read_text(encoding="utf-8")
    aulas_concluidas = extrair_aulas_concluidas(conteudo_md)
    timestamp = datetime.now(timezone.utc).isoformat()

    payload = {
        "aluno_id": aluno_id,
        "aluno_nome": env.get("ALUNO_NOME", aluno_id),
        "timestamp_utc": timestamp,
        "total_aulas_concluidas": len(aulas_concluidas),
        "aulas_concluidas": aulas_concluidas,
        "relatorio_criptografado": cifrar_conteudo(conteudo_md),
    }

    body_bytes = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    assinatura = hmac.new(aluno_token.encode("utf-8"), body_bytes, hashlib.sha256).hexdigest()

    if not api_url or "seu-projeto.vercel.app" in api_url:
        PENDING_PATH.write_bytes(body_bytes)
        print("[AVISO] PROFESSOR_API_URL ainda não configurada. Relatório salvo localmente em progresso.pending.json.")
        sys.exit(0)

    req = urllib.request.Request(
        api_url,
        data=body_bytes,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "X-Aluno-ID": aluno_id,
            "X-Aluno-Signature": assinatura,
        },
    )

    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            if 200 <= resp.status < 300:
                if PENDING_PATH.exists():
                    PENDING_PATH.unlink()
                print(f"[OK] Progresso sincronizado com sucesso ({len(aulas_concluidas)} aulas registradas).")
            else:
                PENDING_PATH.write_bytes(body_bytes)
                print(f"[AVISO] Resposta inesperada ({resp.status}). Salvo em progresso.pending.json.")
    except urllib.error.URLError as exc:
        PENDING_PATH.write_bytes(body_bytes)
        print(f"[AVISO] Falha de conexão ({exc.reason}). Progresso salvo em progresso.pending.json para reenvio.")


if __name__ == "__main__":
    main()
