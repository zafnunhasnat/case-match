from sentence_transformers import SentenceTransformer, util

# Five original sentences for the semantic search experiment
sentences = [
    "The patient is experiencing shortness of breath.",
    "The individual has difficulty breathing.",
    "The patient reports severe chest pain.",
    "The person is having trouble catching their breath.",
    "The patient has a broken arm after falling."
]

# Load the SBERT model
model = SentenceTransformer("all-MiniLM-L6-v2")

# Convert each sentence into an embedding
embeddings = model.encode(sentences, convert_to_tensor=True)

# Calculate cosine similarity between all sentences
similarity_matrix = util.cos_sim(embeddings, embeddings)

# Display the similarity matrix
print("\nSIMILARITY MATRIX\n")

for i, sentence in enumerate(sentences):
    print(f"\nSentence {i + 1}: {sentence}")

    for j, other_sentence in enumerate(sentences):
        score = similarity_matrix[i][j].item()
        print(f"  Sentence {j + 1}: {score:.4f}")

# Collect each unique sentence pair
pairs = []

for i in range(len(sentences)):
    for j in range(i + 1, len(sentences)):
        score = similarity_matrix[i][j].item()
        pairs.append((score, i, j))

# Sort pairs from highest similarity to lowest
pairs.sort(reverse=True)

# Display the highest-scoring pairs
print("\nTOP SIMILAR SENTENCE PAIRS\n")

for score, i, j in pairs:
    print(f"Similarity: {score:.4f}")
    print(f"Sentence {i + 1}: {sentences[i]}")
    print(f"Sentence {j + 1}: {sentences[j]}")
    print()

    