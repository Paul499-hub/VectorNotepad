## Create test env
```
python -m venv .venv-tests
```

## Install deps
```
.\.venv-tests\Scripts\python.exe -m pip install pytest qdrant-client==1.16.1 sqlalchemy==2.0.41 pydantic==2.12.5 python-dotenv==1.2.1 Markdown==3.8.1 Pygments==2.19.1
```

## Run test example
```
.\.venv-tests\Scripts\python.exe -m pytest tests/test_note_references.py -v
```
