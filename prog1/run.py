"""Prog 1: Simple Retrieval System"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mylib.document import Document, load_documents
from mylib.request import load_requests
from mylib.text import tokenize

def count_matches(query_words: list[str], doc_words: list[str]) -> tuple[int, int, list[str]]:
    """Return total matches, unique matches, and matching words."""
    query_set = set(query_words)
    matching_words = [w for w in doc_words if w in query_set]
    unique_matching_words = list(set(matching_words))
    return len(matching_words), len(unique_matching_words), unique_matching_words

def rank_score(query_words: list[str], document: Document) -> float:
    """Rank score = number of unique document words that match the query."""
    doc_words = tokenize(document.text)
    _, unique_count, _ = count_matches(query_words, doc_words)
    return float(unique_count)

def main():
    data_dir = ROOT / "data"
    requests = load_requests(str(data_dir / "neuclir3-requests.jsonl"))
    documents = load_documents(str(data_dir / "neuclir3-small-corpus-eng.jsonl"))

    print(f"Loaded {len(requests)} requests and {len(documents)} documents")
    print("Example request:\n", "ID: ", requests[0].request_id, "\n Title: ", requests[0].title)
    print("Example document:\n", "ID: ", documents[0].doc_id, "\n Text: ",documents[0].text[:100], "...")

    output_path = Path(__file__).parent / "rankings.txt"
    k = 3

    with open(output_path, mode="w", encoding="utf-8") as out:
        for req in requests:
            query_words = tokenize(req.title)

            # Report matches for a few documents
            print(f"\nQuery {req.request_id}: {req.title}")
            for doc in documents[:3]:
                doc_words = tokenize(doc.text)
                total, unique, words = count_matches(query_words, doc_words)
                print(f"  {doc.doc_id}: total={total}, unique={unique}, words={words[:10]}")

            # Sort with reverse=True so highest scores come first
            ranking = sorted(
                documents,
                key=lambda doc: rank_score(query_words, doc),
                reverse=True,
            )
            top_k = ranking[:k]

            # Write top ranked results to output file
            for rank, doc in enumerate(top_k, start=1):
                score = rank_score(query_words, doc)
                out.write(f"{req.request_id}\t{doc.doc_id}\t{rank}\t{score}\n")
                print(f"  rank {rank}: {doc.doc_id} score={score}")


if __name__ == "__main__":
    main()