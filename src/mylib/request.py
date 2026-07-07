from pydantic import BaseModel

class Request(BaseModel):
    """A request from neuclir3-requests.jsonl."""
    request_id: str
    title: str
    background: str = ""
    problem_statement: str = ""
    limit: int = 2000
    collection_ids: list[str] = []

def load_requests(path: str) -> list[Request]:
    """Load all requests from a JSONL file."""
    requests = []
    with open(path, mode="r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if line:
                requests.append(Request.model_validate_json(line))
    return requests
