# backend/app/services/semantic_search.py

from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from sqlalchemy.orm import Session
from sqlalchemy import text

class SemanticSearchService:
    """
    Handles semantic embedding generation and pgvector similarity search
    for approved clinical note sections (Issue #14).
    """
    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        # Initialize the Sentence Transformer model
        self.model = SentenceTransformer(model_name)
        
    def generate_embedding(self, text_content: str) -> List[float]:
        """
        Converts clinical text into a normalized numerical vector representation.
        """
        embedding = self.model.encode(text_content, normalize_embeddings=True)
        return embedding.tolist()

    def search_similar_notes(
        self,
        db: Session,
        query_text: str,
        limit: int = 5,
        score_threshold: float = 0.20
    ) -> List[Dict[str, Any]]:
        """
        Generates an embedding for the query and searches approved notes
        using pgvector cosine distance (<=>).
        """
        query_embedding = self.generate_embedding(query_text)
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        
        sql = text("""
            SELECT 
                n.id,
                n.note_identifier,
                n.content,
                (1.0 - (n.embedding <=> :embedding_vector::vector)) as semantic_score
            FROM clinical_notes n
            WHERE n.is_approved = TRUE
            ORDER BY n.embedding <=> :embedding_vector::vector ASC
            LIMIT :limit;
        """)
        
        result = db.execute(sql, {
            "embedding_vector": embedding_str,
            "limit": limit
        }).fetchall()
        
        matches = []
        for row in result:
            score = float(row.semantic_score)
            if score >= score_threshold:
                matches.append({
                    "note_id": row.id,
                    "note_identifier": row.note_identifier,
                    "snippet": row.content[:300] + "...",
                    "semantic_score": score,
                    "evidence": {
                        "matched_query": query_text,
                        "retrieval_method": "pgvector_cosine_similarity"
                    }
                })
        return matches