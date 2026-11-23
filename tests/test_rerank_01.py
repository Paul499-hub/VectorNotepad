import math
# Modules
from app.services.reranking import RerankingService

# ------ LAUNCH 
# docker compose run --rm tests python3 -m tests.test_rerank_01

# ----------- TEST SCOPE
# Tests real reranking on a shared set of notes using several queries
# Checks score count, finite scores, and whether the expected note ranks first
# Includes paraphrased queries and closely related notes
# Does not test Qdrant retrieval or the search endpoint


reranking_svc = RerankingService()

# A shared collection of candidate notes
notes = [
    "Use df -h to display filesystem capacity and available disk space.",
    "Use free -h to inspect RAM usage on Linux.",
    "Mix beetroot, tuna and eggs to make a salad.",
    "Use docker compose stop to stop containers without removing them.",
    "Use docker compose down to stop and remove containers and networks.",
    "SQL ON DELETE CASCADE removes child rows when their parent row is deleted.",
    "A database index can speed up queries that filter rows by an indexed column.",
    "Use git restore path/to/file to discard uncommitted changes in a tracked file.",
]

# Each case specifies the index of the note we expect to rank first
cases = [
    {
        "query": "How do I check available disk space on Linux?",
        "expected_index": 0,
    },
    {
        "query": "How much memory is my Linux computer using?",
        "expected_index": 1,
    },
    {
        "query": "What can I cook with canned fish and beetroot?",
        "expected_index": 2,
    },
    {
        "query": "Stop my Docker containers but keep them so I can restart them.",
        "expected_index": 3,
    },
    {
        "query": "Remove related attachments automatically when I delete a note.",
        "expected_index": 5,
    },
    {
        "query": "Undo my unsaved-to-git changes to a tracked file.",
        "expected_index": 7,
    },
]

passed = 0

for case in cases:
    query = case["query"]
    scores = reranking_svc.rerank(query, notes)

    # Check that each note received a valid numeric score
    assert len(scores) == len(notes), "Score count does not match note count."
    assert all(math.isfinite(float(score)) for score in scores), (
        "Model returned a NaN or infinite score."
    )

    # Pair each note with its score, then sort by score descending
    ranked_notes = sorted(
        zip(notes, scores),
        key=lambda item: item[1],
        reverse=True,
    )

    expected_note = notes[case["expected_index"]]
    top_note = ranked_notes[0][0]
    matched = top_note == expected_note

    if matched:
        passed += 1

    print(f"\nQuery: {query}")
    print(f"Expected first: {expected_note}")
    print(f"Result: {'PASS' if matched else 'CHECK RANKING'}")

    for note, score in ranked_notes:
        print(f"  {score:.4f} | {note}")

print(f"\nExpected top result: {passed}/{len(cases)} cases")