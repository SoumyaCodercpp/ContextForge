import math
import os
import re
from dataclasses import dataclass, field
from datetime import datetime, timezone
import numpy as np
from dotenv import load_dotenv
from context_engine.embedder import embed_query

load_dotenv()

WEIGHT_SEMANTIC = float(os.getenv("SCORE_WEIGHT_SEMANTIC", "0.45"))
WEIGHT_FRESHNESS = float(os.getenv("SCORE_WEIGHT_FRESHNESS", "0.15"))
WEIGHT_AUTHORITY = float(os.getenv("SCORE_WEIGHT_AUTHORITY", "0.15"))
WEIGHT_DENSITY = float(os.getenv("SCORE_WEIGHT_DENSITY", "0.25"))
FRESHNESS_HALF_LIFE = int(os.getenv("FRESHNESS_HALF_LIFE_DAYS", "365"))
DEFAULT_AUTHORITY = float(os.getenv("DEFAULT_AUTHORITY", "0.5"))

_authority_registry = {} # internal to this module


@dataclass
class ScoredChunk:
    """A chunk with its composite score and breakdown of all 4 factors."""
    chunk: object
    context_score: float = 0.0
    semantic_similarity: float = 0.0
    freshness_score: float = 0.0
    authority_score: float = 0.0
    density_score: float = 0.0


@dataclass
class ScoringResult:
    """The result of scoring — contains all scored chunks and the weights used."""
    query: str
    chunks: list = field(default_factory=list)
    weights: dict = field(default_factory=dict)

    @property
    def ranked_chunks(self):
        """Chunks sorted by context_score, highest first."""
        def get_score(chunk):
            return chunk.context_score
        return sorted(self.chunks, key=get_score, reverse=True)


def set_authority(document_id, score):
    """Set the authority score for a specific document."""
    if not 0.0 <= score <= 1.0:
        raise ValueError(f"Authority must be between 0 and 1, got {score}")
    _authority_registry[document_id] = score


def get_authority(document_id):
    """Get the authority score for a document. Defaults to 0.5."""
    return _authority_registry.get(document_id, DEFAULT_AUTHORITY)


def _compute_semantic(query_embedding, chunk):
    """How well does this chunk match the question? Cosine similarity."""
    chunk_embedding = embed_query(chunk.text)
    
    q = np.array(query_embedding)
    c = np.array(chunk_embedding)
    
    dot = np.dot(q, c)
    norm_q = np.linalg.norm(q)
    norm_c = np.linalg.norm(c)
    
    if norm_q == 0 or norm_c == 0:
        return 0.0
    
    similarity = float(dot / (norm_q * norm_c))
    return max(0.0, similarity)


def _compute_freshness(indexed_at=None):
    """How recently was this document indexed? New docs score higher."""
    if indexed_at is None:
        return 1.0
    
    now = datetime.now(timezone.utc)
    if indexed_at.tzinfo is None:
        indexed_at = indexed_at.replace(tzinfo=timezone.utc)
    
    age_days = (now - indexed_at).total_seconds() / 86400
    if age_days < 0:
        return 1.0
    
    return 0.5 ** (age_days / FRESHNESS_HALF_LIFE)


def _compute_density(text):
    """How much actual information is in this chunk? Penalizes headers, whitespace, stopwords."""
    if not text or not text.strip():
        return 0.0
    
    total_chars = len(text)
    
    non_ws = len(re.sub(r"\s+", "", text))
    text_ratio = non_ws / max(total_chars, 1)
    
    stopwords = {
        "the", "a", "an", "is", "are", "was", "were", "be", "been",
        "have", "has", "had", "do", "does", "did", "will", "would",
        "could", "should", "may", "might", "can", "to", "of", "in",
        "for", "on", "with", "at", "by", "from", "as", "into", "and",
        "but", "or", "not", "so", "this", "that", "these", "those",
        "it", "its", "we", "you", "i", "he", "she", "they", "what",
        "which", "who", "how", "if", "then", "about", "up", "out",
    }
    words = re.findall(r"\b[a-zA-Z]+\b", text.lower())
    if not words:
        content_ratio = 0.0
    else:
        content_words = [w for w in words if w not in stopwords]
        content_ratio = len(content_words) / len(words)
    
    word_count = len(words)
    length_score = 1.0 / (1.0 + math.exp(-0.3 * (word_count - 15)))
    
    alnum_chars = len(re.sub(r"[^a-zA-Z0-9]", "", text))
    alnum_ratio = alnum_chars / max(total_chars, 1)
    
    density = (
        0.25 * text_ratio
        + 0.30 * content_ratio
        + 0.25 * length_score
        + 0.20 * alnum_ratio
    )
    
    return max(0.0, min(1.0, density))


def score_chunks(query, chunks, weights=None, document_indexed_at=None):
    """
    Score each chunk on 4 factors and return ranked by composite score.
    
    Factors: Semantic (45%), Freshness (15%), Authority (15%), Density (25%).
    """
    if weights is None:
        weights = {
            "semantic": WEIGHT_SEMANTIC,
            "freshness": WEIGHT_FRESHNESS,
            "authority": WEIGHT_AUTHORITY,
            "density": WEIGHT_DENSITY,
        }
    
    total_weight = sum(weights.values())
    if not math.isclose(total_weight, 1.0):
        raise ValueError(f"Weights must sum to 1.0, got {total_weight}")
    
    query_embedding = embed_query(query)
    scored = []
    
    for chunk in chunks:
        semantic = _compute_semantic(query_embedding, chunk)
        
        indexed_at = None
        """ document_indexed_at = {
            1: datetime(2026, 8, 1),    
            2: datetime(2025, 3, 15),    
            5: datetime(2026, 8, 10),   
        }
        """
        if document_indexed_at:
            indexed_at = document_indexed_at.get(chunk.document_id)
        freshness = _compute_freshness(indexed_at)
        
        authority = get_authority(chunk.document_id)
        density = _compute_density(chunk.text)
        
        context_score = (
            weights["semantic"] * semantic
            + weights["freshness"] * freshness
            + weights["authority"] * authority
            + weights["density"] * density
        )
        
        scored.append(ScoredChunk(
            chunk=chunk,
            context_score=round(context_score, 6),
            semantic_similarity=round(semantic, 4),
            freshness_score=round(freshness, 4),
            authority_score=round(authority, 4),
            density_score=round(density, 4),
        ))
    
    return ScoringResult(query=query, chunks=scored, weights=weights)