import unittest

import tests.reusable as reusable
from tests.test_similarity_search_quality import SearchQualityChecks

# -------- LAUNCH (CPU)
# .\run_cpu_test.ps1 test_bm25_search_quality
# docker compose -f docker-compose.cpu.test.yml up -d
# docker compose -f docker-compose.cpu.test.yml exec backend python -m tests.test_bm25_search_quality -v

# ====== DOWN (CPU)
# docker compose -f docker-compose.cpu.test.yml down

# -------- LAUNCH (GPU)
# docker compose -f docker-compose.test.yml up -d
# docker compose -f docker-compose.test.yml exec backend python3 -m tests.test_bm25_search_quality -v

# ====== DOWN (GPU)
# docker compose -f docker-compose.test.yml down

RESULT_LIMIT = 100

class BM25SearchQualityTest(SearchQualityChecks, unittest.TestCase):
    def test_bm25_search_quality(self):
        print("\nSearch method: SQLite FTS5 BM25")
        self.run_search_quality(
            folder_prefix="bm25_search_quality",
            metadata={"search_method": "bm25", "limit": RESULT_LIMIT},
        )

    def search(self, query):
        return reusable.request(
            "POST", "/sqlite/search_fts_bm25", {"text": query, "limit": RESULT_LIMIT}
        )

if __name__ == "__main__":
    unittest.main()
