# 04 - Retrieval Basics

## Definitions (with tiny worked examples)

### tsvector
A Postgres data type: a document turned into a sorted list of normalized
words (stemmed, stop words removed) with their positions.
Example: 'shortness of breath' becomes 'breath':3 'short':1.

### Embedding
A list of numbers (a vector) produced by a model so that texts with similar
meaning land close together in space.
Example (toy 2D): "cat" -> [0.9, 0.1], "kitten" -> [0.85, 0.2],
"car" -> [0.1, 0.95]. Cat and kitten are near each other; car is far.

### Cosine similarity
The cosine of the angle between two vectors. 1 = same direction,
0 = unrelated, -1 = opposite. It ignores length and compares direction.
Example: a = [1, 0], b = [1, 1]
dot = 1, |a| = 1, |b| = 1.414, so cos = 1 / 1.414 = 0.707.

### RRF (Reciprocal Rank Fusion)
Combines several ranked lists by summing 1 / (k + rank) for each list a
document appears in (k about 60). Uses only rank positions, not raw scores.
Example (k = 60):
- Doc A: keyword rank 1, vector rank 3 -> 1/61 + 1/63 = 0.0323
- Doc B: keyword rank 2, vector rank 1 -> 1/62 + 1/61 = 0.0325
Doc B wins narrowly, because it is high in both lists.

### Precision@k
Of the top k results, what fraction are relevant?
Example: top 5 returned, 2 relevant -> P@5 = 2/5 = 0.4.

### Recall@k
Of all relevant documents that exist, what fraction are in the top k?
Example: 4 relevant docs exist, 2 are in the top 5 -> R@5 = 2/4 = 0.5.

### MRR (Mean Reciprocal Rank)
Average over queries of 1 / (rank of the first relevant result).
Example: first relevant result at ranks 1, 3, 2 for three queries ->
(1 + 1/3 + 1/2) / 3 = 0.611.

## My SBERT results (all-MiniLM-L6-v2)
- "has shortness of breath" <-> "denies any shortness of breath": 0.814 (highest)
- "has shortness of breath" <-> "difficulty breathing": 0.624
- "has shortness of breath" <-> "cat sat on the mat": 0.088

## Weaknesses

### Keyword search (tsvector / full-text)
- Misses synonyms and paraphrases ("shortness of breath" vs
  "difficulty breathing" did not match with plainto_tsquery).
- Sensitive to wording, spelling, and abbreviations (SOB, dyspnea).
- AND queries are brittle: one missing term means no match.
- Stemming can conflate or miss words.

### Embeddings (SBERT)
- Handles negation poorly: "has shortness of breath" and "denies shortness
  of breath" scored 0.814, higher than the true synonym pair (0.624).
- Can blur exact identifiers: drug names, codes, numbers, rare terms.
- Quality depends on the model's training domain (general vs medical).
- Scores are hard to explain, and results can be "similar but wrong".

### RRF
- Ignores score magnitude: a near-perfect match and a barely-OK match at
  adjacent ranks get almost the same credit.
- Only as good as the input lists; if both retrievers miss a document, RRF
  cannot recover it.
- k is a tunable constant with no universal best value.
- A strong result in only one list gets limited credit versus a mediocre
  result in both.

# Retrieval Basics

## 1. PostgreSQL Keyword Search

### What is tsvector?

`tsvector` is PostgreSQL's normalized, searchable representation of text. It processes text by removing certain common words and normalizing terms.

Example:

```sql
SELECT to_tsvector('english', 'shortness of breath');
```

Output:

```text
'breath':3 'short':1
```

### What is plainto_tsquery?

`plainto_tsquery` converts ordinary search text into a PostgreSQL search query. It normalizes the words and connects the surviving terms using AND logic.

Example:

```sql
SELECT plainto_tsquery('english', 'difficulty breathing');
```

### What is @@?

The `@@` operator checks whether a document matches a search query.

Example:

```sql
SELECT
    to_tsvector('english', 'shortness of breath')
    @@
    plainto_tsquery('english', 'difficulty breathing');
```

Result:

```text
false
```

### Experiment Results

| Historical record | Search phrase | Result |
|---|---|---|
| shortness of breath | difficulty breathing | false |
| shortness of breath | shortness of breath | true |

### Conclusion

Keyword search finds matching normalized words, but it does not automatically understand that different phrases have similar meanings.

For example, "shortness of breath" and "difficulty breathing" describe similar symptoms but may not match using basic keyword search.

This is why CaseMatch AI needs semantic search in addition to keyword search.

---

## 2. Semantic Search with SBERT

### What is an embedding?

An embedding is a numerical representation of text. It converts a sentence into a list of numbers that represents its meaning.

Sentences with similar meanings should have embeddings that are closer together.

### What is SBERT?

SBERT stands for Sentence-BERT. It converts sentences into embeddings so that their semantic similarity can be compared.

Example sentences:

