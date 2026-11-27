import json
import os
import unittest
from datetime import datetime, timezone
from statistics import mean, median
from time import perf_counter

import tests.reusable as reusable
from tests.data.reranker_messy_notes import MESSY_CANDIDATES, MESSY_QUERIES
from tests.data.vocabulary_mismatch import VOCABULARY_CANDIDATES, VOCABULARY_QUERIES
from tests.test_reranker_quality import CANDIDATES, HARD_CANDIDATES, HARD_QUERIES, QUERIES
from tests.test_similarity_search_quality import POINT_LIMIT

# -------- LAUNCH (CPU)
# .\run_cpu_test.ps1 test_search_reranking_comparison
# docker compose -f docker-compose.cpu.test.yml up -d
# docker compose -f docker-compose.cpu.test.yml exec backend python -m tests.test_search_reranking_comparison -v

# ====== DOWN (CPU)
# docker compose -f docker-compose.cpu.test.yml down

# -------- LAUNCH (GPU)
# docker compose -f docker-compose.test.yml up -d
# docker compose -f docker-compose.test.yml exec backend python3 -m tests.test_search_reranking_comparison -v

# ====== DOWN (GPU)
# docker compose -f docker-compose.test.yml down


class SearchRerankingComparisonTest(unittest.TestCase):
    def test_search_reranking_comparison(self):
        rows = []
        summary = {
            "embedding_model": os.environ["EMBEDDING_MODEL"],
            "reranker_model": os.environ["RERANKER_MODEL"],
            "point_limit": POINT_LIMIT,
            "datasets": {},
        }
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
            note_labels = {}
            for label, text in candidates.items():
                note = reusable.create_test_note_chunks(self, text)
                note_labels[note["id"]] = label

            warmup_query = queries[0][0]
            self.search(warmup_query, rerank=False, note_labels=note_labels)
            self.search(warmup_query, rerank=True, note_labels=note_labels, timeout=600)

            dataset_rows = []
            for query, expected_label in queries:
                row = {"dataset": dataset, "query": query, "expected_note": expected_label}
                for mode, rerank in (("off", False), ("on", True)):
                    ranked_labels, elapsed_ms = self.search(query, rerank=rerank, note_labels=note_labels)
                    rank = ranked_labels.index(expected_label) + 1 if expected_label in ranked_labels else None
                    row.update({
                        f"rerank_{mode}_rank": rank,
                        f"rerank_{mode}_latency_ms": round(elapsed_ms, 1),
                        f"rerank_{mode}_ranked_notes": " ".join(ranked_labels),
                    })
                dataset_rows.append(row)

            self.assertTrue(self.doCleanups(), f"Failed to clean up the {dataset} dataset")
            rows.extend(dataset_rows)
            metrics = {"query_count": len(dataset_rows), "candidates_per_query": len(candidates)}
            for mode in ("off", "on"):
                ranks = [row[f"rerank_{mode}_rank"] for row in dataset_rows]
                metrics[f"rerank_{mode}"] = {
                    "hit_at_1": mean(rank == 1 for rank in ranks),
                    "hit_at_3": mean(rank is not None and rank <= 3 for rank in ranks),
                    "mrr": mean(1 / rank if rank is not None else 0 for rank in ranks),
                    "median_latency_ms": median(row[f"rerank_{mode}_latency_ms"] for row in dataset_rows),
                }
            summary["datasets"][dataset] = metrics

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        csv_path = reusable.write_results_csv(
            "results.csv", rows, run_folder=f"search_reranking_comparison_{timestamp}"
        )
        with csv_path.with_name("metadata.json").open("x", encoding="utf-8") as file:
            json.dump(summary, file, indent=2)
            file.write("\n")

        for dataset, metrics in summary["datasets"].items():
            for mode in ("off", "on"):
                values = metrics[f"rerank_{mode}"]
                print(
                    f"{dataset} | Rerank {mode} | Hit@1: {values['hit_at_1']:.3f} | "
                    f"Hit@3: {values['hit_at_3']:.3f} | MRR: {values['mrr']:.3f} | "
                    f"Median latency: {values['median_latency_ms']:.1f} ms"
                )
        print(f"Saved results to {csv_path.parent}", flush=True)

    def search(self, query, *, rerank, note_labels, timeout=120):
        start = perf_counter()
        results = reusable.request(
            "POST", "/storage/similarity_search_chunks",
            {"text": query, "point_limit": POINT_LIMIT, "rerank": rerank},
            timeout=timeout,
        )
        elapsed_ms = (perf_counter() - start) * 1000
        self.assertTrue(all(("reranked_score" in note) == rerank for note in results), query)
        ranked_labels = [note_labels[note["id"]] for note in results]
        self.assertEqual(len(ranked_labels), len(set(ranked_labels)), query)
        return ranked_labels, elapsed_ms


if __name__ == "__main__":
    unittest.main()
