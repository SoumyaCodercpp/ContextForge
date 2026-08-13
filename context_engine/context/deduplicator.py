import os
import numpy as np
from dataclasses import dataclass, field
from dotenv import load_dotenv
from context_engine.embedder import embed_chunks


load_dotenv()

DEDUP_THRESHOLD = float(os.getenv("DEDUP_THRESHOLD", "0.85"))


@dataclass
class DedupResult:
    kept: list = field(default_factory=list)
    removed: list = field(default_factory=list)
    threshold: float = DEDUP_THRESHOLD
    input_count: int = 0
    output_count: int = 0

    def __post_init__(self):
        self.input_count = len(self.kept) + len(self.removed)
        self.output_count = len(self.kept)


def _cosine_similarity(vec_a, vec_b):
    """Cosine similarity between two vectors. Assumes both are normalized."""
    a = np.array(vec_a)
    b = np.array(vec_b)
    
    dot = np.dot(a, b)

    # magnitutde
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b)
    
    if norm_a == 0 or norm_b == 0:
        return 0.0
    
    return float(dot / (norm_a * norm_b))


def deduplicate(chunks, threshold=DEDUP_THRESHOLD):
    """
    Remove near-duplicate chunks using embedding similarity.
    
    Algorithm: Greedy score-priority. Process chunks in retrieval order.
    A chunk is kept only if it's not too similar to any previously kept chunk.
    """
    if not chunks:
        return DedupResult(threshold=threshold)
    
    # Get embeddings for all chunks in one batch
    texts = [chunk.text for chunk in chunks]
    embeddings = embed_chunks(texts)
    
    kept = []
    kept_embeddings = []
    removed = []
    
    for i, chunk in enumerate(chunks):
        current_embedding = embeddings[i]
        is_duplicate = False
        
        # Compare against all kept chunks
        for kept_emb in kept_embeddings:
            similarity = _cosine_similarity(current_embedding, kept_emb)
            if similarity >= threshold:
                is_duplicate = True
                break
        
        if is_duplicate:
            removed.append(chunk)
        else:
            kept.append(chunk)
            kept_embeddings.append(current_embedding)
    
    return DedupResult(kept=kept, removed=removed, threshold=threshold)