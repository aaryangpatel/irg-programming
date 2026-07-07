# Prog 3: Query Web Search for RAG

In this assignment you will Web Search APIs in addition to LLMs.

**Learning goals**: 
- Different ways to access search engines
- Accessing content from the Web
- Building a report generator

You will be building on code and knowledge from the previous assignment. 

    ================================================================================
    Before you start, create an account at SerpAPI with your UNH address. You claim your free 1000 searches, by reaching out to them via the Support Chat, tell them that you are taking CS 753 with Prof. Dietz.
    ================================================================================


# Task 1. Retrieve Web Documents

For this first task, it is okay to use the `snippets` from the search engine in lieu of documents.


## Task 1a. Retrieve Web Documents via SerpAPI

Use `SerpAPI` to search Google for Web pages that answer the information requests. For now it is okay to use the search snippet instead of the full web page.

* Create an account at  <https://serpapi.com> with your `unh.edu` email address to get 1000 free searches (standard free is 250). When your searches are gone, the are gone. You can check how many searches you have performed when you go to your SerpAPI account.
* Read the documentation at SerpAPI. <https://serpapi.com/search-api>
* Look at their playground. Bottom right displays the JSON you will get as a response. Top right has a button "Export to Code".

In order to use `SerpAPI` you need to add the library `google-search-results` to your python environment (ensure that it is added to `requirements.txt` then reinstall them).



## Task 1b. Retrieve Web Documents via DuckDuckGo 

DuckDuckGo offers free access to their web search via the DDGS (**D**uck**D**uck**G**o **S**earch) library. Here some starter code.

```python
from ddgs import DDGS
from ddgs.exceptions import TimeoutException,RatelimitException, DDGSException

query="lazy fox hunt"
max_results=10

# todo need to wrap with exception handling, retries, backoffs, and throttling.
with DDGS(timeout=20) as ddgs:
    return list(ddgs.text(query,  backend="html", region="wt-wt", safesearch="moderate", max_results=max_results))
```

Inspect the result you receive and parse out the ranking, urls, and snippets.



## Optional Task 1c: Retrieve Web Documents via OpenRouter Tool Invocations

Please familiarize yourself with the web search "tool" on OpenRouter:
https://openrouter.ai/docs/features/web-search

Perform the same task, but with this LLM tool invocation.



## Task 2. Obtaining Web Page Content

Now we move towards obtaining web page content from the web.

You use the `requests` library to download the web page and `BeautifulSoup` to get the visible text out of the HTML. Here some starter code:

```python
  import requests
  from bs4 import BeautifulSoup

  url = "https://example.com"
  response = requests.get(url)

  if response.status_code == 200:
      # page content as html
      html = response.text

      # parse html
      soup = BeautifulSoup(html, "html.parser")

      # Extract all text
      content = soup.get_text()
      
      print("content = ",content)
      return content

  else:
      print("Error:", response.status_code)
      return ""
```


# Task 3. Retrieve-and-Generate

Build your own RAG pipeline using the Web Search and the LLM endpoint for generation.

Here some ideas to explore:
1. See how different ways to access Web search change the results.
2. Add additional search terms.
3. Use the LLM to convert the `background` and `problem_statement` of the requests into a web query. Use that to search the web instead of the title query.
4. Use the LLM to convert each retrieved page into one clean sentence for the response.
5. Use the LLM to condense content from multiple web pages at once.


# Task 4. Output Responses in RAGTIME format

Read the RAGTIME track guidelines, here <https://trec-ragtime.github.io/> or in this repository at `./RAGTIME-2025-guidelines.md`. 

Write the reponses you obtained in the described "report" format. I suggest you use Pydantic.

Instead of document ids from the NeuCIR/RAGTIME corpus, you can use the URLs from Web Search.
