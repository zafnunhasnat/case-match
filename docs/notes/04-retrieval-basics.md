
# Retrieval Basics

## 1. PostgreSQL Keyword Search

### What is tsvector?

`tsvector` is PostgreSQL's normalized, searchable representation of text.

It processes text by removing certain common words and normalizing terms so they can be searched more efficiently.

Example:

```sql
SELECT to_tsvector('english', 'shortness of breath');
```

### What is plainto_tsquery?

`plainto_tsquery` converts ordinary search text into a PostgreSQL search query.

It normalizes the words and connects the surviving terms using AND logic.

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

### Experiment Results

| Historical record | Search phrase | Expected result |
|---|---|---|
| shortness of breath | difficulty breathing | false |
| shortness of breath | shortness of breath | true |

### Conclusion

Keyword search finds matching normalized words, but it does not automatically understand that different phrases have similar meanings.

For example, "shortness of breath" and "difficulty breathing" describe similar symptoms but may not match using basic keyword search.

This is why CaseMatch AI needs semantic search in addition to keyword search.
