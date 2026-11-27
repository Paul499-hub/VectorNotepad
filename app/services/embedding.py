from app.ai_models.model_registry import embedding_model
from app.schemas.embedding import F_EmbedTextOut
from app.core.config import settings
from collections.abc import Iterator

class EmbeddingService:
    def __init__(self):
        self.tokenizer = embedding_model.tokenizer
        self.chunk_overlap = 36
        # encode() adds special tokens to each chunk
        self.num_special_tokens = self.tokenizer.num_special_tokens_to_add(pair=False)
        self.chunk_limit = min(
            embedding_model.max_seq_length,
            embedding_model.max_seq_length - self.num_special_tokens
        )


    def embed_text(self, text:str) -> F_EmbedTextOut:
        vector = embedding_model.encode(text)
        return F_EmbedTextOut.model_validate({
            "status": "ok",
            "vector": vector.tolist(), # NumPy array -> list
            "vector_size": len(vector),
        })

    def embed_text_chunks(self, text:str, prefix: str = "") -> Iterator[F_EmbedTextOut]:
        """### Yield embedded token chunks with overlap, prefix and special tokens accounted for"""
        p_tokens = embedding_model.tokenizer(prefix, truncation=False, add_special_tokens=False)["input_ids"]
        tokens = embedding_model.tokenizer(text, truncation=False, add_special_tokens=False)["input_ids"]
        ttl = len(tokens) # Tokenized text length (full note)
        ptl = len(p_tokens) # Prefix token len
        # Validate chunk overlap
        if not 0 <= self.chunk_overlap < self.chunk_limit - ptl:
            raise ValueError("Chunk overlap must be smaller than the token budget")
        # For loop through token in windows of chunk limit len, embed each one and yield
        if ttl + ptl > self.chunk_limit:
            chunk_count = 0
            while True:
                chunk_count += 1
                # Define window limits
                start = 0
                end = self.chunk_limit - ptl
                last = False
                if end >= len(tokens):
                    end = len(tokens)
                    last = True
                # Slice
                window = tokens[start:end] 
                # Embed
                prefix_text = self.tokenizer.decode(p_tokens, clean_up_tokenization_spaces=False)
                chunk_text = self.tokenizer.decode(window, clean_up_tokenization_spaces=False)
                vector = embedding_model.encode(prefix_text + chunk_text)
                yield F_EmbedTextOut.model_validate({
                    "status": "ok",
                    "vector": vector.tolist(), # NumPy array -> list
                    "vector_size": len(vector),
                    "chunk_index": chunk_count
                })
                del tokens[0:self.chunk_limit - self.chunk_overlap - ptl]
                if last: break
        else:
            vector = embedding_model.encode(prefix + text)
            yield F_EmbedTextOut.model_validate({
                "status": "ok",
                "vector": vector.tolist(), # NumPy array -> list
                "vector_size": len(vector),
            })

