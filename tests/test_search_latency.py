import json
import os
import unittest
from datetime import datetime, timezone
from statistics import median
from time import perf_counter

import tests.reusable as reusable

# -------- LAUNCH (CPU)
# docker compose -f docker-compose.cpu.test.yml up -d   # <-- (only if test containers are not already running)
# docker compose -f docker-compose.cpu.test.yml exec backend python -m tests.test_search_latency -v

# ====== DOWN
# docker compose -f docker-compose.cpu.test.yml down

# -------- LAUNCH (GPU)
# docker compose -f docker-compose.test.yml up -d --build
# Wait for http://127.0.0.1:48727/ui/home to load.
# docker compose -f docker-compose.test.yml exec backend python3 -m tests.test_search_latency -v

# ====== DOWN (GPU)
# docker compose -f docker-compose.test.yml down

# ----------- ENVIRONMENT
# make sure your .env or .env.cpu (depeding of which compose you're running) has these variables
# EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
# QDRANT_VECTOR_LENGTH=384
# RERANKER_MODEL=BAAI/bge-reranker-v2-m3



NOTE_COUNTS = (1, 5, 10, 20, 50, 100)
REPEATS = 3
POINT_LIMIT = 150
# Match the character windows used by /storage/similarity_search_chunks.
RERANK_WINDOW_SIZE = 512
RERANK_OVERLAP = 64
QUERY = "How can I avoid charging a customer twice after a payment timeout?"
NOTE_TEXTS = (
    "Use an idempotency key to prevent charging a customer twice when a payment is retried.",
    "Group payment attempts by invoice and record the time each response arrives. "
    "Review pending attempts before sending the daily reconciliation report.",
    "A customer may close the checkout page while a payment is still pending. "
    "Check the payment provider before sending a receipt or asking the customer to try again. "
    "Keep the provider reference in the order history so support can inspect the result.",
    "The workshop opens on Saturday morning. The first volunteer should check the tools, "
    "unlock the side entrance, and place the sign-in sheet near the door. After lunch, "
    "sort the spare parts by size and put the heavier boxes on the lowest shelf. At closing "
    "time, check the windows and return the keys to the coordinator. "
    "The next group will use the same room on Sunday. Leave the tables clear and write "
    "a short handover note if any equipment needs attention. Put tools that need repair "
    "on the smaller bench and label them with the part number if it is visible. "
    "The coordinator will review those notes before buying replacement supplies.",
)


class SearchLatencyTest(unittest.TestCase):
    def test_search_latency_by_note_count(self):
        embedding_model = os.environ["EMBEDDING_MODEL"]
        reranker_model = os.environ["RERANKER_MODEL"]
        self.assertEqual(
            reusable.request("GET", "/sqlite/count_notes"), 0,
            "Run against an empty test notebook so each row has the stated candidate count.",
        )

        note_ids = set()

        def timed_search(rerank, *, timeout=120):
            start = perf_counter()
            results = reusable.request(
                "POST",
                "/storage/similarity_search_chunks",
                {"text": QUERY, "point_limit": POINT_LIMIT, "rerank": rerank},
                timeout=timeout,
            )
            elapsed_ms = (perf_counter() - start) * 1000
            self.assertCountEqual([note["id"] for note in results], note_ids)
            self.assertTrue(all(("reranked_score" in note) == rerank for note in results))
            return elapsed_ms

        chunk_count = 0
        input_chars = 0
        csv_rows = []
        step = RERANK_WINDOW_SIZE - RERANK_OVERLAP
        print(f"\nEmbedding model: {embedding_model}\nReranker model: {reranker_model}", flush=True)
        print(
            "\nNotes | Total chunks | Input chars | Rerank off median (ms) | Rerank on median (ms)",
            flush=True,
        )
        for count in NOTE_COUNTS:
            for index in range(len(note_ids), count):
                text = f"# Benchmark note {index + 1}\n\n{NOTE_TEXTS[index % len(NOTE_TEXTS)]}"
                saved = reusable.create_test_note_chunks(self, text)
                note_ids.add(saved["id"])
                remaining_chars = max(0, len(saved["text"]) - RERANK_WINDOW_SIZE)
                extra_chunks = (remaining_chars + step - 1) // step
                note_chunk_count = 1 + extra_chunks
                chunk_count += note_chunk_count
                # Each extra window repeats the overlap, and every pair repeats the query.
                input_chars += len(saved["text"]) + extra_chunks * RERANK_OVERLAP
                input_chars += note_chunk_count * len(QUERY)

            timed_search(False)
            first_reranked_ms = timed_search(True, timeout=600 if count == NOTE_COUNTS[0] else 120)
            if count == NOTE_COUNTS[0]:
                print(f"First reranked request (excluded): {first_reranked_ms:.1f} ms", flush=True)

            off_times = []
            on_times = []
            for _ in range(REPEATS):
                off_times.append(timed_search(False))
                on_times.append(timed_search(True))
            off_median_ms = median(off_times)
            on_median_ms = median(on_times)
            csv_rows.append({
                "notes": count,
                "total_chunks": chunk_count,
                "input_chars": input_chars,
                "rerank_off_median_ms": round(off_median_ms, 1),
                "rerank_on_median_ms": round(on_median_ms, 1),
            })
            print(
                f"{count:>5} | {chunk_count:>12} | {input_chars:>11} | "
                f"{off_median_ms:>22.1f} | {on_median_ms:>21.1f}",
                flush=True,
            )

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        csv_path = reusable.write_results_csv(
            "results.csv", csv_rows, run_folder=f"search_latency_{timestamp}"
        )
        metadata_path = csv_path.with_name("metadata.json")
        with metadata_path.open("x", encoding="utf-8") as metadata_file:
            json.dump({
                "embedding_model": embedding_model,
                "reranker_model": reranker_model,
            }, metadata_file, indent=2)
            metadata_file.write("\n")
        print(f"Saved results to {csv_path}", flush=True)
        print(f"Saved model names to {metadata_path}", flush=True)


if __name__ == "__main__":
    unittest.main()
