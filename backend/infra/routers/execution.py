from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from application.use_cases import (
    ExecutarScriptUseCase,
    ScriptInactiveError,
    ScriptNotFoundError,
)
from infra.deps import get_executar_script
from infra.security import sanitize_params, verify_token

router = APIRouter(tags=["Execução"])


# ── Schemas ────────────────────────────────────────────────────────

class ExecuteIn(BaseModel):
    params: List[str] = []


class MaintenanceExecuteIn(BaseModel):
    """Schema alternativo para compatibilidade com a spec do hackathon."""
    script_id: int
    params: List[str] = []


class ExecuteOut(BaseModel):
    id: int
    script_name: str
    status: str
    output: str
    error: str
    duration_ms: int
    executed_at: datetime


# ── Lógica interna compartilhada ───────────────────────────────────

def _do_execute(
    script_id: int,
    params: List[str],
    use_case: ExecutarScriptUseCase,
) -> ExecuteOut:
    try:
        clean = sanitize_params(params)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    try:
        log = use_case.execute(script_id, clean)
    except ScriptNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ScriptInactiveError as exc:
        raise HTTPException(status_code=422, detail=str(exc))

    return ExecuteOut(
        id=log.id,
        script_name=log.script_name,
        status=log.status,
        output=log.output,
        error=log.error,
        duration_ms=log.duration_ms,
        executed_at=log.executed_at,
    )


# ── Endpoints ──────────────────────────────────────────────────────

@router.post("/api/v1/scripts/{script_id}/execute", response_model=ExecuteOut)
def executar_por_id(
    script_id: int,
    body: ExecuteIn,
    _: str = Depends(verify_token),
    use_case: ExecutarScriptUseCase = Depends(get_executar_script),
):
    """Executa um script pelo ID (rota principal — usada pelo frontend)."""
    return _do_execute(script_id, body.params, use_case)


@router.post("/api/v1/maintenance/execute", response_model=ExecuteOut)
def executar_manutencao(
    body: MaintenanceExecuteIn,
    _: str = Depends(verify_token),
    use_case: ExecutarScriptUseCase = Depends(get_executar_script),
):
    """Executa um script pelo ID no corpo da requisição (rota spec hackathon)."""
    return _do_execute(body.script_id, body.params, use_case)
