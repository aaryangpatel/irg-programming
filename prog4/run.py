"""Prog 4: Indexing and BM25 retrieval with Whoosh."""

import shutil
import sys
from pathlib import Path

from whoosh import index
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import ID, TEXT, Schema
from whoosh.qparser import QueryParser
from whoosh.scoring import BM25F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mylib.document import load_documents
from mylib.request import load_requests
from mylib.trec import load_qrels, write_run
from mylib.text import tokenize

def build_index(corpus_path: str, index_dir: Path):
    """Index documents and print statistics."""
    if index_dir.exists():
        shutil.rmtree(index_dir)
    index_dir.mkdir(parents=True)

    schema = Schema(doc_id=ID(stored=True, unique=True), text=TEXT(analyzer=StemmingAnalyzer()))
    ix = index.create_in(str(index_dir), schema)
    writer = ix.writer()

    documents = load_documents(corpus_path)
    all_words = set()
    for doc in documents:
        writer.add_document(doc_id=doc.doc_id, text=doc.text)
        all_words.update(tokenize(doc.text))
    writer.commit()

    print(f"Documents indexed: {len(documents)}")
    print(f"Estimated Unique words: {len(all_words)}")

def search_bm25(index_dir: Path, query: str, top_k: int = 1000) -> list[tuple[str, int, float]]:
    """BM25 retrieval"""
    ix = index.open_dir(str(index_dir))
    
    with ix.searcher(weighting=BM25F()) as searcher:
        parser = QueryParser("text", schema=ix.schema)
        q = parser.parse(query)
        results = searcher.search(q, limit=top_k)
        return [(result["doc_id"], i + 1, result.score) for i, result in enumerate(results)]

def main():
    data_dir = ROOT / "data"
    index_dir = Path(__file__).parent / "index"
    corpus_path = str(data_dir / "neuclir3-small-corpus-eng.jsonl")

    build_index(corpus_path, index_dir)

    requests = load_requests(str(data_dir / "neuclir3-requests.jsonl"))
    all_runs: dict[str, list[tuple[str, int, float]]] = {}

    top3_path = Path(__file__).parent / "top3_rankings.txt"

    with open(top3_path, mode="w", encoding="utf-8") as top3_out:
        for req in requests:
            ranking = search_bm25(index_dir, req.title, top_k=1000)
            all_runs[req.request_id] = ranking
            for doc_id, rank, score in ranking[:3]:
                top3_out.write(f"{req.request_id}\t{doc_id}\t{rank}\t{score}\n")
                print(f"{req.request_id} Rank {rank}: {doc_id} Score={score:.4f}")
            top3_out.write("\n")
            print()

    run_path = Path(__file__).parent / "bm25.run"
    top100 = {qid: docs[:100] for qid, docs in all_runs.items()}
    write_run(str(run_path), top100, "bm25")

    qrels = load_qrels(str(data_dir / "neuclir3.qrel"))
    from mylib.trec import average_precision, ndcg_at_k

    maps = []
    ndcgs = []
    for qid in qrels:
        if qid in all_runs:
            doc_ids = [d for d, _, _ in all_runs[qid]]
            maps.append(average_precision(qrels[qid], doc_ids))
            ndcgs.append(ndcg_at_k(qrels[qid], doc_ids, k=20))

    print(f"MAP: {sum(maps)/len(maps):.4f}")
    print(f"ndcg@20: {sum(ndcgs)/len(ndcgs):.4f}")
    print(f"num_q: {len(qrels)}")

if __name__ == "__main__":
    main()
