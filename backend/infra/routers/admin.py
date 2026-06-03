from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from application.use_cases import AlterarTokenUseCase, TokenInvalidError
from infra.deps import get_alterar_token, get_config_repo
from infra.repositories import SQLiteConfigRepository
from infra.security import verify_token

router = APIRouter(prefix="/api/v1/admin", tags=["Administração"])


class TokenIn(BaseModel):
    token: str


class TokenOut(BaseModel):
    message: str


@router.put("/token", response_model=TokenOut)
def alterar_token(
    body: TokenIn,
    _: str = Depends(verify_token),
    use_case: AlterarTokenUseCase = Depends(get_alterar_token),
):
    """
    Altera dinamicamente o token de autenticação da API.
    O novo token passa a valer imediatamente, sem restart do serviço.
    Mínimo de 16 caracteres obrigatório.
    """
    try:
        use_case.execute(body.token)
        return {"message": "Token atualizado com sucesso."}
    except TokenInvalidError as exc:
        raise HTTPException(status_code=400, detail=str(exc))


@router.get("/info")
def info_sistema(
    _: str = Depends(verify_token),
    config_repo: SQLiteConfigRepository = Depends(get_config_repo),
):
    """Retorna metadados do sistema (versão, runtime, diretório de scripts)."""
    return config_repo.get_system_info()
