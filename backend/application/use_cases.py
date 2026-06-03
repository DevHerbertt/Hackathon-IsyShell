"""
Camada de Aplicação — Casos de Uso (Application Layer).

Orquestra entidades do domínio e interfaces de repositório sem saber NADA
sobre FastAPI, SQLAlchemy ou subprocess. Regra do SOLID: SRP + DIP.
"""
from __future__ import annotations
import json
import os
from datetime import datetime
from typing import List, TYPE_CHECKING

from domain.entities import Script, LogAuditoria
from domain.repositories import ScriptRepository, LogRepository, ConfigRepository

if TYPE_CHECKING:
    from infra.script_executor import ScriptExecutor


# ── Exceções de domínio ────────────────────────────────────────────

class ScriptNotFoundError(Exception):
    def __init__(self, script_id: int):
        super().__init__(f"Script #{script_id} não encontrado.")


class ScriptInactiveError(Exception):
    def __init__(self, script_id: int):
        super().__init__(f"Script #{script_id} está inativo. Ative-o antes de executar.")


class TokenInvalidError(Exception):
    pass


# ── UC-01: Listar Scripts ──────────────────────────────────────────

class ListarScriptsUseCase:
    def __init__(self, repo: ScriptRepository):
        self._repo = repo

    def execute(self) -> List[Script]:
        return self._repo.list_all()


# ── UC-02: Criar Script ────────────────────────────────────────────

class CriarScriptUseCase:
    def __init__(self, repo: ScriptRepository):
        self._repo = repo

    def execute(self, script: Script) -> Script:
        return self._repo.save(script)


# ── UC-03: Atualizar Script ────────────────────────────────────────

class AtualizarScriptUseCase:
    def __init__(self, repo: ScriptRepository):
        self._repo = repo

    def execute(self, script_id: int, **kwargs) -> Script:
        script = self._repo.find_by_id(script_id)
        if not script:
            raise ScriptNotFoundError(script_id)
        for key, value in kwargs.items():
            if hasattr(script, key):
                setattr(script, key, value)
        return self._repo.update(script)


# ── UC-04: Remover Script ──────────────────────────────────────────

class RemoverScriptUseCase:
    def __init__(self, repo: ScriptRepository):
        self._repo = repo

    def execute(self, script_id: int) -> bool:
        if not self._repo.find_by_id(script_id):
            raise ScriptNotFoundError(script_id)
        return self._repo.delete(script_id)


# ── UC-05: Executar Script ─────────────────────────────────────────

class ExecutarScriptUseCase:
    """
    Ponto central de execução segura.
    Valida estado do script, delega ao executor de SO e persiste o log.
    """
    def __init__(
        self,
        script_repo: ScriptRepository,
        log_repo: LogRepository,
        executor: "ScriptExecutor",
        scripts_dir: str,
        timeout: int = 120,
    ):
        self._scripts = script_repo
        self._logs = log_repo
        self._executor = executor
        self._scripts_dir = scripts_dir
        self._timeout = timeout

    def execute(self, script_id: int, params: List[str]) -> LogAuditoria:
        script = self._scripts.find_by_id(script_id)
        if not script:
            raise ScriptNotFoundError(script_id)
        if not script.is_active:
            raise ScriptInactiveError(script_id)

        script_path = os.path.join(self._scripts_dir, script.filename)
        result = self._executor.run(script_path, params, self._timeout)

        log = LogAuditoria(
            script_id=script.id,
            script_name=script.name,
            params=json.dumps(params, ensure_ascii=False),
            status=result.status,
            output=result.stdout,
            error=result.stderr,
            duration_ms=result.duration_ms,
            executed_at=datetime.utcnow(),
        )
        return self._logs.save(log)


# ── UC-06: Alterar Token ───────────────────────────────────────────

class AlterarTokenUseCase:
    MIN_LENGTH = 16

    def __init__(self, repo: ConfigRepository):
        self._repo = repo

    def execute(self, new_token: str) -> None:
        if len(new_token) < self.MIN_LENGTH:
            raise TokenInvalidError(
                f"Token deve ter ao menos {self.MIN_LENGTH} caracteres."
            )
        self._repo.set_token(new_token)


# ── UC-07: Listar Logs ─────────────────────────────────────────────

class ListarLogsUseCase:
    def __init__(self, repo: LogRepository):
        self._repo = repo

    def execute(self, limit: int = 100) -> List[LogAuditoria]:
        return self._repo.list_all(limit)


# ── UC-08: Telemetria para IA ──────────────────────────────────────

class TelemetriaUseCase:
    def __init__(self, log_repo: LogRepository, config_repo: ConfigRepository):
        self._logs = log_repo
        self._config = config_repo

    def execute(self) -> dict:
        return self._logs.telemetry_summary()
