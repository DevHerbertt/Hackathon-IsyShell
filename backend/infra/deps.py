"""
Injeção de Dependência — camada de Infra.

Fábricas de Use Cases para uso com FastAPI Depends().
Cada request recebe instâncias frescas com a sessão de DB correta.
"""
from fastapi import Depends
from sqlalchemy.orm import Session

from application.use_cases import (
    AlterarTokenUseCase,
    AtualizarScriptUseCase,
    CriarScriptUseCase,
    ExecutarScriptUseCase,
    ListarLogsUseCase,
    ListarScriptsUseCase,
    RemoverScriptUseCase,
    TelemetriaUseCase,
)
from config import settings
from .database import get_db
from .repositories import SQLiteConfigRepository, SQLiteLogRepository, SQLiteScriptRepository
from .script_executor import ScriptExecutor


# ── Repositórios ───────────────────────────────────────────────────

def get_script_repo(db: Session = Depends(get_db)) -> SQLiteScriptRepository:
    return SQLiteScriptRepository(db)


def get_log_repo(db: Session = Depends(get_db)) -> SQLiteLogRepository:
    return SQLiteLogRepository(db)


def get_config_repo(db: Session = Depends(get_db)) -> SQLiteConfigRepository:
    return SQLiteConfigRepository(db)


def get_executor() -> ScriptExecutor:
    return ScriptExecutor()


# ── Fábricas de Use Cases ──────────────────────────────────────────

def get_listar_scripts(
    repo: SQLiteScriptRepository = Depends(get_script_repo),
) -> ListarScriptsUseCase:
    return ListarScriptsUseCase(repo)


def get_criar_script(
    repo: SQLiteScriptRepository = Depends(get_script_repo),
) -> CriarScriptUseCase:
    return CriarScriptUseCase(repo)


def get_atualizar_script(
    repo: SQLiteScriptRepository = Depends(get_script_repo),
) -> AtualizarScriptUseCase:
    return AtualizarScriptUseCase(repo)


def get_remover_script(
    repo: SQLiteScriptRepository = Depends(get_script_repo),
) -> RemoverScriptUseCase:
    return RemoverScriptUseCase(repo)


def get_executar_script(
    script_repo: SQLiteScriptRepository = Depends(get_script_repo),
    log_repo: SQLiteLogRepository = Depends(get_log_repo),
    executor: ScriptExecutor = Depends(get_executor),
) -> ExecutarScriptUseCase:
    return ExecutarScriptUseCase(
        script_repo=script_repo,
        log_repo=log_repo,
        executor=executor,
        scripts_dir=settings.scripts_dir,
        timeout=settings.execution_timeout,
    )


def get_alterar_token(
    repo: SQLiteConfigRepository = Depends(get_config_repo),
) -> AlterarTokenUseCase:
    return AlterarTokenUseCase(repo)


def get_listar_logs(
    repo: SQLiteLogRepository = Depends(get_log_repo),
) -> ListarLogsUseCase:
    return ListarLogsUseCase(repo)


def get_telemetria(
    log_repo: SQLiteLogRepository = Depends(get_log_repo),
    config_repo: SQLiteConfigRepository = Depends(get_config_repo),
) -> TelemetriaUseCase:
    return TelemetriaUseCase(log_repo, config_repo)
