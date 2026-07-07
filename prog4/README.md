# Prog 4: Indexing and Retrieval System

In this assignment you will use a retrieval system to build a search index of the provided example documents, use it to retrieve documents from the index, and evaluate the retrieval quality.

**Learning goals**: 
- Becoming familiar with retrieval systems
- Ability to create a search index
- Ability to retrieve from the search index
- Running a search engine evaluation.

You will be building on code and knowledge from the previous assignment. 

    ================================================================================
    Note that  you will need to download and install a retrieval system, such as Pyserini. 
    Be prepared that working through the installation procedure will take time, leave time to 
    work out  configuration issues.
    ================================================================================


# Task 1. Install Retrieval System

Choose one of the following:

1. [Whoosh](https://whoosh.readthedocs.io/en/latest/quickstart.html#a-quick-introduction) (pure python, simple install, okay for medium-scale corpora)
2. [Pyserini](https://github.com/castorini/pyserini)  (python with java, recommended, widely used)
3. [Anserini](https://github.com/castorini/anserini) (java, install via maven)
4. [Lucene](https://lucene.apache.org/) (java, widely used)
5. [PyTerrier](https://github.com/terrier-org/pyterrier)  (python wrapper around java-based Terrier, colab notebooks available, active development)
6. [PyLucene](https://lucene.apache.org/pylucene/) (python wrapper around java-based Lucene)
7. [Weaviate](https://docs.weaviate.io/weaviate/quickstart/local)  (python client plus docker, serious search engine for high loads)
8. [Vespa](https://docs.vespa.ai/en/vespa-quick-start.html) (python client plus docker, serious search engine for vector-based search)


If previously you used `uv pip install` , then I recommend you continue to prepend `uv` in front of all `pip install` instructions.



# Task 2. Index the document collection from Prog 1

With the retrieval system of your choice, index the document text from the  small document collection from Prog 1, represented in: `./data/neuclir3-small-corpus-eng.jsonl`

Print statistics of the search index, such as the total number of documents indexed and the total number of unique words.



# Task 3. BM25 retrieval with queries from Prog 1

For each of the (title) queries from the from NeuCLIR collcection (`./data/neuclir3-requests.jsonl`), obtain the top 1000 documents from the index using the BM25 retrieval model.

For each query, print the top 3 documents to a file along with their document id, rank score, and rank. (The best documents gets rank 1, runner-up gets rank 2, etc). Compare those to the documents obtained in Prog 1.



# Task 4. Output Rankings in TREC Run format

Familiarize yourself with the retrieval evaluation tool `trec_eval`. The tool expects two inputs: 

**Run (Rankings)**
: rankings of document IDs with score and rank for all queries (represented by their `request_id`).
the rankings are given in a text file, each line follows this pattern:

```
$query_id Q0 $doc_id $rank $score $methodname
```

Example

```
myquery Q0 doc123 1 13.42 bm25
```

**Qrel (Truth)**
: lists of document IDs that are relevant for each of the queries. Qrel stands for "query relevance". A qrel file is provided in `./data/neuclir3.qrel`. In general qrel files are also given as a text file, each line follows this pattern:

```
$query_id $iteration $doc_id $relevance
```

Example:

```
myquery  0  doc1234  1 
```

Output the top 100 documents from Task 3 in the trec run file format.


# Task 5. Evaluate Retrieval Quality with TREC Eval

Download and install the evaluation tool `trec_eval`. It is recommended to check out the latest release from <https://github.com/usnistgov/trec_eval/tree/version-10.0-rc2> then call `make` in the directory. You can directly use the compiled binary `./trec-eval`. For usage information call `./trec-eval -h`

Using the run file produced in Task 4, and the qrel file provided in `./data/neuclir3.qrel`, employ `trec_eval` to print evaluation measures for your BM25 ranking.

The tool output contains both a set of quality scores for each query/request as well as an average across all queries (under `all`).

Print the `map` and `ndcg@20` (`trec_eval` calls it `ndcg_cut.20`)  evaluation score across  all queries.  I recommend to check that all queries are used via the `num_q` metric.

For comparison, I included a run with a neural ranking method "plaidx" in `./data/plaidx_rankings/neuclir3-plaidx.run`. For the plaidx run, `trec_eval` reports a "map" score of 0.3016 and an "ndcg@20" score of 0.4366.


# Task 6. Exploration

I encourage you to experiment with your code base, and try out some ideas of your own choosing. Evaluate each variant with `trec_eval` and compare to the initial bm25 method and the provided plaidx run.

Here some suggestions:

* Evaluate your document rankings from Prog 1

* Explore the effect of different BM25 parameter settings.

* Use other retrieval models than BM25 as provided by the retrieval system.

* Experiment with different indexing settings, such as tokenization parameters.

* Try retrieving with other fields in the requests, such as `background` or `problem_statement`.

* Try indexing a larger collection and run all requests. Example Dataset from TREC RAG  available here: <https://pages.nist.gov/trec-browser/trec33/rag/data/> 

