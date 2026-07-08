"""Prog 4: Indexing and BM25 retrieval with Whoosh."""

import shutil
import subprocess
import sys
from pathlib import Path

from whoosh import index
from whoosh.analysis import StemmingAnalyzer
from whoosh.fields import ID, TEXT, Schema
from whoosh.qparser import AndGroup, OrGroup, QueryParser
from whoosh.scoring import BM25F

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from mylib.document import Document, load_documents
from mylib.request import Request, load_requests
from mylib.trec import write_run
from mylib.text import tokenize

PROG4_DIR = Path(__file__).parent
INDEX_DIR = PROG4_DIR / "index"
DATA_DIR = ROOT / "data"
QREL_PATH = DATA_DIR / "neuclir3.qrel"
CORPUS_PATH = DATA_DIR / "neuclir3-small-corpus-eng.jsonl"
REQUESTS_PATH = DATA_DIR / "neuclir3-requests.jsonl"
TREC_EVAL = ROOT / "tools/trec_eval/trec_eval"
EVAL_RESULTS_PATH = PROG4_DIR / "eval_results.txt"
PLAIDX_RUN_PATH = DATA_DIR / "plaidx_rankings/neuclir3-plaidx.run"

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
    print(f"Estimated unique words: {len(all_words)}")

def search_bm25(index_dir: Path, query: str, top_k: int = 1000, use_or_group: bool = False) -> list[tuple[str, int, float]]:
    """BM25 retrieval"""
    ix = index.open_dir(str(index_dir))
    with ix.searcher(weighting=BM25F()) as searcher:
        group = OrGroup if use_or_group else AndGroup
        parser = QueryParser("text", schema=ix.schema, group=group)
        q = parser.parse(query)
        results = searcher.search(q, limit=top_k)
        return [(result["doc_id"], i + 1, result.score) for i, result in enumerate(results)]

def build_full_query(req: Request) -> str:
    """Combine title, background, and problem statement into one query."""
    return " ".join([req.title, req.background, req.problem_statement])

def build_prog1_query(req: Request) -> list[str]:
    """Build the Prog 1 tokenized query from all request fields."""
    return tokenize(build_full_query(req), remove_stopwords=True)

def prog1_rank_score(query_words: list[str], document: Document) -> float:
    """Prog 1 rank score: count of unique query words found in the document."""
    doc_words = tokenize(document.text, remove_stopwords=True)
    return float(len(set(query_words) & set(doc_words)))

def generate_prog1_run(requests: list[Request], documents: list[Document], run_path: Path, top_k: int = 100) -> dict[str, list[tuple[str, int, float]]]:
    """Generate a TREC run file using the Prog 1 word-overlap ranking."""
    all_runs: dict[str, list[tuple[str, int, float]]] = {}
    for req in requests:
        query_words = build_prog1_query(req)
        ranking = sorted(documents, key=lambda doc: prog1_rank_score(query_words, doc), reverse=True)
        all_runs[req.request_id] = [
            (doc.doc_id, rank, prog1_rank_score(query_words, doc))
            for rank, doc in enumerate(ranking[:top_k], start=1)
        ]
    write_run(str(run_path), all_runs, "prog1")
    return all_runs

def run_trec_eval(trec_eval: Path, qrel_path: Path, run_path: Path) -> dict[str, float]:
    """Run trec_eval and return map, ndcg_cut.20, and num_q for all queries."""
    result = subprocess.run(
        [
            str(trec_eval),
            "-m",
            "map",
            "-m",
            "ndcg_cut.20",
            "-m",
            "num_q",
            str(qrel_path),
            str(run_path),
        ],
        capture_output=True,
        text=True,
        check=True,
    )

    metrics: dict[str, float] = {}
    for line in result.stdout.splitlines():
        parts = line.split()
        if len(parts) >= 3 and parts[1] == "all":
            metric_name = parts[0]
            if metric_name in {"map", "ndcg_cut_20", "num_q", "num_ret", "num_rel", "num_rel_ret"}:
                metrics[metric_name] = float(parts[2])
    return metrics

def evaluate_runs(runs: list[tuple[str, Path]], qrel_path: Path, trec_eval: Path) -> str:
    """Evaluate each run with trec_eval and return a formatted comparison report."""
    lines: list[str] = []
    for label, run_path in runs:
        metrics = run_trec_eval(trec_eval, qrel_path, run_path)
        lines.append(f"=== {label} ===")
        lines.append(f"map: {metrics.get('map', 0.0):.4f}")
        lines.append(f"ndcg@20: {metrics.get('ndcg_cut_20', 0.0):.4f}")
        lines.append(f"num_q: {int(metrics.get('num_q', 0))}")
        lines.append("")

        print(f"{label}")
        print(f"  map: {metrics.get('map', 0.0):.4f}")
        print(f"  ndcg@20: {metrics.get('ndcg_cut_20', 0.0):.4f}")
        print(f"  num_q: {int(metrics.get('num_q', 0))}")
        print()
    return "\n".join(lines)

def main():
    build_index(str(CORPUS_PATH), INDEX_DIR)

    requests = load_requests(str(REQUESTS_PATH))
    documents = load_documents(str(CORPUS_PATH))
    all_runs: dict[str, list[tuple[str, int, float]]] = {}
    full_runs: dict[str, list[tuple[str, int, float]]] = {}

    top3_path = PROG4_DIR / "top3_rankings.txt"
    with open(top3_path, mode="w", encoding="utf-8") as top3_out:
        for req in requests:
            ranking = search_bm25(INDEX_DIR, req.title, top_k=1000)
            all_runs[req.request_id] = ranking
            full_runs[req.request_id] = search_bm25(
                INDEX_DIR, build_full_query(req), top_k=1000, use_or_group=True
            )

            for doc_id, rank, score in ranking[:3]:
                top3_out.write(f"{req.request_id}\t{doc_id}\t{rank}\t{score}\n")
                print(f"{req.request_id} Rank {rank}: {doc_id} Score={score:.4f}")
            top3_out.write("\n")
            print()

    bm25_run_path = PROG4_DIR / "bm25.run"
    bm25_full_run_path = PROG4_DIR / "bm25_full.run"
    prog1_run_path = PROG4_DIR / "prog1.run"

    write_run(str(bm25_run_path), {qid: docs[:100] for qid, docs in all_runs.items()}, "bm25")
    write_run(str(bm25_full_run_path), {qid: docs[:100] for qid, docs in full_runs.items()}, "bm25_full")
    generate_prog1_run(requests, documents, prog1_run_path, top_k=100)

    eval_report = evaluate_runs(
        [
            ("bm25 (title only)", bm25_run_path),
            ("bm25 (full query)", bm25_full_run_path),
            ("prog1 (word overlap)", prog1_run_path),
            ("plaidx (baseline)", PLAIDX_RUN_PATH),
        ],
        QREL_PATH,
        TREC_EVAL,
    )
    EVAL_RESULTS_PATH.write_text(eval_report, encoding="utf-8")

if __name__ == "__main__":
    main()
