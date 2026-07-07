# Prog 2: Query LLMs, Error handling, Retries, Async, and Throttling

In this assignment you will use LLMs with error handling, parallel requests, and throttling to meet rate limits.

**Learning goals**: 
- Working with endpoints 
- Parallelizing requests with async
- Handling network errors and resilient retries

You will be building on code from the previous assignment.


    ================================================================================
    Note: We are not directly using OpenAI's API Service. You don't need to purchase OpenAI credits.
    
    We are merely using the python library called `OpenAI`, which works with any LLM endpoint. We are using OpenRouter and will provide you with an API KEY.
    ================================================================================

Quickstart instructions from OpenRouter:
<https://openrouter.ai/docs/quickstart>

Models currently supported by OpenRouter:
<https://openrouter.ai/models>




# Task 0. Preparation of LLM API Keys


In order to access LLM endpoints you need a so-called "API Key".

We will provide you with a key for OpenRouter under the following policy:
* This key is **issued to you personally** for the **sole purpose** of doing **homework** for this course. 
* You **must not share** this key with anyone else. 
* You must **never** add the key directly to your **source code**.  
* You must **never** commit or push your key to a repository.  
* **If you accidentally commit your key, IMMEDIATELY notify the instructor** so we can deactivate the old key and re-issue a new one.


## Recommended Practice
1. Create a directory called `.env`. (Linux and macOS hide directories that start with `.`.)  
2. Make sure `.env` is listed in `.gitignore` so Git will never include it by mistake.  
3. Inside `.env`, create a file such as:

```
.env/
  irgprog.env
```
3. 4. Put your API keys in that file `.env/irgprog.env`, one per line, using uppercase variable names and no spaces:
```
export OPENAI_API_KEY=sk-...
export OPENROUTER_API_KEY=sk-or-...
export SERPAPI_API_KEY=...
```
4.  In your shell, load the file into your environment variables by typing:
```bash
source .env/irgprog.env
```
5.  Alternatively, load it in Python:
```python
import os
from dotenv import load_dotenv

load_dotenv(dotenv_path=".env/irgprog.env")  # choose the file explicitly
```

You can check that the key was loaded to the environment with `print(os.environ["OPENROUTER_API_KEY"])`


This way, your keys remain local, hidden, and never checked into version control.


# Task 1. Generate Responses with an LLM Endpoint

Load the requests from `./data/neuclir3-requests.jsonl`, use the LLM to generate a response for each request.

Here some starter code to query an LLM. Hint: please familiarize yourself with each component of this call (e.g `temperature`). 

```python
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"], # DO NOT SHARE. Do not add to source!!
    )
    resp = client.chat.completions.create(
        model="gpt-oss-20b:free",  # pick any OpenRouter model id, start with "free"
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Give me two bullet points on retrieval-augmented generation."},
        ],
        temperature=0.3,
    )
    response = resp.choices[0].message.content
    print("response=", response)
```

You can get a list of all "free" models here:
<https://openrouter.ai/models?max_price=0>

Once you know your code works, you can use a more expensive model.


# Task 2.  Async

When you run many LLM calls, code becomes slow if you send each request only after the previous one completes. To send multiple requests at the same time (concurrently) use asynchronous programming in Python. The core ideas are simple once you see the primitives.

Your task is to code an alternative to the previous task that makes use of async. (Please first try this with **less than 10 parallel calls**, the reasons will become clear in the remainder of this assignment.)

### Async Primitives

* **`async def`**
  Defines a special kind of function that does not run immediately; instead it produces a coroutine object, which is like a "to-do item" that describes the work to perform, and the event loop decides when to start it, pause it, and resume it while other tasks are also in progress.

* **`await`**
  This tells Python to pause the current async function until another coroutine (or other awaitable work) is finished, and while it is paused the event loop can run other coroutines; `await` is always used inside an `async def` function.

  * You can write `result = await some_coroutine()` to wait for one coroutine.

  * You can create a task with `task = asyncio.create_task(some_coroutine())` and later await task.

* **`asyncio.gather(*coroutines)`**
  Lets you wait for several coroutines or tasks that run at the same time. It starts them all together, when completed returns a list of their results in the same order you asked for them. If one of them fails, gather will normally stop and raise that error, but if you pass return_exceptions=True it will give you the exceptions alongside the results so you can handle them yourself.
  
  * `answers = await asyncio.gather(*coroutines)`
  
  Note the `*` in front of "coroutines" will unpack the lists elements into arguments for the gather function. This is also called the "splat operator", more info: <https://docs.python.org/3/tutorial/controlflow.html#unpacking-argument-lists>.

* **Event loop**
    The event loop is the manager that controls when each coroutine runs. All coroutines that you want to run in parallel must be part of the same event loop, because the loop is responsible for starting them, pausing them, and resuming them at the right times.

    * `asyncio.run(main_routine())` creates an event loop, runs the coroutine `main_routine` to completion.

More details on asyncio <https://docs.python.org/3/library/asyncio.html>

Here is a polished version in clear professional language, without contractions or dashes:


