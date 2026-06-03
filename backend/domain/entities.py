from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class Script:
    """Entidade de domínio que representa um script de manutenção registrado."""
    name: str
    filename: str
    description: str
    parameters_hint: str
    is_active: bool
    id: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class LogAuditoria:
    """Entidade de domínio que representa o registro imutável de uma execução."""
    script_id: int
    script_name: str
    params: str        # JSON-encoded list: '["cliente", "30"]'
    status: str        # "success" | "error" | "timeout"
    output: str        # stdout capturado
    error: str         # stderr capturado
    duration_ms: int   # tempo de execução em milissegundos
    id: Optional[int] = None
    executed_at: datetime = field(default_factory=datetime.utcnow)
