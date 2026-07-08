"""Prog 6: Learning-to-Rank"""

import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PROG6 = Path(__file__).parent
FEATURE_DIR = PROG6 / "features"
OUT_DIR = PROG6 / "out"
RANKLIB_JAR = ROOT / "RankLib-2.18.jar"
sys.path.insert(0, str(ROOT / "src"))

from mylib.trec import load_qrels, load_run, write_run

TRAIN_QUERIES = ["324", "361"]
TEST_QUERY = "387"
MAX_ITER = 100
FEATURE_NAMES = ["bm25_score", "bm25_rr", "plaidx_score", "plaidx_rr"]

def build_features(bm25_run: dict[str, list[tuple[str, int, float]]], plaidx_run: dict[str, list[tuple[str, int, float]]]) -> dict[str, dict[str, list[float]]]:
    """Build 4-feature vectors by unioning BM25 and PlaidX runs: BM25 score/reciprocal & PlaidX score/reciprocal."""
    features: dict[str, dict[str, list[float]]] = {}
    all_qids = set(bm25_run.keys()) | set(plaidx_run.keys())

    for qid in all_qids:
        doc_feats: dict[str, list[float]] = {}

        for doc_id, rank, score in bm25_run.get(qid, []):
            doc_feats[doc_id] = [score, 1.0 / rank, 0.0, 0.0]

        for doc_id, rank, score in plaidx_run.get(qid, []):
            if doc_id in doc_feats:
                doc_feats[doc_id][2] = score
                doc_feats[doc_id][3] = 1.0 / rank
            else:
                doc_feats[doc_id] = [0.0, 0.0, score, 1.0 / rank]

        features[qid] = doc_feats
    return features

def write_binary_qrels(path: Path, qrels: dict[str, dict[str, int]]):
    """Write binary qrels (0/1) for RankLib MAP evaluation."""
    with open(path, mode="w", encoding="utf-8") as f:
        for qid in sorted(qrels.keys()):
            for doc_id, rel in sorted(qrels[qid].items()):
                f.write(f"{qid} 0 {doc_id} {1 if rel > 0 else 0}\n")

def write_svm_file(path: Path, qids: list[str], features: dict[str, dict[str, list[float]]], qrels: dict[str, dict[str, int]]):
    """Write SVMlight feature file."""
    lines: list[str] = []
    for qid in qids:
        for doc_id, feats in sorted(features[qid].items()):
            label = 1 if qrels[qid].get(doc_id, 0) > 0 else 0
            feat_str = " ".join(f"{i + 1}:{value}" for i, value in enumerate(feats))
            lines.append(f"{label} qid:{qid} {feat_str} # {doc_id}")

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")

def prepare_data(bm25_run: dict, plaidx_run: dict, qrels: dict[str, dict[str, int]]) -> tuple[Path, Path, Path, Path, dict[str, dict[str, list[float]]]]:
    """Export train/test SVMlight files and qrels for RankLib."""
    features = build_features(bm25_run, plaidx_run)

    train_path = FEATURE_DIR / "train.txt"
    test_path = FEATURE_DIR / "test.txt"
    train_qrel_path = FEATURE_DIR / "train.qrel"
    test_qrel_path = FEATURE_DIR / "test.qrel"

    train_qrels = {q: qrels[q] for q in TRAIN_QUERIES}
    test_qrels = {q: qrels[q] for q in [TEST_QUERY]}

    write_svm_file(train_path, TRAIN_QUERIES, features, qrels)
    write_svm_file(test_path, [TEST_QUERY], features, qrels)
    write_binary_qrels(train_qrel_path, train_qrels)
    write_binary_qrels(test_qrel_path, test_qrels)

    return train_path, test_path, train_qrel_path, test_qrel_path, features

def run_ranklib(args: list[str]) -> str:
    """Run RankLib quietly; return stdout for MAP parsing."""
    cmd = ["java", "-jar", str(RANKLIB_JAR), "-silent", *args]
    result = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return result.stdout

def parse_ranklib_map(text: str) -> float:
    """Extract MAP from RankLib stdout."""
    match = re.search(r"MAP on (?:training|test) data:\s*([\d.eE+-]+)", text)
    return float(match.group(1))

