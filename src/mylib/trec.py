import math
from collections import defaultdict

def load_qrels(path: str) -> dict[str, dict[str, int]]:
    """Load qrels file: query_id -> doc_id -> relevance."""
    qrels: dict[str, dict[str, int]] = defaultdict(dict)
    with open(path, mode="r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 4:
                qid, _, doc_id, rel = parts[0], parts[1], parts[2], int(parts[3])
                qrels[qid][doc_id] = rel
    return dict(qrels)

def load_run(path: str) -> dict[str, list[tuple[str, int, float]]]:
    """Load TREC run file: query_id -> [(doc_id, rank, score), ...]."""
    runs: dict[str, list[tuple[str, int, float]]] = defaultdict(list)
    with open(path, mode="r", encoding="utf-8") as f:
        for line in f:
            parts = line.split()
            if len(parts) >= 5:
                qid, _, doc_id, rank, score = parts[0], parts[1], parts[2], int(parts[3]), float(parts[4])
                runs[qid].append((doc_id, rank, score))
    return dict(runs)

def write_run(path: str, runs: dict[str, list[tuple[str, int, float]]], method: str):
    """Write rankings in TREC run format."""
    with open(path, mode="w", encoding="utf-8") as f:
        for qid in sorted(runs.keys()):
            for doc_id, rank, score in runs[qid]:
                f.write(f"{qid} Q0 {doc_id} {rank} {score} {method}\n")

def write_qrels(path: str, qrels: dict[str, dict[str, int]]) -> None:
    """Write qrels in trec_eval format."""
    with open(path, mode="w", encoding="utf-8") as f:
        for qid in sorted(qrels.keys()):
            for doc_id, rel in sorted(qrels[qid].items()):
                f.write(f"{qid} 0 {doc_id} {rel}\n")

def ndcg_at_k(qrels: dict[str, int], ranking: list[str], k: int = 20) -> float:
    """Compute NDCG@k for one query."""
    gains = []
    for doc_id in ranking[:k]:
        rel = qrels.get(doc_id, 0)
        gains.append(rel)

    dcg = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(gains))

    ideal = sorted(qrels.values(), reverse=True)[:k]
    idcg = sum((2**g - 1) / math.log2(i + 2) for i, g in enumerate(ideal))
    if idcg == 0:
        return 0.0
    return dcg / idcg