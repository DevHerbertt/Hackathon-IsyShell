from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from .database import Base


class ScriptModel(Base):
    __tablename__ = "scripts"

    id              = Column(Integer, primary_key=True, index=True)
    name            = Column(String(100), nullable=False)
    filename        = Column(String(255), nullable=False, unique=True)
    description     = Column(Text, default="")
    parameters_hint = Column(String(255), default="")
    is_active       = Column(Boolean, default=True, nullable=False)
    created_at      = Column(DateTime, default=datetime.utcnow)


class LogAuditoriaModel(Base):
    __tablename__ = "logs_auditoria"

    id          = Column(Integer, primary_key=True, index=True)
    script_id   = Column(Integer, nullable=False)
    script_name = Column(String(100), nullable=False)
    params      = Column(Text, default="[]")        # JSON array serializado
    status      = Column(String(20), nullable=False) # success | error | timeout
    output      = Column(Text, default="")           # stdout
    error       = Column(Text, default="")           # stderr
    duration_ms = Column(Integer, default=0)
    executed_at = Column(DateTime, default=datetime.utcnow, index=True)


class ConfigModel(Base):
    """Tabela chave-valor para configurações dinâmicas (token, etc.)."""
    __tablename__ = "config"

    key   = Column(String(100), primary_key=True)
    value = Column(Text, nullable=False)
