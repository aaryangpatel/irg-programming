# Prog 6: Learning-to-Rank

In this assignment you will be using a learning-to-rank package to re-rank a set of documents. You will derive features from rankings/run-files you created previously. You can either use BM25 and PlaidX from a previous programming assignment, or rankings your created for your course project.

You are encouraged to ask questions on the discussion forum whenever you are uncertain how to proceed.

**Learning goal**:
- Learn how to apply a Learning-to-Rank framework for re-ranking.
- Learn how to use Z-score normalization for features.


# Task 1. Download, Install, Familiarize yourself

You have a choice between two software toolkits which both support
list-wise learning-to-rank.

-   Rank-Lips automatically optimizes for MAP, supports features that
    come from run files.

-   RankLib is a java project that optimizes for various evaluation
    measures, but you need to convert the rankings into a special
    feature file. Also it has some bugs to work around if you want to
    optimize for MAP.

## Rank-Lips (Linux only)

-   Download and instructions from:
    <https://www.cs.unh.edu/~dietz/rank-lips/> (use the statically
    compiled Linux binary)

-   Read the "Complete Usage Instructions" <https://www.cs.unh.edu/~dietz/rank-lips/usage.html>

-   Work through the toy example <https://www.cs.unh.edu/~dietz/rank-lips/example.html>

Rank-lips is designed for the use case where you have different ranking
functions, each in a TREC run file, and you want to learn how to combine
those features to get the best ranking.

To represent the features vector $\vec{f}$ for document $D$ and
query $Q$, you need to produce directory of input features. Each feature
$F_i$ will be represented as a TREC run file (I call it the
"feature file"), listing query id and document id along with the
retrieval score and rank. Note that the retrieval score will be the
$i$'th feature for the query-document combination. You can chose any
file name for the feature files, but you must use the same file names
for training and test.

Use the flags `–feature-variant FeatScore` to use the score as feature
or the flag `–feature-variant FeatRecipRank` to use the inverse rank as
features. Documents that are not included in the run file, will be
assigned a default feature (which is set with
`–default-any-feature-value VALUE`.

For the test set, you will have to produce a directory of features
containing exactly the same file names as during training. The software
will stop with an error if a file is missing.

Please do not copy the rank-lips binary into your repository. Instead
include instructions how to download the binary and place it in an
accessible path on the `c02` server.

## RankLib (Java only)

Download the RankLib source files, build, and familiarize yourself with
how to use RankLib:

-   Overview\
    <https://sourceforge.net/p/lemur/wiki/RankLib/>

-   `RankLib.jar` is provided on `mycourses -> Files -> other-material`.\
    Alternative installation instructions (slightly outdated version)\
    <https://sourceforge.net/p/lemur/wiki/RankLib%20Installation/> and\
    The actual latest source code\
    <https://sourceforge.net/p/lemur/code/HEAD/tree/RankLib/trunk/>

-   How to use RankLib (misses the -qrel option)\
    <https://sourceforge.net/p/lemur/wiki/RankLib%20How%20to%20use/>

-   Training data format\
    <https://sourceforge.net/p/lemur/wiki/RankLib%20File%20Format/>

Please do not copy the RankLib code into your repository. Instead
include instructions how to download and build RankLib into your
installation instructions.

You need to produce a feature file thas represents the feature vectors
$\vec{f}$ for document $D$ and query $Q$ as one line in RankLib
format. Actually, this format is called SVMlight format. For details on
the Format see:
<https://sourceforge.net/p/lemur/wiki/RankLib%20File%20Format/>. Note
that relevant documents are indicated by label 1 and non-relevant with
label 0.

If you want to optimize for MAP, you must use the option `-qrel FILE`
and pass in the qrel file (otherwise the MAP numbers are wrong). The
option is not documented in the web page, but you find out about it in
the program's usage help.


# Optional Task 2. Test Features

(You can skip this task if you feel comfortable with the framework.)

-   There is only a single query (whose text does not matter, you can
    call it query id `Q0`)

-   The document corpus contains documents D1 \... D12.

-   For training labels: only $D2, D3, D5$ are relevant according to the judges.

-   As features use both:
    1. the rank score
    2. the reciprocal rank  (= 1/rank)


-   Consider the following four document rankings $\mathcal{R}_i$,
    notation `docID: score`). Each ranking corresponding to a different
    ranking function hence the different scores and rankings, despite
    using the same query and corpus. You can assume a score of 0.0 for
    documents that were omitted from the ranking.


