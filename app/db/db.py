from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import create_engine, event
from pathlib import Path
# Modules
from app.core.config import settings, APP_DIR

db_path = APP_DIR / settings.sqlite_db_path
db_path.parent.mkdir(parents=True, exist_ok=True)
engine = create_engine(f"sqlite:///{db_path}", connect_args={"check_same_thread": False})
def create_notes_fts():
    """Index `text` from existing sqlite `notes` table, uses id's from `notes.id`"""
    with engine.begin() as connection:

        insert_trigger_exists = connection.exec_driver_sql("""
            SELECT 1 FROM sqlite_master
            WHERE type = 'trigger' AND name = 'notes_fts_insert'
        """).scalar() is not None

        connection.exec_driver_sql("""
            CREATE VIRTUAL TABLE IF NOT EXISTS notes_fts
            USING fts5(text, content='notes', content_rowid='id')        
        """)
        # On sqlite `note`` create, `create notes_fts` row aswell
        connection.exec_driver_sql("""
            CREATE TRIGGER IF NOT EXISTS notes_fts_insert
            AFTER INSERT ON notes BEGIN
                INSERT INTO notes_fts(rowid, text) VALUES (new.id, new.text);
            END
        """)
        # On sqlite `note` delete, remove `notes_fts` row aswell
        connection.exec_driver_sql("""
            CREATE TRIGGER IF NOT EXISTS notes_fts_delete
            AFTER DELETE ON notes BEGIN
                INSERT INTO notes_fts(notes_fts, rowid, text)
                VALUES ('delete', old.id, old.text);
            END
        """)
        connection.exec_driver_sql("""
            CREATE TRIGGER IF NOT EXISTS notes_fts_update
            AFTER UPDATE OF text ON notes BEGIN
                INSERT INTO notes_fts(notes_fts, rowid, text)
                VALUES ('delete', old.id, old.text);
                INSERT INTO notes_fts(rowid, text) VALUES (new.id, new.text);
            END
        """)
        # Read every note already in notes and add its words to the search index
        if not insert_trigger_exists:
            connection.exec_driver_sql(
                "INSERT INTO notes_fts(notes_fts) VALUES ('rebuild')"
            )
        
      
@event.listens_for(engine, "connect")
def enable_foreign_keys(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
