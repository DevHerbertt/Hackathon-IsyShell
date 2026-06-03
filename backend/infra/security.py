"""
Segurança — camada de Infra.

Dois mecanismos independentes:
1. verify_token  — FastAPI Dependency que valida X-Isy-Token contra o BD.
2. sanitize_params — Proteção contra Command Injection via allowlist rígida.
"""
from __future__ import annotations
import re

from fastapi import Depends, Header, HTTPException
from sqlalchemy.orm import Session

from .database import get_db
from .repositories import SQLiteConfigRepository

# ── Allowlist de parâmetros ────────────────────────────────────────
# Permite: alfanumérico, underscore, hífen, ponto, barra, @, dois-pontos
# Bloqueia: ; & | > < $ ` ' " ( ) { } [ ] ! # ~ * \ espaço e outros metacaracteres de shell
_SAFE_PARAM_RE = re.compile(r'^[a-zA-Z0-9_\-\./@:]{1,255}$')


def sanitize_params(params: list[str]) -> list[str]:
    """
    Valida cada parâmetro contra a allowlist.
    Lança ValueError com descrição do problema se detectar caractere suspeito.
    """
    sanitized: list[str] = []
    for p in params:
        if not _SAFE_PARAM_RE.match(p):
            safe_preview = p[:40].replace("<", "").replace(">", "")
            raise ValueError(
                f"Parâmetro inválido detectado: '{safe_preview}'. "
                "Apenas [a-zA-Z0-9_\\-./@ :] são permitidos. "
                "Possível tentativa de Command Injection bloqueada."
            )
        sanitized.append(p)
    return sanitized


# ── Validação de Token ─────────────────────────────────────────────

def verify_token(
    x_isy_token: str = Header(..., alias="X-Isy-Token"),
    db: Session = Depends(get_db),
) -> str:
    """
    FastAPI Dependency — valida o header X-Isy-Token contra o token armazenado no BD.
    O token é dinâmico: pode ser trocado via PUT /api/v1/admin/token sem restart.
    """
    config_repo = SQLiteConfigRepository(db)
    expected = config_repo.get_token()
    if x_isy_token != expected:
        raise HTTPException(
            status_code=401,
            detail="Token de autenticação inválido. Verifique o header X-Isy-Token.",
        )
    return x_isy_token
