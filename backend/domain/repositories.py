from __future__ import annotations
from abc import ABC, abstractmethod
from typing import List, Optional

from .entities import Script, LogAuditoria


class ScriptRepository(ABC):
    """Interface de repositório para Scripts — inversão de dependência (DIP)."""

    @abstractmethod
    def list_all(self) -> List[Script]: ...

    @abstractmethod
    def find_by_id(self, script_id: int) -> Optional[Script]: ...

    @abstractmethod
    def save(self, script: Script) -> Script: ...

    @abstractmethod
    def update(self, script: Script) -> Script: ...

    @abstractmethod
    def delete(self, script_id: int) -> bool: ...


class LogRepository(ABC):
    """Interface de repositório para Logs de Auditoria."""

    @abstractmethod
    def save(self, log: LogAuditoria) -> LogAuditoria: ...

    @abstractmethod
    def list_all(self, limit: int = 100) -> List[LogAuditoria]: ...

    @abstractmethod
    def telemetry_summary(self) -> dict: ...


class ConfigRepository(ABC):
    """Interface de repositório para configurações dinâmicas (token, info)."""

    @abstractmethod
    def get_token(self) -> str: ...

    @abstractmethod
    def set_token(self, token: str) -> None: ...

    @abstractmethod
    def get_system_info(self) -> dict: ...
