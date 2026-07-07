from pydantic import BaseModel

class Document(BaseModel):
    """A document from neuclir3-small-corpus-eng.jsonl."""
    doc_id: str
    text: str

def load_documents(path: str) -> list[Document]:
    """Load all documents from a JSONL file."""
    documents = []
    with open(path, mode="r", encoding="utf-8") as f:
        for line in f.readlines():
            line = line.strip()
            if line:
                documents.append(Document.model_validate_json(line))
    return documents

def load_documents_by_id(path: str) -> dict[str, Document]: 
    """Load documents indexed by doc_id.""" 
    return {doc.doc_id: doc for doc in load_documents(path)}