def scores_to_run(test_path: Path, score_path: Path) -> dict[str, list[tuple[str, int, float]]]:
    """Convert RankLib score file + test feature file into a TREC run."""
    test_lines = test_path.read_text(encoding="utf-8").splitlines()
    doc_ids = [line.split("#", maxsplit=1)[1].strip() for line in test_lines]
    qids = [line.split("qid:", maxsplit=1)[1].split()[0] for line in test_lines]

    scores_by_index: dict[int, float] = {}
    for score_line in score_path.read_text(encoding="utf-8").splitlines():
        parts = score_line.strip().split()
        if len(parts) >= 3:
            scores_by_index[int(parts[1])] = float(parts[2])
        elif len(parts) == 1:
            scores_by_index[len(scores_by_index)] = float(parts[0])

    by_qid: dict[str, list[tuple[str, float]]] = {}
    for index, (qid, doc_id) in enumerate(zip(qids, doc_ids)):
        score = scores_by_index.get(index, 0.0)
        by_qid.setdefault(qid, []).append((doc_id, score))

    runs: dict[str, list[tuple[str, int, float]]] = {}
    for qid, doc_scores in by_qid.items():
        doc_scores.sort(key=lambda item: item[1], reverse=True)
        runs[qid] = [
            (doc_id, rank, score) for rank, (doc_id, score) in enumerate(doc_scores, start=1)
        ]
    return runs

def train_and_predict(train_path: Path, test_path: Path, train_qrel_path: Path, test_qrel_path: Path, zscore: bool) -> dict:
    """Train RankLib coordinate ascent and predict on query 387."""
    tag = "zscore" if zscore else "raw"
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    model_path = OUT_DIR / f"l2r-{tag}-model.txt"
    score_path = OUT_DIR / f"l2r-{tag}-scores.txt"
    run_path = OUT_DIR / f"l2r-{tag}.run"

    train_cmd = [
        "-train", str(train_path),
        "-ranker", "4",
        "-metric2t", "MAP",
        "-qrel", str(train_qrel_path),
        "-save", str(model_path),
        "-i", str(MAX_ITER),
    ]
    if zscore:
        train_cmd.extend(["-norm", "zscore"])

    run_ranklib(train_cmd)
    norm_args = ["-norm", "zscore"] if zscore else []

    train_map = parse_ranklib_map(run_ranklib([
        "-load", str(model_path),
        "-test", str(train_path),
        "-metric2T", "MAP",
        "-qrel", str(train_qrel_path),
        *norm_args,
    ]))

    run_ranklib([
        "-load", str(model_path),
        "-rank", str(test_path),
        "-score", str(score_path),
        *norm_args,
    ])

    runs = scores_to_run(test_path, score_path)
    write_run(str(run_path), runs, "l2r")

    test_map = parse_ranklib_map(run_ranklib([
        "-load", str(model_path),
        "-test", str(test_path),
        "-metric2T", "MAP",
        "-qrel", str(test_qrel_path),
        *norm_args,
    ]))

    print(f"  {tag}: Train MAP={train_map:.4f}  Test MAP={test_map:.4f}")

    return {
        "train_map": train_map,
        "test_map": test_map,
        "model": str(model_path.relative_to(PROG6)),
        "run": str(run_path.relative_to(PROG6)),
    }

def main():
    for path in (FEATURE_DIR, OUT_DIR):
        if path.exists():
            shutil.rmtree(path)

    qrels = load_qrels(str(ROOT / "data/neuclir3.qrel"))
    train_path, test_path, train_qrel_path, test_qrel_path, _ = prepare_data(
        load_run(str(ROOT / "prog4/bm25.run")),
        load_run(str(ROOT / "data/plaidx_rankings/neuclir3-plaidx.run")),
        qrels,
    )

    print("Training RankLib models...")
    raw = train_and_predict(train_path, test_path, train_qrel_path, test_qrel_path, zscore=False)
    zscore = train_and_predict(train_path, test_path, train_qrel_path, test_qrel_path, zscore=True)

    delta_test = zscore["test_map"] - raw["test_map"]
    if delta_test > 0.001:
        verdict = "Z-score normalization helps on the test query."
    elif delta_test < -0.001:
        verdict = "Z-score normalization hurts on the test query."
    else:
        verdict = "Z-score normalization has little or no effect on the test query."

    print(f"Test delta: {delta_test:+.4f} — {verdict}")

    best = zscore if zscore["test_map"] >= raw["test_map"] else raw
    shutil.copy2(PROG6 / best["run"], PROG6 / "l2r.run")
    (PROG6 / "l2r_model.json").write_text(json.dumps({
        "normalization": "zscore" if best is zscore else "raw",
        "train_map": best["train_map"],
        "test_map": best["test_map"],
        "model": best["model"],
        "features": FEATURE_NAMES,
    }, indent=2), encoding="utf-8")

    (PROG6 / "zscore_comparison.txt").write_text(
        f"Z-score Normalization\n"
        f"{'=' * 45}\n\n"
        f"Raw train MAP:     {raw['train_map']:.4f}\n"
        f"Raw test MAP:      {raw['test_map']:.4f}\n\n"
        f"Z-score train MAP: {zscore['train_map']:.4f}\n"
        f"Z-score test MAP:  {zscore['test_map']:.4f}\n"
        f"Test delta: {delta_test:+.4f}\n"
        f"Conclusion: {verdict}\n",
        encoding="utf-8",
    )

if __name__ == "__main__":
    main()