|   rank  |  $\mathcal{R}_{1}$ |  $\mathcal{R}_{2}$  | $\mathcal{R}_{3}$ |  $\mathcal{R}_{4}$ |
|  ------ | ------------------ | ------------------- | ----------------- | ------------------ |
|     1   |      D1: 0.9       |     D2: 99          |     D1: 10        |   D1: 1.2          |
|     2   |      D2: 0.8       |     D5: 50          |     D2: 5         |   D2: 1.1          |
|     3   |      D3: 0.5       |     D6: 10          |     D5: 3         |   D8: 0.9          |
|     4   |      D4: 0.3       |     D7: 1.5         |                   |  D10: 0.1          |
|     5   |      D5: 0.2       |     D8: 1.0         |                   |  D12: 0.1          |
|     6   |      D6: 0.1       |     D9: 0.9         |                   |                    |
|     7   |                    |    D10: 0.1         |                   |                    |
|     8   |                    |    D11: 0.01        |                   |                    |


Train the model (as instructed in Task 4) with these features and report the training MAP score.


# Task 3. Derive Feature Vectors and Training/Test Labels

Convert the BM25 and PlaidX run files, into feature vectors that will be used for Learning-to-Rank. 


**As features** use both:
1. the rank score
2. the reciprocal rank  (= 1/rank)

The result will be four features:
* BM25-score
* BM25-reciprocal-rank
* PlaidX-score
* PlaidX-reciprocal-rank


**As training labels** use the ground labels for **training queries 324 and 261** from the query relevance file `./data/neuclir3.qrel`.

**For evaluation** use the ground truth labels for **test query 387** from the query relevance file `./data/neuclir3.qrel`

Note that depending on the L2R framework, you may need to emit this in different formats. See above for more information.


# Task 4. Train the Learning-to-Rank Model

Using the traning queries, train a Learning-to-Rank model with the features/labels you generated above. Use

* List-wise Learning-to-rank
* Coordinate Ascent
* Optimize for best ranking performance in Mean-Average Precision (MAP). --- Note: If you use RankLib, you must set the `-qrel` parameter, otherwise your results are incorrect.

* Use maximum 100 training iterations

Save the model to a file.

Also, please save any information about training progress and training quality.


# Task 5. Evaluate the Learning-To-Rank Model

Using the test queries (here: query, singular), evaluate the quality of your trained model.

1. You will use the features you generate for your test query to predict rank scores, to produce a ranking of documents. Write those to a new run-file.
2. Evaluate the new run-file as in the previous programming assignment.



# Task 6. Exploration

Explore one idea. Here suggestions:

* Effects of Z-score normalization (See below)
* The effects of using additional run files (e.g. total matches, TF-IDF, query expansion/reformulation, different fields of the report request)
* Effects of using LLM-as-a-judge labels for training, but manual labels for evaluation.


## Z-Score Normalization

Study the effects of Z-score normalization applied to the features.
Design an evaluation that allows you identify whether Z-score
normalization is better, worse, or has no effect.

You apply Z-score normalization to each feature individually, using the
following process.

2.  For every feature $i$, you will compute the mean of the feature
    values $f_{i}$ across all feature vectors (denoted $\mu_i$)
    as well as the standard deviation $\sigma_i$.

3.  Then you define the Z-score normalized feature vector
    $\vec{f'}$ by setting each $i$'th component to
    $$f'_i=\frac{1}{\sigma_i} \left( f_i - \mu_i \right)$$

You obtain a set of candidate documents by using different retrieval
models to retrieve the top 100 documents, then union the sets.

**Remember:** If you train a model with Z-score normalized features, you
will also need to apply Z-score normalization to the features of test
data. There are two solutions: The proper way is to compute the means
$\mu_i$ and standard deviations $\sigma_i$ on the training data, then
store them along with the model, to apply them to test data. (There is
also a way to correct model parameters to absorb this information, which
I am happy to discuss.)

The less technical correct way (which is also accepted for this
programming assignment) is to apply Z-score normalization to both train
and test features using means/standard deviations across the whole data
set.

You can also see if your learning-to-rank software supports this
normalization out of the box.
