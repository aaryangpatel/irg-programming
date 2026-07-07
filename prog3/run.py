"""Prog 3: Web Search RAG pipeline."""

import json
import os
import sys
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from ddgs import DDGS
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(dotenv_path=ROOT / ".env/irgprog.env")

from mylib.request import Request, load_requests

BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "gpt-oss-20b:free"

class ReportMetadata(BaseModel):
    """RAGTIME report metadata."""
    team_id: str = "my-team"
    topic_id: str
    run_id: str = "web-rag"
    run_desc: str = "DuckDuckGo search + OpenRouter gpt"

class ResponseItem(BaseModel):
    """One sentence in a RAGTIME report with citations."""
    text: str
    citations: list[str]

class ReportRun(BaseModel):
    """RAGTIME report format for one request."""
    metadata: ReportMetadata
    responses: list[ResponseItem]
    references: list[str]

def build_search_query(req: Request) -> str:
    """Build a web search query from the request fields."""
    return " ".join([req.title, req.background, req.problem_statement])

def search_duckduckgo(query: str, max_results: int = 5) -> list[dict]:
    """Search via DuckDuckGo and return rank, url, and snippet."""
    results = []
    with DDGS(timeout=20) as ddgs:
        for i, item in enumerate(ddgs.text(query, max_results=max_results), start=1):
            results.append({
                "rank": i,
                "url": item.get("href", ""),
                "snippet": item.get("body", ""),
            })
    return results

def fetch_page_text(url: str) -> str:
    """Download a web page and extract visible text."""
    response = requests.get(url, timeout=20)
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, "html.parser")
        return soup.get_text()
    
    print("Error:", response.status_code)
    return ""

def generate_report(req: Request, results: list[dict]) -> ReportRun:
    """RAG: use DuckDuckGo snippets and OpenRouter to generate a report."""
    context_lines = []
    for result in results[:5]:
        context_lines.append(f"[{result['rank']}] {result['snippet']} ({result['url']})")
    
    context = "\n".join(context_lines)
    urls = [result["url"] for result in results if result.get("url")]

    client = OpenAI(
        base_url=BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    
    prompt = (
        f"Topic: {req.title}\n"
        f"Background: {req.background}\n"
        f"Problem: {req.problem_statement}\n"
        f"Sources:\n{context}\n"
        "Write a short report with exactly 3 factual sentences based on the sources. "
        "Only write factual sentences supported by the sources. Do not apologize or ask for more sources."
    )
    
    resp = client.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )
    
    text = resp.choices[0].message.content
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]

    responses = []
    for i, sentence in enumerate(sentences[:3]):
        cite = [urls[i]] if i < len(urls) else []
        responses.append(ResponseItem(text=sentence + ".", citations=cite))

    return ReportRun(
        metadata=ReportMetadata(topic_id=req.request_id),
        responses=responses,
        references=urls,
    )

def main():
    requests_list = load_requests(str(ROOT / "data/neuclir3-requests.jsonl"))
    output_path = Path(__file__).parent / "ragtime_reports.jsonl"

    with open(output_path, mode="w", encoding="utf-8") as out:
        for req in requests_list:
            print(f"\n=== {req.request_id}: {req.title} ===")
            query = build_search_query(req)

            results = search_duckduckgo(query)
            print(f"DuckDuckGo: {len(results)} results")
            for result in results[:3]:
                print(f"  Rank={result['rank']} URL={result['url']}")
                print(f"    Snippet={result['snippet'][:100]}...")

            if results and results[0].get("url"):
                content = fetch_page_text(results[0]["url"])
                print(f"Fetched page content: {content[:100]}...")

            report = generate_report(req, results)
            out.write(json.dumps(report.model_dump(), ensure_ascii=False) + "\n")
            
            print(f"Report for {req.request_id}")
            for item in report.responses:
                print(f"  - {item.text} citations={item.citations}")

if __name__ == "__main__":
    main()