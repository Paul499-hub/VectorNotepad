from pydantic import BaseModel, Field

# Router schemas
class IN_TextEmbedRequest(BaseModel):
    text: str

class IN_SimilaritySearchRequest(BaseModel):
    text: str
    point_limit: int = Field(gt=0, lt=99999)
    note_limit: int | None = Field(default=None, gt=0, lt=99999)
    rerank: bool = True

class IN_FTS_BM25_SearchRequest(BaseModel):
    text: str
    limit: int = Field(default=100, gt=0, lt=99999)

class IN_UpdateRequest(BaseModel):
    id: int = Field(gt=0, lt=99999)
    text: str