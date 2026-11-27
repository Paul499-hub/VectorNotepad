import unittest 
# Modules
import tests.reusable as reusable

# -------- LAUNCH
# docker compose -f docker-compose.cpu.test.yml up -d   # <-- (only if test containers are not already running)
# docker compose -f docker-compose.cpu.test.yml exec backend python -m tests.test_smoketest -v

# ====== DOWN
# docker compose -f docker-compose.cpu.test.yml down

class CpuStackSearchTest(unittest.TestCase):
    def test_saved_note_appears_in_vector_search(self):
        note_text = (
            "Use an idempotency key to avoid charging a customer twice "
            "when they retry a payment."
        )
        saved = reusable.create_test_note_chunks(self, note_text)
        
        results = reusable.request(
                "POST",
                "/storage/similarity_search_chunks",
                {
                    "text": "How can I prevent a duplicate charge after a payment timeout?",
                    "point_limit": 10,
                    "rerank": False,
                },
            )
        matches = [note for note in results if note["id"] == saved["id"]]
        self.assertEqual(len(matches), 1, "Expected the newly saved note in search results")
        self.assertEqual(matches[0]["text"], note_text)

if __name__ == "__main__":
    unittest.main()
