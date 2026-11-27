import csv
import json
from pathlib import Path
from urllib.request import Request, urlopen

TEST_API_URL = "http://127.0.0.1:8000" # API url within docker since test module will run inside


def write_results_csv(filename: str, rows: list[dict], *, run_folder: str | None = None) -> Path:
    """Write a new CSV in tests/log or one of its run folders."""
    if Path(filename).name != filename or Path(filename).suffix.lower() != ".csv":
        raise ValueError("Provide a CSV filename without a directory")
    if not rows:
        raise ValueError("Provide at least one row to write")
    fieldnames = list(rows[0])
    if any(row.keys() != rows[0].keys() for row in rows):
        raise ValueError("All CSV rows must have the same columns")
    log_dir = Path(__file__).resolve().parent / "log"
    if run_folder is not None:
        if run_folder in {"", ".", ".."} or Path(run_folder).name != run_folder:
            raise ValueError("Provide a single run folder name")
        log_dir = log_dir / run_folder
    log_dir.mkdir(parents=True, exist_ok=True)
    path = log_dir / filename
    with path.open("x", encoding="utf-8", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    return path


def request(method, path, payload=None, *, timeout=30) -> dict | list | int | None:
    """## Build a request - get json parsed response"""
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    headers = {"Content-Type": "application/json"} if body is not None else {}
    req = Request(f"{TEST_API_URL}{path}", data=body, headers=headers, method=method)
    with urlopen(req, timeout=timeout) as response:
        data = response.read()
        return json.loads(data) if data else None


def create_test_note_chunks(test_case, text: str) -> dict:
    """
    ## Create a test note using test api's `/storage/save_note_chunks` \n
    and register it's cleanup (delete call)
    Example:\n
    ```
    # Inside the test method
    saved = create_test_note_chunks(self, note_text)
    ```
    """
    note = request("POST", "/storage/save_note_chunks", {"text": text})
    test_case.addCleanup(request, "DELETE", f"/storage/del/{note['id']}")
    return note

def create_test_note(test_case, text: str) -> dict:
    """
    ## Create a test note using test api's `/storage/save_note` \n
    and register it's cleanup (delete call)
    Example:\n
    ```
    # Inside the test method
    saved = create_test_note(self, note_text)
    ```
    """
    note = request("POST", "/storage/save_note", {"text": text})
    test_case.addCleanup(request, "DELETE", f"/storage/del/{note['id']}")
    return note
