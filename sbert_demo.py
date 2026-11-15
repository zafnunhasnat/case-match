from itertools import combinations
from sentence_transformers import SentenceTransformer, util

sentences = [
    "The patient has shortness of breath.",
    "She is having difficulty breathing.",
    "He complained of chest pain.",
    "The patient denies any shortness of breath.",
    "The cat sat on the mat.",
]

model = SentenceTransformer("all-MiniLM-L6-v2")
emb = model.encode(sentences, convert_to_tensor=True)

scores = []
for i, j in combinations(range(len(sentences)), 2):
    scores.append((util.cos_sim(emb[i], emb[j]).item(), i, j))

for score, i, j in sorted(scores, reverse=True):
    print(f"{score:.3f}  [{i}] {sentences[i]}  <->  [{j}] {sentences[j]}")
