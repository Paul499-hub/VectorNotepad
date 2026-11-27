import json
import os
import unittest
from datetime import datetime, timezone
from math import isfinite
from statistics import mean

import tests.reusable as reusable
from tests.data.reranker_messy_notes import MESSY_CANDIDATES, MESSY_QUERIES
from tests.data.vocabulary_mismatch import VOCABULARY_CANDIDATES, VOCABULARY_QUERIES

# -------- LAUNCH (CPU)
# docker compose -f docker-compose.cpu.test.yml up -d
# docker compose -f docker-compose.cpu.test.yml exec backend python -m tests.test_reranker_quality -v

# ====== DOWN (CPU)
# docker compose -f docker-compose.cpu.test.yml down

# -------- LAUNCH (GPU)
# docker compose -f docker-compose.test.yml up -d
# docker compose -f docker-compose.test.yml exec backend python3 -m tests.test_reranker_quality -v

# ====== DOWN (GPU)
# docker compose -f docker-compose.test.yml down

# Set RERANKER_MODEL in .env.cpu or .env and recreate the test backend before each run.

CANDIDATES = {
    "deferred_fk": "Declare a PostgreSQL foreign key DEFERRABLE INITIALLY DEFERRED to check it at commit. A child row can be inserted ahead of its parent within the same transaction.",
    "cascade_delete": "A foreign key with ON DELETE CASCADE automatically removes referencing child rows when the parent is deleted.",
    "savepoint": "Create a savepoint before a risky operation. Roll back to that savepoint to undo part of the transaction while keeping earlier changes.",
    "compose_stop": "Use docker compose stop to stop running services while keeping the containers available for docker compose start.",
    "compose_down": "Use docker compose down to remove the project's containers and network. Named volumes are preserved by default.",
    "compose_recreate": "After changing a service's environment, use docker compose up -d to recreate the container with the new settings and reuse the image.",
    "git_restore": "Run git restore on a tracked file to discard unstaged working-tree changes and restore the version from the index.",
    "git_unstage": "Use git restore --staged to remove a file from the next commit while keeping its edits in the working tree.",
    "git_revert": "Use git revert to create a new commit that reverses an earlier commit while preserving shared history.",
    "idempotency_key": "Send the same idempotency key when retrying a payment. The server can return the original result and prevent a duplicate charge.",
    "rate_limit": "After an HTTP 429 response, use the Retry-After header to decide how long to wait before sending another request.",
    "payment_reconciliation": "Compare provider settlement records with internal payment records and investigate differences in amounts or missing entries.",
}

# One labeled target per query. Every model scores the same candidate texts.
QUERIES = (
    ("Can I add a dependent record before the referenced record and verify the relationship at commit?", "deferred_fk"),
    ("How can deleting a parent record clean up its dependent rows automatically?", "cascade_delete"),
    ("One step failed in my transaction. How can I undo just that step and retain my earlier work?", "savepoint"),
    ("I want to shut the services off for the evening and bring the same containers back tomorrow.", "compose_stop"),
    ("How do I remove the Compose containers and their network while retaining the database volume?", "compose_down"),
    ("I changed the settings passed to a container. How do I apply them using the image I already built?", "compose_recreate"),
    ("How do I throw away my unstaged edits to a tracked file?", "git_restore"),
    ("I added a file by accident. How do I leave it out of the next commit and keep my edits?", "git_unstage"),
    ("How can I undo a commit that's already on the shared branch and keep the commit history?", "git_revert"),
    ("The checkout request timed out. How can I retry it without charging the customer twice?", "idempotency_key"),
    ("The server says I'm sending too many requests. Where can I find how long to wait?", "rate_limit"),
    ("How can I spot payments in our system that never showed up in the processor's settlement report?", "payment_reconciliation"),
)

# These passages discuss the same topics as the original candidates and differ
# on details such as when a check runs or which data an operation preserves.
HARD_CANDIDATES = {
    **CANDIDATES,
    "immediate_fk": "A foreign key declared DEFERRABLE INITIALLY IMMEDIATE is checked after each statement unless the transaction explicitly defers it with SET CONSTRAINTS.",
    "defer_then_validate": "Run SET CONSTRAINTS ALL IMMEDIATE to validate already-pending deferred constraints before committing the transaction.",
    "rollback_transaction": "ROLLBACK ends the transaction and discards all changes made since it began, including changes made before any savepoints.",
    "compose_pause": "Use docker compose pause to suspend container processes in place. Use docker compose unpause to resume those same processes.",
    "compose_restart": "Use docker compose restart to restart existing containers with their existing configuration. Updated environment variables are applied when containers are recreated.",
    "git_restore_both": "Use git restore --source=HEAD --staged --worktree to discard both staged and unstaged changes to a tracked path.",
    "git_reset_commit": "Use git reset --soft HEAD~1 to move the current branch back one commit while leaving the changes staged. This rewrites the branch tip.",
    "payment_status_lookup": "After a payment timeout, look up the existing attempt by its provider reference to learn whether it succeeded. A status lookup does not submit a payment.",
    "new_payment_key": "Generate a new idempotency key for each distinct payment operation. Reusing a key from an earlier operation can replay that operation's result.",
}

