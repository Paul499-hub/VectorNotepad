from sqlalchemy import select, text as sql_text
from collections.abc import Iterable
from sqlalchemy.engine import Row
import re
# Modules
from app.core.helpers import parse_into_markdown
from app.db.db import SessionLocal
from app.db.models import NoteORM, FileORM
from app.schemas.file import FileCreate
from app.schemas.note import Note

class SQLiteService():
    def create_files(self, payload: list[FileCreate]):
        session = SessionLocal()
        try:
            created_files = []
            for f in payload:
                file = FileORM(
                    filename = f.filename,
                    content_type = f.content_type,
                    size_bytes = f.size_bytes,
                    data = f.data,
                    note_id = f.note_id
                )
                session.add(file)
                created_files.append(file)
            # Insert rows and id's before committing
            session.flush()
            result = {
                "files": [
                    {
                        "id": file.id,
                        "note_id": file.note_id,
                        "filename": file.filename,
                        "content_type": file.content_type,
                        "size_bytes": file.size_bytes
                    }
                    for file in created_files
                ]
            }
            session.commit()
            return result
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    def create_note(self, text:str) -> NoteORM:
        session = SessionLocal()
        try:
            note = NoteORM(text=text)
            session.add(note)
            session.commit()
            session.refresh(note)
            return note
        finally:
            session.close()
    
    def find_note_contains(self, text:str) -> list[NoteORM]:
        session = SessionLocal()
        try:
            search_result = session.query(NoteORM).filter(NoteORM.text.contains(text)).all()
            return [
                {
                    "id": s.id,
                    "score": 1.0,
                    "text": s.text,
                    "html_md": parse_into_markdown(s.text), 
                    #"preview": f'{" ".join(s.text.split())[:50]}...' #<-- remove newlines / tabs
                }
                for s in search_result
            ]
        finally:
            session.close()

    def find_notes_by_ids(self, ids: Iterable[int]) -> list[NoteORM]:
        session = SessionLocal()
        try:
            stmt = (
                select(NoteORM)
                .where(NoteORM.id.in_(ids))
            )
            return list(session.execute(stmt).scalars().all())
        finally:
            session.close()
    
    def count_notes(self) -> int:
        session = SessionLocal()
        try:
            return session.query(NoteORM).count()
        finally:
            session.close()

    def delete_note(self, note_id:int):
        session = SessionLocal()
        try:
            note = session.get(NoteORM, note_id)
            if not note:
                raise ValueError(f"Note with id {note_id} not found")
            session.delete(note)
            session.commit()
            return {"deleted_note_id": note_id}
        finally:
            session.close()

    def deduplicate_sqlite(self):
        session = SessionLocal()
        try:
            stmt = select(NoteORM.id, NoteORM.text).order_by(NoteORM.id)
            notes = session.execute(stmt).yield_per(100)
            seen = set()
            duplicate_ids = []
            for note_id, text in notes:
                if text in seen:
                    duplicate_ids.append(note_id)
                else:
                    seen.add(text)
        finally:
            session.close()
        for note_id in duplicate_ids:
            self.delete_note(note_id)
        return {"message": "ok", "deleted_duplicates": len(duplicate_ids)}
    
    def update_note(self, note_id:int, text:str):
        """### Updates `note.text` in sqlite of given `note_id` to given `text`
        """
        session = SessionLocal()
        try:
            new_note:Note = Note.model_validate({"id": note_id, "text": text})
            note:NoteORM = session.get(NoteORM, note_id)
            if not note:
                raise ValueError("Note not found")
            old_text_cache = note.text
            note.text = new_note.text
            session.commit()
            session.refresh(note)
            return {
                "updated_id":f"{note_id}", 
                "old_text":old_text_cache, 
                "new_text":new_note.text,
                "new_html_md": parse_into_markdown(new_note.text) 
            }
        finally:
            session.close()

    def get_by_id(self, note_id:int):
        session = SessionLocal()
        try:
            note:NoteORM = session.get(NoteORM, note_id)
            if not note:
                raise ValueError("Note not found")
            return {
                "id": note.id,
                "score": 1.0,
                "text": note.text,
                "html_md": parse_into_markdown(note.text)
            }
        finally:
            session.close()

    def get_note_att_meta(self, note_id: int) -> list[dict]:
        # fetch id, filename, content_type, size_bytes
        session = SessionLocal()
        try:
            stmt = (
                select(FileORM.id, FileORM.filename, FileORM.content_type, FileORM.size_bytes)
                .where(FileORM.note_id == note_id)
            )
            resp = session.execute(stmt).mappings().all() # list[RowMapping]
            return resp
        finally:
            session.close()

    def get_file_by_id(self, file_id: int) -> None | Row[tuple[bytes, str]]:
        session = SessionLocal()
        try:
            stmt = (
                select(FileORM.data, FileORM.content_type, FileORM.filename)
                .where(FileORM.id == file_id)
            )
            return session.execute(stmt).one_or_none()
        finally:
            session.close()

    def search_notes_bm25(self, query: str, limit: int = 50) -> list[dict]:
        terms = re.findall(r"[^\W_]+", query)
        if not terms:
            return []
        match_query = " OR ".join(f'"{term}"' for term in terms)
        statement = sql_text("""
            SELECT notes.id, notes.text, bm25(notes_fts) AS score
            FROM notes_fts
            JOIN notes ON notes.id = notes_fts.rowid
            WHERE notes_fts MATCH :match_query
            ORDER BY score ASC, notes.id ASC
            LIMIT :limit
        """)
        with SessionLocal() as session:
            rows = session.execute(
                statement, {"match_query": match_query, "limit": limit}
            ).mappings()
            return [
                {
                    "id": row["id"],
                    "text": row["text"],
                    "score": row["score"],
                    "html_md": parse_into_markdown(row["text"])
                } 
                for row in rows
            ]
