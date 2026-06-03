from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from config import settings

engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},
)


@event.listens_for(engine, "connect")
def _configure_sqlite(dbapi_conn, _):
    """Ativa WAL mode e foreign keys a cada nova conexão SQLite."""
    dbapi_conn.execute("PRAGMA journal_mode=WAL")
    dbapi_conn.execute("PRAGMA foreign_keys=ON")


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI dependency — sessão de banco por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
