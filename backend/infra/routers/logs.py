from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel

from application.use_cases import ListarLogsUseCase
from infra.deps import get_listar_logs
from infra.security import verify_token

router = APIRouter(prefix="/api/v1/logs", tags=["Auditoria"])


class LogOut(BaseModel):
    id: int
    script_id: int
    script_name: str
    params: str
    status: str
    output: str
    error: str
    duration_ms: int
    executed_at: datetime


@router.get("", response_model=List[LogOut])
def listar_logs(
    limit: int = Query(100, ge=1, le=1000, description="Número máximo de registros"),
    _: str = Depends(verify_token),
    use_case: ListarLogsUseCase = Depends(get_listar_logs),
):
    """Retorna o histórico de auditoria das execuções (ordem cronológica inversa)."""
    return [LogOut(**log.__dict__) for log in use_case.execute(limit=limit)]
