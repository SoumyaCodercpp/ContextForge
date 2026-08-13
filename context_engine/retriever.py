import os
from dataclasses import dataclass, field
from dotenv import load_dotenv
from context_engine.embedder import embed_query
from context_engine.vectordb import search_vectors

load_dotenv()

DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "20"))


@dataclass
class RetrievedChunk:
    """A single chunk returned from Qdrant with its similarity score."""
    chunk_id: int
    document_id: int
    text: str
    score: float
    chunk_index: int = 0
    page_number: int = None
    token_count: int = 0

    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = max(1, len(self.text.split()))


@dataclass
class RetrievalResult:
    """The result of a retrieval — contains the query and all retrieved chunks."""
    query: str
    chunks: list = field(default_factory=list)
    top_k: int = DEFAULT_TOP_K
    total_candidates: int = 0

    def __post_init__(self):
        self.total_candidates = len(self.chunks)


def retrieve(query, top_k=DEFAULT_TOP_K, document_ids=None):
    """Convert a question to a vector, search Qdrant, return matching chunks."""
    query_vector = embed_query(query)
    
    query_filter = None
    if document_ids:
        query_filter = {
            "must": [{"key": "document_id", "match": {"any": document_ids}}]
        }
    
    raw_results = search_vectors(
        query_vector=query_vector,
        top_k=top_k,
        query_filter=query_filter,
    )
    
    chunks = []
    for hit in raw_results:
        payload = hit.get("payload", {})
        text = payload.get("text", "")
        chunks.append(RetrievedChunk(
            chunk_id=hit["id"],
            document_id=payload.get("document_id", 0),
            text=text,
            score=hit["score"],
            chunk_index=payload.get("chunk_index", 0),
            page_number=payload.get("page_number"),
            token_count=max(1, len(text.split())),
        ))
    
    return RetrievalResult(query=query, chunks=chunks, top_k=top_k)