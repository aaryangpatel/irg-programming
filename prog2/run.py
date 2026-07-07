"""Prog 2: Query LLMs with async, retries, and throttling."""

import asyncio
import os
import sys
from pathlib import Path

from aiolimiter import AsyncLimiter
from dotenv import load_dotenv
from openai import AsyncOpenAI, OpenAI, OpenAIError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
load_dotenv(dotenv_path=ROOT / ".env/irgprog.env")

from mylib.document import load_documents
from mylib.request import load_requests

BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "gpt-oss-20b:free"
MAX_ATTEMPTS = 3
LIMITER = AsyncLimiter(max_rate=3, time_period=60)

def make_prompt(title: str) -> str:
    """Build a user prompt from a request title."""
    return f"Write two bullet points about: {title}"

def sync_generate(requests: list):
    """Synchronous LLM calls."""
    client = OpenAI(
        base_url=BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    for req in requests:
        resp = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": make_prompt(req.title)},
            ],
            temperature=0.3,
        )
        response = resp.choices[0].message.content
        print(f"{req.request_id}: {response}")

async def ask_once(client: AsyncOpenAI, prompt: str) -> str:
    """Single async LLM call with retries and error handling."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            async with LIMITER:
                resp = await client.chat.completions.create(
                    model=MODEL,
                    messages=[
                        {"role": "system", "content": "You are concise and helpful."},
                        {"role": "user", "content": prompt},
                    ],
                    temperature=0.3,
                )
            return resp.choices[0].message.content
        
        except OpenAIError as e:
            status = getattr(e, "status_code", None)
            permanent = status in (400, 401, 403, 404)
            if permanent or attempt == MAX_ATTEMPTS:
                print(f"Error {e}. Stopping.")
                raise
            
            wait = 10 * attempt
            print(f"Error {e}. Retrying in {wait}s...")
            await asyncio.sleep(wait)
    
    return ""

async def async_generate(requests: list):
    """Async LLM calls with throttling and retries."""
    client = AsyncOpenAI(
        base_url=BASE_URL,
        api_key=os.environ["OPENROUTER_API_KEY"],
    )
    prompts = [make_prompt(req.title) for req in requests]
    coroutines = [ask_once(client, p) for p in prompts]
    answers = await asyncio.gather(*coroutines)
    
    for req, answer in zip(requests, answers):
        print(f"{req.request_id}: {answer}")

def dspy():
    import dspy

    documents = load_documents(str(ROOT / "data/neuclir3-small-corpus-eng.jsonl"))
    document_text = documents[0].text

    lm = dspy.LM(
        model=f"openai/{MODEL}",
        api_key=os.environ["OPENROUTER_API_KEY"],
        api_base=BASE_URL,
    )
    dspy.configure(lm=lm)
    predict = dspy.Predict("document -> summary")
    result = predict(document=document_text)
    print(f"{result.summary}")

def main():
    requests = load_requests(str(ROOT / "data/neuclir3-requests.jsonl"))
    print("=== Sync ===")
    sync_generate(requests)
    print("\n=== Async with Retries and Throttling ===")
    asyncio.run(async_generate(requests))
    print("\n=== DSPy Example ===")
    dspy()

if __name__ == "__main__":
    main()