```python
# pip install "openai>=1.40"

import os
import asyncio
from openai import AsyncOpenAI

# --- Configure for OpenRouter (OpenAI-compatible endpoint) ---
BASE_URL = "..."
API_KEY_ENV = "..."
MODEL = "..."

async def async_generate():

    client = AsyncOpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.environ["OPENROUTER_API_KEY"],
    )

    async def ask_once(prompt: str) -> str:
        """
        One asynchronous call: returns the assistant message string.
        """
        resp = await client.chat.completions.create(
            model="gpt-oss-20b:free",
            messages=[
                {"role": "system", "content": "You are concise and helpful."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
        )
        return resp.choices[0].message.content

    async def loop():
        prompts = [
            "Define retrieval-augmented generation in one sentence.",
            "Name three pitfalls of LLM judges.",
            "Give one benefit of nugget-based evaluation.",
            "Three reasons why async helps with LLM batching.",
        ]

        # Run all the requests concurrently
        coroutines = [ask_once(p) for p in prompts]
        answers = await asyncio.gather(*coroutines)   # preserves order of 'prompts'

        # Pairs of LLM inputs and outputs
        for p, a in zip(prompts, answers):
            print(f"\nQ: {p}\nA: {a}")

    return await loop()

asyncio.run(async_generate())
```


### You need to use `AsyncOpenAI` with Async

From inside an `async def` function you can call other `async def` functions with `await` or call normal functions (`def`) directly.

Normal `def` functions will block the event loop, and no other work can be scheduled until they are completed. This is acceptable for functions that finish quickly or are *CPU bound*, such as math, data preparation, parsing results.

However, it is not appropriate to call blocking I/O functions, such as those that wait on the network, disk, or a database. In these cases the CPU is sitting idle while the program waits, but the event loop cannot switch to other coroutines because the function does not yield. This is why `await` is needed for true asynchronous functions: they give control back to the event loop while waiting.

Therefore you must use `AsyncOpenAI` when working with async and `await`.

* `AsyncOpenAI` methods are truly asynchronous: they return coroutines and yield control back to the event loop during network waits.
* `OpenAI` methods are synchronous: they directly execute their code, including waiting for responses from the LLM endpoint. Wrapping them in `async def` does not make them asynchronous; it only hides blocking behavior inside a coroutine.


## Common pitfalls

1. Forgetting to use `await` on a coroutine, which results in a coroutine object being returned instead of the actual value.
2. Mixing blocking I/O operations (such as the `requests` library) inside asynchronous code. In asynchronous programs, one must use asynchronous clients such as `AsyncOpenAI` or `aiohttp`.
3. Assuming that asynchronous programming improves performance for CPU-bound work. It does not. Asynchronous programming is helpful primarily for workloads that involve waiting for I/O, such as many concurrent HTTP calls.


# Task 3. Handling Network Errors


Whenever you issue a request over the network, be prepared for errors to occur. Adjust your code to handle network errors in an *appropriate* way.

In python you can catch exceptions with try/except:

```python
try:
    ...

except openai.OpenAIError as e:
  print("Caught exception {e} when issueing request ....")
  raise  # this will propagate the exception to the caller.
```

Often you want to wait a bit, then retry. 

```python
for attempt in range(1, MAX_ATTEMPTS + 1):
    try:
        ...
    except openai.OpenAIError as e:
      if attempt < MAX_ATTEMPTS:
        print(f"Error {e}. Retrying..")
        asyncio.sleep(10) # wait 10 seconds -- use `asyncio` in async context,  use `time` in normal functions
      else:
        print(f"Error {e}. Giving up!")
        raise   # you can also raise a new Error object
```


Be aware that there are two major classes of errors (**which the example code does not address**):

* **Transient errors** (timeouts, connection failures, 429, 500-504) these should be retried for a limited number of times, with a backoff, i.e., an increasing wait time in between retries.
* **Permanent errors** (400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found) should fail immediately, because they imply a mistake on your end.

Here a list of network errors, what they mean:
<https://www.restapitutorial.com/advanced/responses/retries>


General advice from AWS about how to handle "backoff": 
<https://aws.amazon.com/builders-library/timeouts-retries-and-backoff-with-jitter/>



### Network Errors



HTTP is often used as a transport protocol that runs on your internet connection. Here a list of errors that can arise from HTTP, their codes, and what they mean (e.g. 200 means "it worked"):
<https://developer.mozilla.org/en-US/docs/Web/HTTP/Reference/Status>

Many python libraries build on the `requests`, `httpx`, or `urllib3` libraries to handle HTTP communication. This means you may have to handle exceptions when things go wrong.  

Here some general documentation including error handling:

Requests
: <https://requests.readthedocs.io/en/latest/user/quickstart>

HTTPX
: <https://www.python-httpx.org/exceptions/>

urllib3
: <https://hip.readthedocs.io/en/stable/user-guide.html>

OpenAI
: <https://platform.openai.com/docs/guides/error-codes/python-library>



HBelow a list of the errors that may be raised by different libraries.



