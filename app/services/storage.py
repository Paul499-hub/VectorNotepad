from app.services.reranking import RerankingService
from app.services.qdrant import QdrantService
from app.services.sqlite import SQLiteService
from app.db.models import NoteORM
from app.db.db import SessionLocal
from sqlalchemy import select
# Modules
from app.schemas.router import IN_SimilaritySearchRequest
from app.core.helpers import parse_into_markdown
from app.schemas.file import FileCreate

class StorageService:
    """## Abstract service, using `qdrant` + `sqlite` storage functionalities"""
    def __init__(self, qdrant_svc: QdrantService, sqlite_svc: SQLiteService, reranking_svc: RerankingService ):
        self.reranking_svc = reranking_svc
        self.qdrant_svc = qdrant_svc
        self.sqlite_svc = sqlite_svc
        
    def save_note(self, text:str):
        sqlite_saved_note:NoteORM = self.sqlite_svc.create_note(text=text)
        note_id:int = sqlite_saved_note.id
        self.qdrant_svc.store_vector(text=text,note_id=note_id)
        return {
            "id": sqlite_saved_note.id,
            "text": text,
            "html_md": parse_into_markdown(text)
        } 
        
    def del_note(self, note_id: int):
        """### Deletes note from both databases
        Deletes all Qdrant points where payload.sqlite_note_id == note_id
        Delets main sqlite note at this `note_id`
        """
        self.qdrant_svc.delete_vector(note_id=note_id)
        return self.sqlite_svc.delete_note(note_id=note_id)
    
    def recreate_from_sqlite(self):
        """Re build all Qdrant points from SQLite source"""
        session = SessionLocal()
        try:
            self.qdrant_svc.clear_points()
            stmt = select(NoteORM.id, NoteORM.text)
            note_info = session.execute(stmt).yield_per(100)
            for note_id, text in note_info:
                self.qdrant_svc.store_vector_chunks(text=text, note_id=note_id)
            return {"message":"ok"}
        finally:
            session.close()

    def update_note(self, note_id: int, text: str):
        update_dict:dict = self.sqlite_svc.update_note(note_id, text)
        self.qdrant_svc.delete_vector(note_id)
        self.qdrant_svc.store_vector(text, note_id)
        return {
            "message": "ok",
            **update_dict
        }

    def update_note_chunks(self, note_id: int, text: str):
        """### Updates sqlite / qdrant note
        First updates sqlite `note.text` to given `text`
        Deletes all Qdrant points where payload.sqlite_note_id == note_id
        Recreates chunked Qdrant points using new given `text`
        """
        update_dict:dict = self.sqlite_svc.update_note(note_id, text)
        self.qdrant_svc.delete_vector(note_id)
        self.qdrant_svc.store_vector_chunks(text, note_id)
        return {
            "message": "ok",
            **update_dict
        }

    def vector_search_note(self, payload: IN_SimilaritySearchRequest):
        # Returned vector search points
        vector_points: list[dict] = self.qdrant_svc.similarity_search(payload) 
        # Many vector retrieved points can share same sqlite_id - deduplicate
        # Find highest score for each matching sqlite_id 
        memory: dict[int, float] = {} # Key = sqlite_id: int , value = score: float 
        for vp in vector_points:
            sid, score = int(vp["sqlite_id"]), vp["score"]
            if sid in memory:
                memory[sid] = max(memory[sid], score)
            else:
                memory[sid] = score
        sqlite_ids = memory.keys()
        # Find actual note text from SQLite 
        note_orms: list[NoteORM] = self.sqlite_svc.find_notes_by_ids(ids = sqlite_ids)
        if payload.rerank:
            if not note_orms:
                return []
            chunks: list[str] = []
            chunk_note_ids: list[int] = []
            for note in note_orms:
                for chunk in self._chunk(note.text, window_size=512, overlap=64):
                    chunks.append(chunk)
                    chunk_note_ids.append(note.id)
            scores = self.reranking_svc.rerank(payload.text, chunks)
            best_scores: dict[int, float] = {}
            for note_id, score in zip(chunk_note_ids, scores, strict=True):
                score = float(score)
                best_scores[note_id] = max(best_scores.get(note_id, score), score)
            ranked_notes = sorted(
                note_orms,
                key=lambda note: best_scores[note.id],
                reverse=True,
            )
            return [
                {
                    "id": note.id,
                    "score": memory[note.id],
                    "reranked_score": best_scores[note.id],
                    "text": note.text,
                    "html_md": parse_into_markdown(note.text),
                }
                for note in ranked_notes
            ]
        else: # non re-ranking branch
            return [
                {
                    "id": n.id,
                    "score": memory[n.id],
                    "text": n.text,
                    "html_md" : parse_into_markdown(n.text),
                    #"preview": f'{" ".join(n.text.split())[:50]}...' #<-- remove newlines / tabs
                }
                for n in sorted(note_orms, key=lambda note: memory[note.id], reverse=True)
            ]

    def store_files(self, payload: list[FileCreate]):
        return self.sqlite_svc.create_files(payload=payload)

    # --- CHUNK PART 
    def save_note_chunks(self, text:str):
        """
        ### Stores a note in sqlite + qdrant (chunked)
        Note is first stored in sqlite to get it's sqlite id.\n
        Then we store embedded note vectors (optionally chunked if tokenized text len is too large)\n
        in qdrant - with:\n
            "sqlite_note_id": note_id,
            "chunk_idx": emb.chunk_index
        stored additionaly for each vector
        ---
        This function returns:\n
        ```
         return {
                    "id": sqlite_saved_note.id,
                    "text": text,
                    "html_md": parse_into_markdown(text),
                    "last_chunk_idx": last_chunk_idx
                }
        ```
        """
        sqlite_saved_note:NoteORM = self.sqlite_svc.create_note(text=text)
        note_id:int = sqlite_saved_note.id
        last_chunk_idx = self.qdrant_svc.store_vector_chunks(text=text, note_id=note_id)["last_chunk_idx"]
        return {
            "id": sqlite_saved_note.id,
            "text": text,
            "html_md": parse_into_markdown(text),
            "last_chunk_idx": last_chunk_idx
        }

    def vector_search_note_chunks(
                                self, 
                                payload: IN_SimilaritySearchRequest, 
                                r_window_size:int=512, 
                                r_overlap:int=64
                            ):
        """
        ### Searches for vector in qdrant. 
        First uses regular vector simmilarity search to get `point_limit` simmilar vectors  
        Multiple vectors can belong to single sqlite note (chunked), so we deduplicate
        using `sqlite_id` stored along each vector taking max() of simmilarity score => `score` in returned output
        
        **Optional** reranking:
        When enabled - chunks note for reranker (reranker may truncate if note.text is too long aswell)
        and passes all chunks to reranker at once for batch processing
        Adds `reranked_score` key to output
        """
        # Returned vector search points
        vector_points: list[dict] = self.qdrant_svc.similarity_search(payload) 
        # Many vector retrieved points can share same sqlite_id (chunks) - deduplicate
        # Find highest score for each matching sqlite_id 
        memory: dict[int, float] = {} # Key = sqlite_id: int , value = score: float 
        for vp in vector_points:
            sid, score = int(vp["sqlite_id"]), vp["score"]
            if sid in memory:
                memory[sid] = max(memory[sid], score)
            else:
                memory[sid] = score
        sqlite_ids = memory.keys()
        # Find actual note text from SQLite 
        note_orms: list[NoteORM] = self.sqlite_svc.find_notes_by_ids(ids = sqlite_ids)
        if payload.rerank:
            # Chunk note orm text here for reranker so text does not truncate in reranker anymore
            out = []
            query = payload.text
            for n in note_orms:
                chunked = list(self._chunk(n.text, window_size=r_window_size, overlap=r_overlap))
                # Get reranking scores for a single note reranker chunked
                reranked = self.reranking_svc.rerank(query, chunked) # [float...]
                # Must flatten to single score (max)
                r_score = float(max(reranked))
                # Build response output shape
                out.append({
                    "id": n.id,
                    "score": memory[n.id],      # Vector search memory score
                    "reranked_score": r_score,  # Reranked score
                    "text": n.text,
                    "html_md": parse_into_markdown(n.text)
                })
            return [n for n in sorted(out, key=lambda el: el["reranked_score"], reverse=True)]
        else: # non re-ranking branch
            return [
                {
                    "id": n.id,
                    "score": memory[n.id],
                    "text": n.text,
                    "html_md" : parse_into_markdown(n.text),
                    #"preview": f'{" ".join(n.text.split())[:50]}...' #<-- remove newlines / tabs
                }
                for n in sorted(note_orms, key=lambda note: memory[note.id], reverse=True)
            ]


    def vector_search_note_chunks_batched(self, payload: IN_SimilaritySearchRequest):
            # Returned vector search points
            vector_points: list[dict] = self.qdrant_svc.similarity_search(payload) 
            # Many vector retrieved points can share same sqlite_id (chunks) - deduplicate
            # Find highest score for each matching sqlite_id 
            memory: dict[int, float] = {} # Key = sqlite_id: int , value = score: float 
            for vp in vector_points:
                sid, score = int(vp["sqlite_id"]), vp["score"]
                if sid in memory:
                    memory[sid] = max(memory[sid], score)
                else:
                    memory[sid] = score
            sqlite_ids = memory.keys()
            # Find actual note text from SQLite 
            note_orms: list[NoteORM] = self.sqlite_svc.find_notes_by_ids(ids = sqlite_ids)
            # Chunk note orm text here for reranker so text does not truncate in reranker anymore
            if payload.rerank:
                # Build lookup (for reranker batching)
                out = []
                temp = 0
                lookup = {} # parent note idx => {"start", "end"}
                chunked_all = []
                query = payload.text
                # Build lookup dict 
                for idx, n in enumerate(note_orms):
                    # Chunk
                    chunked = list(self._chunk(n.text, window_size=512, overlap=64))
                    chunked_all.extend(chunked)
                    lookup[idx] = {"start":temp, "end":temp+len(chunked)}
                    temp += len(chunked)
                # Rerank using lookup slices - pass all note chunks
                reranked = self.reranking_svc.rerank(query, chunked_all) # [float...]
                # Use lookup dict to flatten r_scores using max
                for idx, n in enumerate(note_orms):
                    mapped: dict = lookup[idx]
                    r_score = float(max( reranked[ mapped["start"] : mapped["end"] ])) 
                    # Build response output shape
                    out.append({
                        "id": n.id,
                        "score": memory[n.id],      # Vector search memory score
                        "reranked_score": r_score,  # Reranked score
                        "text": n.text,
                        "html_md": parse_into_markdown(n.text)
                    })
                return [n for n in sorted(out, key=lambda el: el["reranked_score"], reverse=True)]
            else: # non re-ranking branch
                return [
                    {
                        "id": n.id,
                        "score": memory[n.id],
                        "text": n.text,
                        "html_md" : parse_into_markdown(n.text),
                        #"preview": f'{" ".join(n.text.split())[:50]}...' #<-- remove newlines / tabs
                    }
                    for n in sorted(note_orms, key=lambda note: memory[note.id], reverse=True)
                ]

    def _chunk(self, text: str, window_size: int, overlap: int):
        if not 0 <= overlap < window_size:
            raise ValueError("Overlap must be smaller than the window size")
        last = False
        while True:
            start = 0
            end = window_size
            if end >= len(text):
                end = len(text)
                last = True
            yield text[start : end]
            if last: break
            text = text[end - overlap:] # Remove past non-overlap