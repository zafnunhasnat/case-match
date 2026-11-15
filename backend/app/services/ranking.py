# backend/app/services/ranking.py

from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from sqlalchemy import text

class HybridRankingService:
    """
    Fuses keyword search scores, synonym expansion, and semantic vector scores,
    applies weights, enforces a cutoff threshold, and returns match evidence (Issue #17).
    """
    def __init__(self):
        pass

    def compute_hybrid_ranking(
        self,
        db: Session,
        query_text: str,
        query_embedding: List[float],
        synonyms: List[str] = None,
        weights: Optional[Dict[str, float]] = None,
        score_cutoff: float = 0.30,
        limit: int = 5
    ) -> List[Dict[str, Any]]:
        weights = weights or {"keyword": 0.3, "semantic": 0.5, "synonym": 0.2}
        synonyms = synonyms or []
        
        embedding_str = "[" + ",".join(map(str, query_embedding)) + "]"
        expanded_terms = [query_text] + synonyms
        keyword_query_str = " | ".join(expanded_terms)

        sql = text("""
            SELECT 
                n.id,
                n.note_identifier,
                n.content,
                COALESCE(ts_rank(n.tsv, plainto_tsquery(:keyword_query)), 0.0) as keyword_score,
                COALESCE(ts_rank(n.tsv, plainto_tsquery(:base_query)), 0.0) as base_keyword_score,
                (1.0 - (n.embedding <=> :embedding_vector::vector)) as semantic_score
            FROM clinical_notes n
            WHERE n.is_approved = TRUE
            ORDER BY (
                :w_kw * COALESCE(ts_rank(n.tsv, plainto_tsquery(:base_query)), 0.0) +
                :w_syn * COALESCE(ts_rank(n.tsv, plainto_tsquery(:keyword_query)), 0.0) +
                :w_sem * (1.0 - (n.embedding <=> :embedding_vector::vector))
            ) DESC
            LIMIT :limit;
        """)

        result = db.execute(sql, {
            "base_query": query_text,
            "keyword_query": keyword_query_str,
            "embedding_vector": embedding_str,
            "w_kw": weights.get("keyword", 0.3),
            "w_syn": weights.get("synonym", 0.2),
            "w_sem": weights.get("semantic", 0.5),
            "limit": limit
        }).fetchall()

        ranked_matches = []
        for row in result:
            kw_score = float(row.base_keyword_score)
            syn_score = float(row.keyword_score)
            sem_score = float(row.semantic_score)
            
            combined_score = (
                weights.get("keyword", 0.3) * kw_score +
                weights.get("synonym", 0.2) * syn_score +
                weights.get("semantic", 0.5) * sem_score
            )

            if combined_score >= score_cutoff:
                ranked_matches.append({
                    "note_id": row.id,
                    "note_identifier": row.note_identifier,
                    "snippet": row.content[:350] + "...",
                    "scores": {
                        "keyword": kw_score,
                        "synonym": syn_score,
                        "semantic": sem_score,
                        "combined": combined_score
                    },
                    "evidence": {
                        "matched_query": query_text,
                        "applied_synonyms": synonyms,
                        "fusion_weights": weights,
                        "cutoff_threshold": score_cutoff
                    }
                })

        return ranked_matches