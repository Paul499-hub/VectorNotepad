from fastapi import APIRouter, HTTPException, Form, File, UploadFile
# Modules
from app.schemas.embedding import IN_UpdateRequest, IN_SimilaritySearchRequest
from app.core.services import storage_svc
from app.schemas.note import NoteCreate
from app.schemas.file import FileCreate

router = APIRouter(prefix='/storage', tags=["Storage"])

@router.post("/save_note", status_code=200)
def r_save_note(
                payload: NoteCreate
            ):
    try:
        return storage_svc.save_note(text=payload.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/save_note_chunks", status_code=200)
def r_save_note(
                payload: NoteCreate
            ):
    try:
        return storage_svc.save_note_chunks(text=payload.text)
        # "id": sqlite_saved_note.id,
        # "text": text,
        # "html_md": parse_into_markdown(text),
        # "last_chunk_idx": last_chunk_idx
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    
@router.delete("/del/{note_id}")
def r_delete_note(
                note_id: int
                ):
    try:
        return storage_svc.del_note(note_id = note_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/recreate_from_sqlite_file", status_code=200)
def r_recreate_from_sqlite():
    try:
        return storage_svc.recreate_from_sqlite()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.patch("/update_note", status_code=200)
def r_update_note(
                payload: IN_UpdateRequest
            ):
    try:
        return storage_svc.update_note(note_id=payload.id, text=payload.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.patch("/update_note_chunks", status_code=200)
def r_update_note(
                payload: IN_UpdateRequest
            ):
    try:
        return storage_svc.update_note_chunks(note_id=payload.id, text=payload.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/similarity_search", status_code=200)
def r_vector_search(payload: IN_SimilaritySearchRequest):
    try:
        return storage_svc.vector_search_note(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/similarity_search_chunks", status_code=200)
def r_vector_search(payload: IN_SimilaritySearchRequest):
    try:
        return storage_svc.vector_search_note_chunks(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/store_files", status_code=200)
async def r_store_file(
        note_id: int = Form(...),
        files: list[UploadFile] = File(...)
    ):
    try:
        payload = []
        for f in files:
            data = await f.read()
            payload.append(FileCreate(
                filename = f.filename or "unnamed",
                content_type = f.content_type or "application/octet-stream",
                size_bytes = len(data),
                data = data,
                note_id = note_id
            ))
        return storage_svc.store_files(payload=payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

