from fastapi import APIRouter, HTTPException, Response
from urllib.parse import quote
# Modules
from app.core.services import sqlite_svc
from app.schemas.embedding import IN_TextEmbedRequest, IN_UpdateRequest

router = APIRouter(prefix="/sqlite", tags=["Sqlite"])

@router.post("/save", status_code=200)
def r_save_note_sqlite(
                    payload: IN_TextEmbedRequest
                    ):
    try:
        return sqlite_svc.create_note(payload.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/get", status_code=200)
def r_find_note_sqlite(
                    payload: IN_TextEmbedRequest
                    ):
    try:
        return sqlite_svc.find_note_contains(text=payload.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.delete("/del/{note_id}", status_code = 201)
def r_delete_note_sqlite(note_id: int):
    try:
        return sqlite_svc.delete_note(note_id = note_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/count_notes", status_code=200)
def r_count_notes():
    try:
        return sqlite_svc.count_notes()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.get("/deduplicate_sqlite", status_code=200)
def r_deduplicate():
    try:
        return sqlite_svc.deduplicate_sqlite()
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
@router.post("/update_note_sqlite", status_code = 200)
def r_update_note(
                payload: IN_UpdateRequest
                ):
    try:
        return sqlite_svc.update_note(payload.id, payload.text)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_note/{note_id}", status_code=200)
def r_get_by_id(note_id: int):
    try:
        return sqlite_svc.get_by_id(note_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_note_attachment_metadata/{note_id}", status_code=200)
def r_get_note_att_meta(note_id: int):
    try:
        return sqlite_svc.get_note_att_meta(note_id)    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/get_file/{file_id}", status_code=200)
def r_get_file(file_id: int):
    data = sqlite_svc.get_file_by_id(file_id)
    if data is None:
        raise HTTPException(status_code=404, detail="File not found")
    # After the existing 404 check
    filename = quote(data.filename or "attachment", safe="")
    return Response(
        content=data.data,
        media_type="application/octet-stream",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{filename}",
            "X-Content-Type-Options": "nosniff",
        },
    )
    