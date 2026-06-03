"""
Repositórios concretos — camada de Infra (SQLite via SQLAlchemy).

Implementam as interfaces do Domain sem vazar detalhes de ORM para cima.
"""
from __future__ import annotations
import json
from collections import defaultdict
from datetime import datetime
from typing import List, Optional

from sqlalchemy import func
from sqlalchemy.orm import Session

from config import settings
from domain.entities import Script, LogAuditoria
from domain.repositories import ScriptRepository, LogRepository, ConfigRepository
from .models import ScriptModel, LogAuditoriaModel, ConfigModel


# ── Mapeamento ORM → Entidade ──────────────────────────────────────

def _to_script(m: ScriptModel) -> Script:
    return Script(
        id=m.id,
        name=m.name,
        filename=m.filename,
        description=m.description or "",
        parameters_hint=m.parameters_hint or "",
        is_active=m.is_active,
        created_at=m.created_at or datetime.utcnow(),
    )


def _to_log(m: LogAuditoriaModel) -> LogAuditoria:
    return LogAuditoria(
        id=m.id,
        script_id=m.script_id,
        script_name=m.script_name,
        params=m.params or "[]",
        status=m.status,
        output=m.output or "",
        error=m.error or "",
        duration_ms=m.duration_ms or 0,
        executed_at=m.executed_at or datetime.utcnow(),
    )


# ── Script Repository ──────────────────────────────────────────────

