"""
IsyShell API — Ponto de entrada da aplicação FastAPI.

Responsabilidades:
- Criar tabelas no banco na inicialização (lifespan)
- Seed dos scripts e token padrão na primeira execução
- Registrar routers de cada módulo
- Configurar CORS para o frontend
- Servir o frontend estático (SPA) em produção
"""
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from config import settings
from infra.database import Base, SessionLocal, engine
from infra.models import ConfigModel, ScriptModel
from infra.routers import admin, ai_telemetry, execution, logs, scripts

# ── Dados iniciais ─────────────────────────────────────────────────

_SEED_SCRIPTS = [
    {
        "name": "Limpeza de Logs",
        "filename": "cleanup_logs.sh",
        "description": "Remove logs de cupons com mais de N dias do servidor do cliente.",
        "parameters_hint": "[cliente] [dias]",
        "is_active": True,
    },
    {
        "name": "Status dos Containers",
        "filename": "check_containers.sh",
        "description": "Verifica se os containers Docker de banco, app e proxy estão operacionais.",
        "parameters_hint": "[cliente]",
        "is_active": True,
    },
    {
        "name": "Provisionar Cliente",
        "filename": "provisionar.sh",
        "description": "Cria toda a estrutura de containers, Nginx e SSL para um novo cliente.",
        "parameters_hint": "[cliente] [dominio] [porta]",
        "is_active": True,
    },
    {
        "name": "Atualizar Agente iFood",
        "filename": "update_agent.sh",
        "description": "Atualiza o agente de impressão local do iFood para a versão mais recente.",
        "parameters_hint": "[cliente]",
        "is_active": False,
    },
]


def _seed_database(db) -> None:
    """Popula o banco com token e scripts padrão se ainda estiver vazio."""
    if not db.get(ConfigModel, "api_token"):
        db.add(ConfigModel(key="api_token", value=settings.default_token))

    if db.query(ScriptModel).count() == 0:
        for s in _SEED_SCRIPTS:
            db.add(ScriptModel(**s, created_at=datetime.utcnow()))

    db.commit()


# ── Lifespan (startup / shutdown) ──────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        _seed_database(db)
    finally:
        db.close()
    yield


# ── Aplicação ──────────────────────────────────────────────────────

app = FastAPI(
    title="IsyShell API",
    description=(
        "Orquestrador automático de infraestrutura — converte rotinas críticas de "
        "terminal (.sh) em uma API segura, auditável e conteinerizada.\n\n"
        "**FMU Tech Hackathon 2026**"
    ),
    version=settings.version,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ────────────────────────────────────────────────────────

app.include_router(scripts.router)
app.include_router(execution.router)
app.include_router(logs.router)
app.include_router(admin.router)
app.include_router(ai_telemetry.router)


# ── Health check (público, sem autenticação) ───────────────────────

@app.get("/health", tags=["Health"])
def health():
    return {
        "status": "ok",
        "version": settings.version,
        "runtime": "Python 3.11 + FastAPI",
        "database": "SQLite (SQLAlchemy)",
        "scripts_dir": settings.scripts_dir,
    }


# ── Servir frontend estático (SPA) ─────────────────────────────────
# Mapeado APÓS os routers para que as rotas de API tenham prioridade.
_frontend_dir = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.isfile(os.path.join(_frontend_dir, "index.html")):
    app.mount("/", StaticFiles(directory=_frontend_dir, html=True), name="frontend")
