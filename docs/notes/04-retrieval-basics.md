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
