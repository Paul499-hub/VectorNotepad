from app.ai_models.model_registry import reranker_model


class RerankingService():
    def __init__(self) -> None:
        pass

    def rerank(self, query: str, notes: list[str]):
        scores = reranker_model.predict([(query, note) for note in notes])
        return scores
        
        # # Sort scores by relevance
        # reranked = sorted(
        #     zip(notes, scores),
        #     key=lambda item: item[1], # Sort by `scores` - idx 1 of (notes, scores)
        #     reverse=True
        # )
        # if print_output:
        #     for note, score in reranked:
        #         print(f"{score:.4f} | {note}")
        # return reranked