| Error Type / Cause                                                      | `httpx` Exception                                                                                                      | `requests` Exception                                | `urllib3` Exception                                                  | `openai` Exception                         |
| ----------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------- | -------------------------------------------------------------------- | ----------------------------------------------------- |
| **Connection failed** (DNS error, refused connection, TLS failure)      | `httpx.ConnectError`                                                                                                   | `requests.ConnectionError`                          | `urllib3.exceptions.NewConnectionError` or `MaxRetryError`           | `openai.APIConnectionError`                           |
| **Timeout** (operation took too long)                                   | `httpx.TimeoutException` (base), plus more specific: `httpx.ConnectTimeout`, `httpx.ReadTimeout`, `httpx.WriteTimeout` | `requests.Timeout`                                  | `urllib3.exceptions.ConnectTimeoutError`, `ReadTimeoutError`         | `openai.APITimeoutError`                              |
| **Server returned error status** (non-200 HTTP status, like 500 or 503) | `httpx.HTTPStatusError` (if `raise_for_status()` used)                                                                 | `requests.HTTPError` (if `raise_for_status()` used) | `urllib3.exceptions.HTTPError` (base class; often raised internally) | `openai.APIStatusError` (has `.status_code`)          |
| **Rate limited (HTTP 429)**                                             | `httpx.HTTPStatusError` with status 429                                                                                | `requests.HTTPError` with status 429                | Same as above                                                        | `openai.RateLimitError`                               |
| **SSL/TLS errors**                                                      | `httpx.ConnectError` (with underlying `ssl.SSLError`)                                                                  | `requests.exceptions.SSLError`                      | `urllib3.exceptions.SSLError`                                        | `openai.APIConnectionError` (wrapping `ssl.SSLError`) |
| **Generic request error** (catch-all)                                   | `httpx.RequestError` (base for all transport errors)                                                                   | `requests.RequestException` (base)                  | `urllib3.exceptions.HTTPError` (base)                                | `openai.OpenAIError` (base class for all SDK errors)  |

---

# Task 4. Ratelimiting and Throttling

Put this on a T shirt:

    You must not launch DDOS attacks on web services.

If you send several thousand requests to a service, you are ... Don't do that. It is a quick way to get locked out of the service. In the worst case, you may get all of UNH banned.

Instead, make sure your code limits the number of requests sent within a time period.

An easy way to achieve this is to use `aiolimiter` or other rate limiting libraries.

Here some starter code:

```python
limiter = AsyncLimiter(max_rate=3, time_period=60)  #  up to 3 requests per 60 second period

async with self.limiter:  # Throttle
      # launch request
```

**Please think carefully which rates would get your program to finish quickly, while obeying rate limit requests by the web service.** Hint: if you are seeing Rate Limiting errors (code 429), you are sending too many requests in too short of a time.


You can put everything together with

```python
limiter = AsyncLimiter(max_rate=3, time_period=60)

async def one_request(input):
    async with limiter:  # Throttle
        try:
            return await my_request(input)
        except openai.OpenAIError as e:
            # handle error, retry if needed
            raise

def multiple_requests(inputs):
    async def gather_tasks():
        tasks = [one_request(i) for i in inputs]
        return await asyncio.gather(*tasks)

    return asyncio.run(gather_tasks())

```




# Task 5. Explore Advanced Prompting with DSPy, LangChain, or Agentic Frameworks

When working with the `OpenAI` library, the input will be strings, and the output will be strings. You often find yourself using a template to fill in input variables (e.g.query,passage) and you will have to parse out multiple outputs.

There are many libraries that reduce work with strings by giving you templates, signatures, schemas, or agents that define the shape and intent of a request.

Below are some pointers for you to explore. Choose one, familiarize yourself with it, and include an example in your code base.



### Structured Data
These frameworks help to parse information out of the LLM response.

Instructor
: You ask for a Pydantic object, and the library automatically handles parsing, validation, and retries if the model response does not match.

Outlines
: You guide the model to emit a schema-conformant output rather than post-hoc parsing.

OpenRouter's Built-In support
: OpenRouter supports structured outputs for compatible models, ensuring responses follow a specific JSON Schema format. <https://openrouter.ai/docs/features/structured-outputs>

### Prompt Templates
These frameworks give you composable prompt objects.

LangChain
: You build typed templates and chains instead of manual string assembly.

DSPy
: You define signatures and modules instead of string prompts. DSPy can also optimize prompts against metrics.

LlamaIndex
: You manage prompt objects and pipelines that integrate retrieval and evaluation components.

### Agentic
Frameworks that lets you decompose a pipeline into smaller tasks (each handled by one agent). These are more powerful but also more complex to learn.

AutoGen
: Defining agents that talk to each other using natural language, functions, and tools.

LangChainAgents
: LangChain’s agent layer lets an LLM decide which tool or chain to call, rather than chaining prompts manually.

CrewAI
: Multi-agent teams of agents with roles, goals, and tools, and they coordinate on tasks.

ChatArena
: A lightweight framework for simulating multi-agent LLM "conversations" for evaluation and experiments.

AG2 (Agentscope / AutoGen2)
: A newer generation of orchestration frameworks that extend Autogen-style multi-agent architectures with more modularity and backends.

---

*If you don't know where to start. LangChain is pretty popular, your instructor has mostly worked with DSPy.*
