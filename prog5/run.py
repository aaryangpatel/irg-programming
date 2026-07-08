"""Prog 5: NDCG evaluation, significance testing, and LLM judge."""

import json
import os
import sys
import time
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from dotenv import load_dotenv
from openai import OpenAI, RateLimitError
from scipy import stats
from tabulate import tabulate

ROOT = Path(__file__).resolve().parents[1]
PROG5_DIR = Path(__file__).parent
sys.path.insert(0, str(ROOT / "src"))

from mylib.request import load_requests
from mylib.trec import load_qrels, load_run, ndcg_at_k, write_qrels

load_dotenv(dotenv_path=ROOT / ".env/irgprog.env")

K = 20
MODEL = "gpt-oss-20b:free"

DATA_DIR = ROOT / "data"
YOUR_RUN_PATH = ROOT / "prog4/bm25_full.run"
OTHER_RUNS = [
    ("BM25 (title)", ROOT / "prog4/bm25.run"),
    ("Prog1", ROOT / "prog4/prog1.run"),
]

JUDGE_PROMPT = """Instruction: You are an expert assessor making TREC relevance judgments.
You will be given a TREC topic and a portion of a document.
If any part of the document is relevant to the topic, answer "Yes".
If not, answer "No". Remember that the TREC relevance condition
states that a document is relevant to a topic if it contains information
that is helpful in satisfying the user's information need described by
the topic. A document is judged relevant if it contains information
that is on-topic and of potential value to the user.
Topic: {topic}
Document: {document}
Relevant?"""

def per_query_ndcg(qrels: dict, run: dict, k: int = K) -> dict[str, float]:
    """Compute NDCG@k per query."""
    scores = {}
    for qid in qrels:
        if qid in run:
            doc_ids = [doc_id for doc_id, _, _ in run[qid]]
            scores[qid] = ndcg_at_k(qrels[qid], doc_ids, k=k)
    return scores

def stderr(values: list[float]) -> float:
    """Standard error of the mean."""
    return float(np.std(values, ddof=1) / np.sqrt(len(values)))

def se_overlap(mean_a: float, se_a: float, mean_b: float, se_b: float) -> bool:
    """True if error bars do not overlap."""
    return (mean_a + se_a < mean_b - se_b) or (mean_b + se_b < mean_a - se_a)

def significance_arrow(p_value: float, mean_ref: float, mean_other: float) -> str:
    """Return (^), (v), or (?) for paired t-test result."""
    if p_value >= 0.05:
        return "(?)"
    if mean_other > mean_ref:
        return "(^)"
    return "(v)"

def load_plaidx_docs() -> dict[str, str]:
    """Load document text from PlaidX retrieved docs."""
    docs_by_id = {}
    with open(DATA_DIR / "plaidx_rankings/neuclir3-retrieved_docs.jsonl", encoding="utf-8") as f:
        for line in f:
            entry = json.loads(line)
            for ranked in entry.get("ranked_docs", []):
                doc = ranked["doc"]
                docs_by_id[doc["id"]] = doc["text"]
    return docs_by_id

def llm_judge(topic: str, document: str, client: OpenAI) -> int:
    """Return 1 if relevant, 0 if not."""
    prompt = JUDGE_PROMPT.format(topic=topic, document=document[:3000])
    for attempt in range(3):
        try:
            resp = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.0,
                timeout=45,
            )
            answer = resp.choices[0].message.content.strip().lower()
            if answer.startswith("yes"):
                return 1
            if answer.startswith("no"):
                return 0
        except RateLimitError:
            time.sleep(20)
    return 0

def build_llm_qrels(requests_by_id: dict, plaidx_run: dict, docs_by_id: dict, client: OpenAI, qrels_path: Path) -> dict:
    """LLM judgments for top PlaidX documents."""
    llm_qrels = load_qrels(str(qrels_path)) if qrels_path.exists() else {}

    for qid, rankings in plaidx_run.items():
        llm_qrels.setdefault(qid, {})
        topic = requests_by_id[qid].title
        for doc_id, _, _ in rankings[:K]:
            if doc_id in llm_qrels[qid]:
                continue
            rel = llm_judge(topic, docs_by_id[doc_id], client)
            llm_qrels[qid][doc_id] = rel
            write_qrels(str(qrels_path), llm_qrels)
    return llm_qrels

def evaluate_pair(qrels: dict, run_ref: dict, run_other: dict) -> dict:
    """Compute NDCG@20 comparison stats for two runs."""
    ref_scores = per_query_ndcg(qrels, run_ref)
    other_scores = per_query_ndcg(qrels, run_other)
    qids = sorted(set(ref_scores) & set(other_scores))
    ref_vals = [ref_scores[q] for q in qids]
    other_vals = [other_scores[q] for q in qids]

    mean_ref = float(np.mean(ref_vals))
    mean_other = float(np.mean(other_vals))
    se_ref = stderr(ref_vals)
    se_other = stderr(other_vals)
    _, p_value = stats.ttest_rel(other_vals, ref_vals)

    return {
        "qids": qids,
        "ref_scores": ref_scores,
        "other_scores": other_scores,
        "mean_ref": mean_ref,
        "mean_other": mean_other,
        "se_ref": se_ref,
        "se_other": se_other,
        "var_ref": float(np.var(ref_vals, ddof=1)),
        "var_other": float(np.var(other_vals, ddof=1)),
        "std_ref": float(np.std(ref_vals, ddof=1)),
        "std_other": float(np.std(other_vals, ddof=1)),
        "p_value": float(p_value),
        "arrow": significance_arrow(p_value, mean_ref, mean_other),
        "se_overlap": se_overlap(mean_ref, se_ref, mean_other, se_other),
    }

