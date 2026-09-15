from typing import Generator, Dict, Any
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.ext.compiler import compiles
from geoalchemy2 import Geometry
from app.core.config import settings
from app.core.logging import logger

# SQLite Compatibility: map PostGIS Geometry type to BLOB on SQLite engines
@compiles(Geometry, "sqlite")
def compile_geometry_sqlite(element, compiler, **kw):
    return "BLOB"


# Connect args (e.g. check_same_thread for sqlite)
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=False,
    connect_args=connect_args,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db() -> Generator[Session, None, None]:
    """FastAPI dependency yielding a database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_health() -> Dict[str, Any]:
    """Execute a simple query to verify database connectivity."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return {"connected": True, "status": "healthy"}
    except Exception as exc:
        logger.warning(f"Database health check failed: {exc}")
        return {"connected": False, "status": "unreachable", "error": str(exc)}
