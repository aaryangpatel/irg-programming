# Prog 1: Simple Retrieval System

In this assignment you write a very simple document ranking system.

**Learning goals**: 
- Working with data in JSON / JSON-lines (jsonl) format.
- Segmenting text into words and matching query/document terms.
- Ranking documents by how many query terms they contain.
- Familiarize yourself with ranking models (aka rank score functions).



# 1. Task:  Load the data

First do some research about how to work with JSON files. 

I highly recommend to familiarize yourself with a viewer for json files. It is just a plain text file, so a text viewer can open then. But when json is in compacted or in "json-lines" format, it may be difficult to read. Most web browsers (firefox) and programming environments (Visual Studio Code) can render json. For the bash command lines, I recommend the tool `jq` (<https://jqlang.org/>).


> Learn how to load json or jsonl with python libraries such as `pydantic` or `attrs`.  (You can also use the `json` package, but I don't recommend it.)


Then write some code to load queries and example documents (both from jsonl) from the provided dataset. More details below.

I recommend to print some example output from the files you loaded.



## File handling

Please familiarize yourself with how to open and read/write files in python.

Here some starter code for reading json-lines files

```python
    with open(file=documents_path, mode='r', encoding='utf-8') as f:
        for line in f.readlines():
            # parse one object from the string `lines`
```


## Search Requests / Queries Format
Query file: `./data/neuclir3-requests.jsonl`

This jsonl file contains so-called report requests (each line is one request object).

 Here what these fields mean

* `request_id`: a unique string that will identify this request (more generally, this is called a `query_id`). You will use this later when you write the results
* `title`:  a short search query, which a user would type into the search box.
* `background`: a description of the user's background. (Ignore for now.)
* `problem_statement`: the problem the user is trying to solve. (Ignore for now.)
* `limit`: the number of characters the user would like to read. (Ignore for now.)
* `collection_ids`: the references of collections the user would want to search. (Ignore.)


Example:

```json
{
  "request_id": "324",
  "title": "Machu Picchu, architecture"
  "background": "As an archaeologist leading an expedition in South America, I require insights into the \"Mysteries of Machu Picchu's Architecture\" to deepen our team's understanding of its construction techniques and historical significance. This report will guide our fieldwork and contribute to the scholarly discourse on Incan civilization.",
  "problem_statement": "Produce a report on the mysteries of Machu Picchu's architecture. The focus of the report is on speculations and theories regarding the construction methods and architectural marvels of Machu Picchu. I am also interested in hypotheses about the purpose, techniques, and significance of the unique structures at this ancient Incan site.",
  "limit": 2000,
  "collection_ids": [
    "neuclir/1/all"
  ],
}
```


## Document Format

Corpus file: `./data/neuclir3-small-corpus-eng.jsonl`

This jsonl file contains English documents (each line is one document object).

 Here what these fields mean
* `doc_id`: a unique identifier referring to this document. You will use this later when you write results.
* `text`: the text content of the document.

Example Document

```json

{
  "doc_id": "0084f08e-3bb2-4005-8e47-a8c810344d31",
  "text": "In our time, when the service of mankind has appeared scuba diving and other modern equipment, allowing to descend to the bottom of any reservoirs, the finds of the pyramids under water no longer surprise anyone.\nIt turns out that the famous pyramids of Ancient Egypt are not as lonely as it seemed 150 years ago. [...]"
  }
```

The `\n` denotes the newline character, just like you would in a python string.



# Task 2.  Break Text into Words

You can break a text string `my_text` into words by calling `my_text.split()`

```python 
> "My beautiful text!".split() 
["My", "beautiful", "text!"]
```
> 

But you still need to normalize upper/lower casing and remove punctuation. You can do this with `mystr.lower()` and `mystr.translate(str.maketrans('', '', string.punctuation))`.



# Task 3. Find Documents with Matches

For each query's title and document's text, determine the number of word matches. That is: the number of document terms that are mentioned in the query.

There are two ways to go about it:

* number of document words that match
* number of unique document words that match

For a handful of documents, report both along with the list of words that are matching.

Next we are using the number of (unique/total) matches to derive a so-called **"rank score"**, that is a number to quantify the relevance of a document for a given query. 


# Task 4. Rank / Sort Documents by Word Matches

Finally, we want to give a small set of most relevant documents to the user. This is called a "top-k ranking", where k (e.g. 10) is a number of documents to return.

We will discuss data structures for computing such rankings efficiently, especially when the number of documents in the corpus is large (think: the internet). For now, just use a sort-function.


If you have a function `rank_score` that measures the relevance of each document for a query (such as the number of word matches), you can sort a list of document objects as follows, then take the top `k` documents.

```python 
def rank_score(query_words:List[str]
               , document:Document
               ) -> float:
    [...]

# Sort using thie function 
ranking = sorted(documents
   , key=lambda doc: rank_score(query_words, doc)
   , reverse=True
   )

top_k_ranking = ranking[0:k]  # Just take the first k documents

```

Explain why I suggest to use `reverse=True`.


# Task 5. Output Rankings

For each query, print the top 3 documents to a file along with their document id, rank score, and rank. (The best documents gets rank 1, runner-up gets rank 2, etc).

Choose a useful file format to represent this information.

# Task 6. Exploration

I encourage you to experiment with your code base, and try our some ideas of your own choosing. Here some options:

* Ranking Models

Earlier we discussed two options for rank score functions: total word matches and unique maches.  Other examples of rank score functions (aka Ranking Models) are the Jaccard Index, TF-IDF variants, or BM25. I encourage you to look them up and experiment with them.


* Stopwords

Another thing to consider are so-called stop words, like "the","a","under","about", or "or".  While these words have important grammatical functions, they don't contain a lot of information that is useful for these word match models. So a common approach is to simply remove them, from both the query and the document.  

Here a list of stopwords for IR purposes: <https://dedolist.com/lists/language/smart-stop-words/>

* User Background and Problem Statement

So far we only used the `title` field of the requests, but the data also contains information about the user's background and problem statement. How does your document ranking change when you use the `problem statement` and/or `background` as part of the search query?  Do you have ideas for how to utilize them best as rank score functions?