def print_report(manual: dict, llm_eval: dict) -> None:
    """Print per-query scores, summary table, and stats"""
    rows = [
        [q, f"{manual['ref_scores'][q]:.4f}", f"{manual['other_scores'][q]:.4f}"]
        for q in manual["qids"]
    ]
    rows.append(["All", f"{manual['mean_ref']:.4f}", f"{manual['mean_other']:.4f}"])
    print("=== Per-query NDCG@20 (manual qrels) ===")
    print(tabulate(rows, headers=["Query", "PlaidX", "BM25 (full query)"], tablefmt="grid"))
    print()

    summary = [
        ["PlaidX", f"{manual['mean_ref']:.4f}", f"+/- {manual['se_ref']:.4f}",
         f"{llm_eval['mean_ref']:.4f}", f"+/- {llm_eval['se_ref']:.4f}"],
        ["BM25 (full query)", f"{manual['mean_other']:.4f}", f"+/- {manual['se_other']:.4f} {manual['arrow']}",
         f"{llm_eval['mean_other']:.4f}", f"+/- {llm_eval['se_other']:.4f} {llm_eval['arrow']}"],
    ]
    print("=== Results (PlaidX vs BM25) ===")
    print(tabulate(summary, headers=["Method", f"NDCG@{K} manual", "Stderr", f"NDCG@{K} LLM", "Stderr"], tablefmt="grid"))
    print()

    stats = []
    for label, result in [("Manual", manual), ("LLM", llm_eval)]:
        stats.append([
            label,
            f"{result['var_ref']:.4f}", f"{result['std_ref']:.4f}", f"{result['se_ref']:.4f}",
            f"{result['var_other']:.4f}", f"{result['std_other']:.4f}", f"{result['se_other']:.4f}",
            str(result["se_overlap"]),
            f"{result['p_value']:.4f} {result['arrow']}",
        ])
    print("=== Stats ===")
    print(tabulate(
        stats,
        headers=["Qrels", "PlaidX var", "PlaidX std", "PlaidX stderr",
                 "BM25 var", "BM25 std", "BM25 stderr", "SE overlap sig", "t-test"],
        tablefmt="grid",
    ))
    print()

def compare_all_methods(qrels: dict, plaidx_run: dict):
    """Compare all retrieval methods (Task 6)."""
    plaidx_scores = per_query_ndcg(qrels, plaidx_run)
    plaidx_vals = list(plaidx_scores.values())
    rows = [["PlaidX", f"{np.mean(plaidx_vals):.4f}", f"+/- {stderr(plaidx_vals):.4f}"]]
    for label, run_path in OTHER_RUNS:
        vals = list(per_query_ndcg(qrels, load_run(str(run_path))).values())
        rows.append([label, f"{np.mean(vals):.4f}", f"+/- {stderr(vals):.4f}"])

    print("=== All Retrieval Methods (manual qrels) ===")
    print(tabulate(rows, headers=["Method", f"NDCG@{K}", "Stderr"], tablefmt="grid"))
    print()

def save_plot(manual: dict, llm_eval: dict):
    methods = ["PlaidX", "BM25 (full query)"]
    x = np.arange(len(methods))
    width = 0.35
    fig, ax = plt.subplots()
    ax.bar(x - width / 2, [manual["mean_ref"], manual["mean_other"]], width,
           yerr=[manual["se_ref"], manual["se_other"]], capsize=5, label="Manual")
    ax.bar(x + width / 2, [llm_eval["mean_ref"], llm_eval["mean_other"]], width,
           yerr=[llm_eval["se_ref"], llm_eval["se_other"]], capsize=5, label="LLM")
    ax.set_ylabel(f"NDCG@{K}")
    ax.set_title("Evaluation Measure by Method and Ground Truth")
    ax.set_xticks(x)
    ax.set_xticklabels(methods)
    ax.legend()
    plt.savefig(PROG5_DIR / "evaluation_plot.png")
    plt.close()

def main():
    qrels = load_qrels(str(DATA_DIR / "neuclir3.qrel"))
    plaidx_run = load_run(str(DATA_DIR / "plaidx_rankings/neuclir3-plaidx.run"))
    your_run = load_run(str(YOUR_RUN_PATH))
    requests = {r.request_id: r for r in load_requests(str(DATA_DIR / "neuclir3-requests.jsonl"))}

    manual = evaluate_pair(qrels, plaidx_run, your_run)
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=os.environ["OPENROUTER_API_KEY"])
    llm_qrels = build_llm_qrels(requests, plaidx_run, load_plaidx_docs(), client, PROG5_DIR / "llm_judgments.qrel")
    llm_eval = evaluate_pair(llm_qrels, plaidx_run, your_run)

    print_report(manual, llm_eval)
    compare_all_methods(qrels, plaidx_run)
    save_plot(manual, llm_eval)

if __name__ == "__main__":
    main()