1. The patient is experiencing shortness of breath.
2. The individual has difficulty breathing.
3. The patient reports severe chest pain.
4. The person is having trouble catching their breath.
5. The patient has a broken arm after falling.

SBERT converts these sentences into embeddings and compares them.

### What is cosine similarity?

Cosine similarity measures how similar two vectors are by comparing the angle between them.

A higher score generally means the sentences are more similar in meaning.

For example:

- A score closer to 1 means the vectors point in a similar direction.
- A score around 0 means they are less similar.
- A score closer to -1 means they point in opposite directions.

SBERT uses cosine similarity to compare sentence embeddings.

### SBERT Experiment

The experiment uses five original sentences and compares every sentence with the others.

The expected observation is that sentences about breathing difficulties should receive relatively high similarity scores.

The actual similarity scores are recorded from the output of:

```bash
python scripts/semantic_search.py
```

### Conclusion

Semantic search can find related sentences even when they do not use exactly the same words.

For example, "shortness of breath" and "difficulty breathing" can be recognized as semantically related.

However, embeddings can struggle with negation. For example, "the patient has chest pain" and "the patient does not have chest pain" contain similar words but have opposite meanings.

---

## 3. Reciprocal Rank Fusion (RRF)

### What is RRF?

Reciprocal Rank Fusion combines results from multiple search systems into one ranking.

For example, CaseMatch AI can combine:

- PostgreSQL keyword search results.
- SBERT semantic search results.

RRF uses the position of a result in each ranking to calculate a combined score.

### RRF Formula

```text
score = sum(1 / (k + rank))
```

Where:

- `k` is a constant, commonly around 60.
- `rank` is the position of a result in a search ranking.
- A higher combined score means a result receives a better overall ranking.

### Worked Example

Assume two search systems return these rankings:

| Document | Keyword rank | Semantic rank |
|---|---:|---:|
| A | 1 | 3 |
| B | 2 | 1 |
| C | 3 | 2 |

Using k = 60:

Document A:

```text
1 / (60 + 1) + 1 / (60 + 3)

= 1 / 61 + 1 / 63

= 0.04813
```

Document B:

```text
1 / (60 + 2) + 1 / (60 + 1)

= 1 / 62 + 1 / 61

= 0.03252
```

Document C:

```text
1 / (60 + 3) + 1 / (60 + 2)

= 1 / 63 + 1 / 62

= 0.03200
```

The final ranking is:

1. Document A
2. Document B
3. Document C

### Weakness of RRF

RRF considers the rank positions of results, not the actual similarity or relevance score sizes.

For example, it does not distinguish between a result with a similarity score of 0.95 and one with a similarity score of 0.55 if they have the same rank position.

---

## 4. Search Evaluation Metrics

### What is Precision@k?

Precision@k measures how many of the top k search results are relevant.

Formula:

```text
Precision@k = Relevant results in top k / k
```

Example:

The top 3 results are:

```text
A, B, C
```

If A and C are relevant:

```text
Precision@3 = 2 / 3 = 0.67
```

This means approximately 67% of the top three results are relevant.

### What is Recall@k?

Recall@k measures how many of all relevant results were found in the top k results.

Formula:

```text
Recall@k = Relevant results in top k / Total relevant results
```

Example:

Assume A and C are the only relevant documents.

The top 3 results are:

```text
A, B, C
```

Both relevant documents were found:

```text
Recall@3 = 2 / 2 = 1.00
```

This means 100% of the relevant documents were found.

### What is MRR?

MRR stands for Mean Reciprocal Rank. It measures how highly the first relevant result appears in the search ranking.

Formula:

```text
Reciprocal Rank = 1 / Rank of first relevant result

MRR = Average of reciprocal ranks across queries
```

Example:

The search results are:

```text
1. B (not relevant)
2. A (relevant)
3. C (relevant)
```

The first relevant result is at rank 2:

```text
MRR = 1 / 2 = 0.50
```

A higher MRR means the first relevant result tends to appear closer to the top.

---

## 5. Retrieval System Weaknesses

### Keyword Search Weakness

Keyword search can miss synonyms and phrases with similar meanings.

Example:

- "Shortness of breath"
- "Difficulty breathing"

The phrases describe similar symptoms but do not necessarily share matching keywords.

### Embedding Search Weakness

Embeddings can struggle with negation because sentences with opposite meanings can contain very similar words.

Example:

- "The patient has chest pain."
- "The patient does not have chest pain."

The sentences use similar words but communicate different meanings.

### RRF Weakness

RRF considers result positions instead of the actual search scores.

It can ignore the difference between a very strong match and a weaker match if both occupy the same ranking position.

---

## 6. Final Conclusion

A reliable retrieval system can combine keyword search and semantic search.

- PostgreSQL keyword search finds matching terms.
- SBERT semantic search finds sentences with similar meanings.
- RRF combines rankings from both search systems.
- Precision@k, Recall@k, and MRR help evaluate search quality.

Combining these approaches can improve the retrieval of relevant case information.

