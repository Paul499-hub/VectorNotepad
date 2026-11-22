from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, event
from pathlib import Path
# Modules
from app.core.config import settings, APP_DIR

db_path = APP_DIR / settings.sqlite_db_path
db_path.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