HARD_QUERIES = (
    ("I load order lines ahead of their orders in one transaction. What schema setting lets that work by default without issuing a separate command in every import?", "deferred_fk"),
    ("My import postponed relationship checks. How do I surface invalid references now while leaving the transaction open?", "defer_then_validate"),
    ("Two inserts succeeded before a third failed. I placed a marker after the second insert and want to keep those two changes. What should I do?", "savepoint"),
    ("I want my services to exit overnight, but tomorrow I need to start the same containers and keep their writable layers. What command should I use?", "compose_stop"),
    ("My tracked file contains both staged and unstaged edits. I want the working copy to match what I staged for the next commit. Which operation does that?", "git_restore"),
    ("The last commit is local. I need to redo the commit message and want all of its changes to stay in the index after moving the branch back. What can I use?", "git_reset_commit"),
    ("The payment request may have succeeded before the response was lost. I want to resubmit the original operation and safely receive the same result. What should my client send?", "idempotency_key"),
    ("A payment response was lost. I already have the processor's reference and only want to find out what happened, without sending another charge request. What should I do?", "payment_status_lookup"),
)


class RerankerQualityTest(unittest.TestCase):
    def test_reranker_quality(self):
        from app.services.reranking import RerankingService

        model_name = os.environ["RERANKER_MODEL"]
        reranker = RerankingService()
        rows = []
        summary = {"reranker_model": model_name, "datasets": {}}
        for name, candidates, queries in (
            ("original", CANDIDATES, QUERIES),
            ("hard", HARD_CANDIDATES, HARD_QUERIES),
            ("messy_notes", MESSY_CANDIDATES, MESSY_QUERIES),
            ("vocabulary_mismatch", VOCABULARY_CANDIDATES, VOCABULARY_QUERIES),
        ):
            dataset_rows = self.score_queries(reranker, name, candidates, queries)
            rows.extend(dataset_rows)
            summary["datasets"][name] = {
                "query_count": len(dataset_rows),
                "candidates_per_query": len(candidates),
                "hit_at_1": mean(row["hit_at_1"] for row in dataset_rows),
                "hit_at_3": mean(row["hit_at_3"] for row in dataset_rows),
                "mrr": mean(row["reciprocal_rank"] for row in dataset_rows),
            }

        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        csv_path = reusable.write_results_csv(
            "results.csv", rows, run_folder=f"reranker_quality_{timestamp}"
        )
        with csv_path.with_name("metadata.json").open("x", encoding="utf-8") as file:
            json.dump(summary, file, indent=2)
            file.write("\n")

        print(f"\nReranker model: {model_name}")
        for name, metrics in summary["datasets"].items():
            print(f"{name} | Hit@1: {metrics['hit_at_1']:.3f} | Hit@3: {metrics['hit_at_3']:.3f} | MRR: {metrics['mrr']:.3f}")
        print(f"Saved results to {csv_path.parent}", flush=True)

    def score_queries(self, reranker, dataset, candidates, queries):
        candidate_ids = list(candidates)
        candidate_texts = list(candidates.values())
        rows = []
        for query, expected_id in queries:
            scores = [float(score) for score in reranker.rerank(query, candidate_texts)]
            self.assertEqual(len(scores), len(candidate_ids))
            self.assertTrue(all(isfinite(score) for score in scores), query)
            ranked_ids = [
                candidate_id for candidate_id, _ in sorted(
                    zip(candidate_ids, scores), key=lambda result: result[1], reverse=True
                )
            ]
            rank = ranked_ids.index(expected_id) + 1
            rows.append({
                "dataset": dataset,
                "query": query,
                "expected_note": expected_id,
                "first_result": ranked_ids[0],
                "expected_note_rank": rank,
                "hit_at_1": int(rank == 1),
                "hit_at_3": int(rank <= 3),
                "reciprocal_rank": 1 / rank,
                "ranked_notes": " ".join(ranked_ids),
            })

        return rows


if __name__ == "__main__":
    unittest.main()
