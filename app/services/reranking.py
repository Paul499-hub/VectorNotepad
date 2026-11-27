from threading import Lock
import torch
# Modules
from sentence_transformers import CrossEncoder
from app.core.config import settings

class RerankingService:
    def __init__(self) -> None:
        self.reranker_model: CrossEncoder | None = None
        self._load_lock = Lock()

    def rerank(self, query: str, notes: list[str]):
        """
        ### Returns the re-ranking scores of str notes using `BAAI/bge-reranker-v2-m3` of a given query
        Does NOT sort the returned output. Idx `0` of returned result = reranked score of note idx `0`
        Lazy loads the re-ranking model on first call.\n
        The lock lets only one thread at a time enter the with self._load_lock: block.\n 
        If two reranking requests arrive together:\n
            1. Request A takes the lock, sees None, and starts loading the model.
            2. Request B reaches the lock and waits.
            3. Request A stores the model and leaves the with block. Python releases the lock automatically.
            4. Request B takes the lock, sees the model is already there, and skips loading.
        """
        if not notes:
            return []
        # Lazy load reranker on first re-rank run
        with self._load_lock:
            if self.reranker_model is None:
                use_cuda = torch.cuda.is_available()
                self.reranker_model = CrossEncoder(
                    settings.reranker_model,
                    #"BAAI/bge-reranker-v2-m3",
                    device="cuda" if use_cuda else "cpu",
                    model_kwargs={
                        "dtype": torch.float16 if use_cuda else torch.float32,
                    },
                )
            # now it will skip next load
        return self.reranker_model.predict([(query, note) for note in notes])

