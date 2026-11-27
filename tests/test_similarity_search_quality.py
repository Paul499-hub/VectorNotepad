import json
import os
import unittest
from datetime import datetime, timezone
from statistics import mean

import tests.reusable as reusable
from tests.data.reranker_messy_notes import MESSY_CANDIDATES, MESSY_QUERIES
from tests.data.vocabulary_mismatch import VOCABULARY_CANDIDATES, VOCABULARY_QUERIES
from tests.test_reranker_quality import CANDIDATES, HARD_CANDIDATES, HARD_QUERIES, QUERIES

# -------- LAUNCH (CPU)
# docker compose -f docker-compose.cpu.test.yml up -d
# docker compose -f docker-compose.cpu.test.yml exec backend python -m tests.test_similarity_search_quality -v

# ====== DOWN (CPU)
# docker compose -f docker-compose.cpu.test.yml down

# -------- LAUNCH (GPU)
# docker compose -f docker-compose.test.yml up -d
# docker compose -f docker-compose.test.yml exec backend python3 -m tests.test_similarity_search_quality -v

# ====== DOWN (GPU)
# docker compose -f docker-compose.test.yml down

POINT_LIMIT = 150


class SearchQualityChecks:
    def run_search_quality(self, *, folder_prefix, metadata):
        rows = []
        summary = {**metadata, "datasets": {}}

        for dataset, candidates, queries in (
            ("original", CANDIDATES, QUERIES),
            ("hard", HARD_CANDIDATES, HARD_QUERIES),
            ("messy_notes", MESSY_CANDIDATES, MESSY_QUERIES),
            ("vocabulary_mismatch", VOCABULARY_CANDIDATES, VOCABULARY_QUERIES),
        ):
            self.assertEqual(
                reusable.request("GET", "/sqlite/count_notes"), 0,
                "Use an empty test notebook for the fixed candidate sets.",
            )
            dataset_rows = self.score_queries(dataset, candidates, queries)
            self.assertTrue(self.doCleanups(), f"Failed to clean up the {dataset} dataset")
            rows.extend(dataset_rows)
            summary["datasets"][dataset] = {
                "query_count": len(dataset_rows),
                "candidates_per_query": len(candidates),
                "hit_at_1": mean(row["hit_at_1"] for row in dataset_rows),
                "hit_at_3": mean(row["hit_at_3"] for row in dataset_rows),
                "mrr": mean(row["reciprocal_rank"] for row in dataset_rows),
            }

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        csv_path = reusable.write_results_csv(
            "results.csv", rows, run_folder=f"{folder_prefix}_{timestamp}"
        )
        with csv_path.with_name("metadata.json").open("x", encoding="utf-8") as file:
            json.dump(summary, file, indent=2)
            file.write("\n")

        for dataset, metrics in summary["datasets"].items():
            print(
                f"{dataset} | Hit@1: {metrics['hit_at_1']:.3f} | "
                f"Hit@3: {metrics['hit_at_3']:.3f} | MRR: {metrics['mrr']:.3f}"
            )
        print(f"Saved results to {csv_path.parent}", flush=True)

    def score_queries(self, dataset, candidates, queries):
        note_labels = {}
        for label, text in candidates.items():
            note = reusable.create_test_note_chunks(self, text)
            note_labels[note["id"]] = label

        rows = []
        for query, expected_label in queries:
            results = self.search(query)
            self.assertTrue(all("reranked_score" not in note for note in results), query)
            ranked_labels = [note_labels[note["id"]] for note in results]
            self.assertEqual(len(ranked_labels), len(set(ranked_labels)), query)
            rank = ranked_labels.index(expected_label) + 1 if expected_label in ranked_labels else None
            rows.append({
                "dataset": dataset,
                "query": query,
                "expected_note": expected_label,
                "first_result": ranked_labels[0] if ranked_labels else None,
                "expected_note_rank": rank,
                "hit_at_1": int(rank == 1),
                "hit_at_3": int(rank is not None and rank <= 3),
                "reciprocal_rank": 1 / rank if rank is not None else 0,
                "ranked_notes": " ".join(ranked_labels),
            })
        return rows


class SimilaritySearchQualityTest(SearchQualityChecks, unittest.TestCase):
    def test_similarity_search_quality(self):
        embedding_model = os.environ["EMBEDDING_MODEL"]
        print(f"\nEmbedding model: {embedding_model}")
        self.run_search_quality(
            folder_prefix="similarity_search_quality",
            metadata={"embedding_model": embedding_model, "rerank": False, "point_limit": POINT_LIMIT},
        )

    def search(self, query):
        return reusable.request(
            "POST", "/storage/similarity_search_chunks",
            {"text": query, "point_limit": POINT_LIMIT, "rerank": False},
        )


if __name__ == "__main__":
    unittest.main()