class SQLiteScriptRepository(ScriptRepository):
    def __init__(self, db: Session):
        self._db = db

    def list_all(self) -> List[Script]:
        rows = self._db.query(ScriptModel).order_by(ScriptModel.id).all()
        return [_to_script(r) for r in rows]

    def find_by_id(self, script_id: int) -> Optional[Script]:
        row = self._db.get(ScriptModel, script_id)
        return _to_script(row) if row else None

    def save(self, script: Script) -> Script:
        model = ScriptModel(
            name=script.name,
            filename=script.filename,
            description=script.description,
            parameters_hint=script.parameters_hint,
            is_active=script.is_active,
            created_at=script.created_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return _to_script(model)

    def update(self, script: Script) -> Script:
        row = self._db.get(ScriptModel, script.id)
        if not row:
            raise ValueError(f"Script #{script.id} não encontrado para atualização.")
        row.name = script.name
        row.filename = script.filename
        row.description = script.description
        row.parameters_hint = script.parameters_hint
        row.is_active = script.is_active
        self._db.commit()
        self._db.refresh(row)
        return _to_script(row)

    def delete(self, script_id: int) -> bool:
        row = self._db.get(ScriptModel, script_id)
        if not row:
            return False
        self._db.delete(row)
        self._db.commit()
        return True


# ── Log Repository ─────────────────────────────────────────────────

class SQLiteLogRepository(LogRepository):
    def __init__(self, db: Session):
        self._db = db

    def save(self, log: LogAuditoria) -> LogAuditoria:
        model = LogAuditoriaModel(
            script_id=log.script_id,
            script_name=log.script_name,
            params=log.params,
            status=log.status,
            output=log.output,
            error=log.error,
            duration_ms=log.duration_ms,
            executed_at=log.executed_at,
        )
        self._db.add(model)
        self._db.commit()
        self._db.refresh(model)
        return _to_log(model)

    def list_all(self, limit: int = 100) -> List[LogAuditoria]:
        rows = (
            self._db.query(LogAuditoriaModel)
            .order_by(LogAuditoriaModel.executed_at.desc())
            .limit(limit)
            .all()
        )
        return [_to_log(r) for r in rows]

    def telemetry_summary(self) -> dict:
        total = self._db.query(func.count(LogAuditoriaModel.id)).scalar() or 0

        if total == 0:
            return {
                "summary": {
                    "total_executions": 0,
                    "success_count": 0,
                    "error_count": 0,
                    "timeout_count": 0,
                    "success_rate_pct": 0.0,
                    "avg_duration_ms": 0,
                },
                "scripts_ranking": [],
                "recent_history": [],
                "health_score": 0.0,
                "generated_at": datetime.utcnow().isoformat(),
                "context_for_llm": "IsyShell: nenhuma execução registrada ainda.",
            }

        # Contagens por status
        counts = (
            self._db.query(
                LogAuditoriaModel.status,
                func.count(LogAuditoriaModel.id).label("cnt"),
            )
            .group_by(LogAuditoriaModel.status)
            .all()
        )
        status_map = {r.status: r.cnt for r in counts}
        success  = status_map.get("success", 0)
        errors   = status_map.get("error", 0)
        timeouts = status_map.get("timeout", 0)
        avg_ms   = self._db.query(func.avg(LogAuditoriaModel.duration_ms)).scalar() or 0

        # Ranking de scripts (agregação em Python para máxima compatibilidade com SQLite)
        all_rows = self._db.query(
            LogAuditoriaModel.script_name,
            LogAuditoriaModel.status,
        ).all()

        script_stats: dict = defaultdict(lambda: {"total": 0, "success": 0})
        for row in all_rows:
            script_stats[row.script_name]["total"] += 1
            if row.status == "success":
                script_stats[row.script_name]["success"] += 1

        ranking = sorted(
            [
                {
                    "script_name": name,
                    "executions": st["total"],
                    "success_rate_pct": round(
                        st["success"] / st["total"] * 100, 2
                    ) if st["total"] > 0 else 0.0,
                }
                for name, st in script_stats.items()
            ],
            key=lambda x: x["executions"],
            reverse=True,
        )[:10]

        # Histórico recente (últimas 10 execuções)
        recent_rows = (
            self._db.query(LogAuditoriaModel)
            .order_by(LogAuditoriaModel.executed_at.desc())
            .limit(10)
            .all()
        )
        recent_history = []
        for r in recent_rows:
            try:
                params_list = json.loads(r.params or "[]")
                params_summary = " ".join(str(p) for p in params_list)
            except Exception:
                params_summary = r.params or ""
            recent_history.append({
                "id": r.id,
                "script_name": r.script_name,
                "status": r.status,
                "duration_ms": r.duration_ms,
                "params_summary": params_summary,
                "executed_at": r.executed_at.isoformat() if r.executed_at else None,
            })

        success_rate = round(success / total * 100, 2) if total > 0 else 0.0

        context = (
            f"IsyShell Infrastructure Orchestrator | "
            f"Telemetria gerada: {datetime.utcnow().isoformat()} | "
            f"Total execuções: {total} | "
            f"Taxa de sucesso: {success_rate}% | "
            f"Tempo médio de resposta: {round(avg_ms)}ms | "
            f"Erros: {errors} | Timeouts: {timeouts} | "
            f"Scripts mais utilizados: {', '.join(r['script_name'] for r in ranking[:3]) if ranking else 'nenhum'}."
        )

        return {
            "summary": {
                "total_executions": total,
                "success_count": success,
                "error_count": errors,
                "timeout_count": timeouts,
                "success_rate_pct": success_rate,
                "avg_duration_ms": round(avg_ms),
            },
            "scripts_ranking": ranking,
            "recent_history": recent_history,
            "health_score": success_rate,
            "generated_at": datetime.utcnow().isoformat(),
            "context_for_llm": context,
        }


# ── Config Repository ──────────────────────────────────────────────

class SQLiteConfigRepository(ConfigRepository):
    def __init__(self, db: Session):
        self._db = db

    def get_token(self) -> str:
        row = self._db.get(ConfigModel, "api_token")
        return row.value if row else settings.default_token

    def set_token(self, token: str) -> None:
        row = self._db.get(ConfigModel, "api_token")
        if row:
            row.value = token
        else:
            self._db.add(ConfigModel(key="api_token", value=token))
        self._db.commit()

    def get_system_info(self) -> dict:
        return {
            "version": settings.version,
            "runtime": "Python 3.11 + FastAPI",
            "database": "SQLite (SQLAlchemy)",
            "scripts_dir": settings.scripts_dir,
        }
