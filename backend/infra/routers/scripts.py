from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from application.use_cases import (
    AtualizarScriptUseCase,
    CriarScriptUseCase,
    ListarScriptsUseCase,
    RemoverScriptUseCase,
    ScriptNotFoundError,
)
from domain.entities import Script
from infra.deps import (
    get_atualizar_script,
    get_criar_script,
    get_listar_scripts,
    get_remover_script,
)
from infra.security import verify_token

router = APIRouter(prefix="/api/v1/scripts", tags=["Scripts"])


# ── Schemas ────────────────────────────────────────────────────────

class ScriptIn(BaseModel):
    name: str
    filename: str
    description: str = ""
    parameters_hint: str = ""
    is_active: bool = True


class ScriptPatch(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    parameters_hint: Optional[str] = None
    is_active: Optional[bool] = None


class ScriptOut(BaseModel):
    id: int
    name: str
    filename: str
    description: str
    parameters_hint: str
    is_active: bool
    created_at: datetime

    model_config = {"from_attributes": True}


# ── Endpoints ──────────────────────────────────────────────────────

@router.get("", response_model=List[ScriptOut])
def listar_scripts(
    _: str = Depends(verify_token),
    use_case: ListarScriptsUseCase = Depends(get_listar_scripts),
):
    """Retorna todos os scripts cadastrados (ativos e inativos)."""
    return [ScriptOut(**s.__dict__) for s in use_case.execute()]


@router.post("", response_model=ScriptOut, status_code=201)
def criar_script(
    body: ScriptIn,
    _: str = Depends(verify_token),
    use_case: CriarScriptUseCase = Depends(get_criar_script),
):
    """Cadastra um novo script de manutenção."""
    script = Script(
        name=body.name,
        filename=body.filename,
        description=body.description,
        parameters_hint=body.parameters_hint,
        is_active=body.is_active,
    )
    return ScriptOut(**use_case.execute(script).__dict__)


@router.patch("/{script_id}", response_model=ScriptOut)
def atualizar_script(
    script_id: int,
    body: ScriptPatch,
    _: str = Depends(verify_token),
    use_case: AtualizarScriptUseCase = Depends(get_atualizar_script),
):
    """Atualiza campos de um script (ex.: ativar/desativar)."""
    try:
        updated = use_case.execute(script_id, **body.model_dump(exclude_none=True))
        return ScriptOut(**updated.__dict__)
    except ScriptNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.delete("/{script_id}", status_code=204)
def remover_script(
    script_id: int,
    _: str = Depends(verify_token),
    use_case: RemoverScriptUseCase = Depends(get_remover_script),
):
    """Remove permanentemente um script cadastrado."""
    try:
        use_case.execute(script_id)
    except ScriptNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
