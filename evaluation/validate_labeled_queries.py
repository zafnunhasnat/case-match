import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

with open(ROOT / "data/synthetic_cases/notes.json") as f:
    notes = json.load(f)

with open(ROOT / "evaluation/labeled_queries.json") as f:
    dataset = json.load(f)

valid_note_ids = {note["id"] for note in notes}
dev = dataset["dev"]
test = dataset["test"]
all_queries = dev + test

assert len(all_queries) == 30, f"Expected 30 queries, found {len(all_queries)}"
assert len(dev) == 18, f"Expected 18 dev queries, found {len(dev)}"
assert len(test) == 12, f"Expected 12 test queries, found {len(test)}"

query_ids = [query["id"] for query in all_queries]
assert len(query_ids) == len(set(query_ids)), "Duplicate query IDs"

required_fields = {
    "id",
    "query",
    "relevant_note_ids",
    "must_not_match_note_ids",
    "tags",
}

for query in all_queries:
    assert required_fields <= query.keys(), (
        f"{query['id']} is missing required fields"
    )
    assert query["relevant_note_ids"], (
        f"{query['id']} has no relevant notes"
    )

    for note_id in query["relevant_note_ids"]:
        assert note_id in valid_note_ids, (
            f"{query['id']} references nonexistent relevant note {note_id}"
        )

    for note_id in query["must_not_match_note_ids"]:
        assert note_id in valid_note_ids, (
            f"{query['id']} references nonexistent negative note {note_id}"
        )

    overlap = (
        set(query["relevant_note_ids"])
        & set(query["must_not_match_note_ids"])
    )
    assert not overlap, f"{query['id']} has conflicting labels: {overlap}"

dev_ids = {query["id"] for query in dev}
test_ids = {query["id"] for query in test}
assert not dev_ids & test_ids, "Dev/test overlap"

tag_counts = {
    tag: sum(tag in query["tags"] for query in all_queries)
    for tag in [
        "synonym",
        "negation",
        "history",
        "abbreviation",
        "multi-finding",
    ]
}

minimums = {
    "synonym": 5,
    "negation": 5,
    "history": 3,
    "abbreviation": 3,
    "multi-finding": 5,
}

for tag, minimum in minimums.items():
    assert tag_counts[tag] >= minimum, (
        f"Need at least {minimum} {tag} queries; found {tag_counts[tag]}"
    )

print("Validation passed!")
print(f"Queries: {len(all_queries)} (dev: {len(dev)}, test: {len(test)})")
print("Category counts:")
for tag, count in tag_counts.items():
    print(f"  {tag}: {count}")
