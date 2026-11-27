from app.ai_models.model_registry import embedding_model

# ---- LAUNCH
# Get-Content -Raw .\tests\test_emb_limit.py | docker compose -f docker-compose.cpu.yml exec -T backend python -

text = """
# Notes from a weekend workshop

We opened the workshop by reviewing how the team organizes shared notes.
Everyone had a different system. Some people kept daily logs, others wrote
one document per project, and a few put everything into a single notebook.
We agreed that each note should have a descriptive heading and enough
context for someone to understand it six months later. We also discussed
when screenshots are helpful and when a short written description is easier
to search and maintain.

The next session covered local backups. We made a copy of a sample notebook,
restored it into a clean folder, and compared the restored files with the
originals. Several people found that their backup routine covered documents
but skipped attachments. We added a checklist item to open a restored
attachment and confirm it could still be read. We also wrote down who would
perform the next restore exercise and where the results should be recorded.

After lunch we worked on a small inventory application. We listed the fields
needed to describe borrowed equipment and sketched a screen for recording
returns. We considered how to handle an item with a missing serial number,
how to display overdue items, and whether the interface should remember the
last filter. The group decided to keep the first version small and review
feedback before adding reminders or reports.

At the end of the day we discussed a separate billing problem. If a customer
retries a payment after a network timeout, the server should reuse the
original result. An idempotency key identifies the original operation and
prevents the customer from being charged twice.
"""

tokens = embedding_model.tokenizer(
    text, truncation=False, add_special_tokens=True
)["input_ids"]

print("Note tokens:", len(tokens))
print("Model input limit:", embedding_model.max_seq_length)
print("Embedding shape:", embedding_model.encode(text).shape)

# PS C:\Users\www14\Desktop\master\CODING\VN> Get-Content -Raw .\tests\test_emb_limit.py | docker compose -f docker-compose.cpu.yml exec -T backend python -
# Token indices sequence length is longer than the specified maximum sequence length for this model
#  (310 > 256). Running this sequence through the model will result in indexing errors
# Note tokens: 310
# Model input limit: 256
# Embedding shape: (384,)

