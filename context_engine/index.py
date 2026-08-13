import os
import time
from dataclasses import dataclass, field
from dotenv import load_dotenv

from context_engine.chunker import process_pdf
from context_engine.embedder import embed_chunks, get_embedding_dimension
from context_engine.metadata import Document as DocModel, Chunk as ChunkModel, SessionLocal, init_db
from context_engine.vectordb import create_collection, upsert_vectors
from context_engine.retriever import retrieve
from context_engine.context.deduplicator import deduplicate
from context_engine.context.scorer import score_chunks
from context_engine.context.selector import select_chunks
from context_engine.llm import generate_answer

load_dotenv()

CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "500"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))
DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "20"))
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "4096"))



@dataclass
class PipelineResult:
    query: str
    answer: str = ""
    retrieved: list = field(default_factory=list)
    dedup_result: object = None
    scoring_result: object = None
    selection_result: object = None
    llm_response: object = None
    pipeline_latency_ms: int = 0

    @property
    def stages_summary(self):
        return {
            "retrieved": len(self.retrieved),
            "after_dedup": len(self.dedup_result.kept) if self.dedup_result else 0,
            "after_scoring": len(self.scoring_result.chunks) if self.scoring_result else 0,
            "after_selection": len(self.selection_result.selected) if self.selection_result else 0,
        }

    @property
    def token_summary(self):
        if self.selection_result and self.selection_result.savings:
            return self.selection_result.savings
        return {}


def ingest_pdfs(file_paths, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    """
    Full ingestion pipeline:
    PDF → extract text → chunk → embed → store in Qdrant + PostgreSQL.
    """
    init_db()
    vector_dim = get_embedding_dimension()
    create_collection(vector_size=vector_dim)
    
    documents = []
    for fp in file_paths:
        documents.append(process_pdf(fp, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
    
    if not documents:
        return []
    
    all_texts = []
    for doc in documents:
        for chunk in doc.chunks:
            all_texts.append(chunk.text)
    
    all_embeddings = embed_chunks(all_texts)
    
    session = SessionLocal() # Opening a PostgreSQL session
    document_ids = []
    
    try:
        embedding_idx = 0
        qdrant_points = []
        
        for doc in documents:
            doc_model = DocModel(
                filename=doc.filename,
                file_type=doc.file_type,
                file_size_bytes=doc.file_size_bytes,
                chunk_count=doc.chunk_count,
            )
            session.add(doc_model)
            session.flush() 
            
            for chunk in doc.chunks:
                chunk_model = ChunkModel(
                    document_id=doc_model.id,
                    chunk_index=chunk.chunk_index,
                    text=chunk.text,
                    token_count=chunk.token_count,
                )
                session.add(chunk_model)
                session.flush()
                
                qdrant_points.append({
                    "id": chunk_model.id,
                    "vector": all_embeddings[embedding_idx],
                    "payload": {
                        "document_id": doc_model.id,
                        "chunk_index": chunk.chunk_index,
                        "text": chunk.text,
                        "page_number": chunk.page_number,
                    },
                })
                embedding_idx += 1
            
            document_ids.append(doc_model.id)
        
        session.commit()
        
        if qdrant_points:
            upsert_vectors(qdrant_points)
    
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
    
    return document_ids


def query(question, top_k=DEFAULT_TOP_K, max_tokens=MAX_CONTEXT_TOKENS, selection_strategy="greedy_by_density", document_ids=None):
    """
    Full query pipeline:
    Question → Retrieve → Deduplicate → Score → Select → LLM → Answer.
    """
    start = time.perf_counter()
    
    retrieval_result = retrieve(question, top_k=top_k, document_ids=document_ids)
    retrieved_chunks = retrieval_result.chunks
    
    dedup_result = deduplicate(retrieved_chunks)
    
    scoring_result = score_chunks(question, dedup_result.kept)
    selection_result = select_chunks(scoring_result, max_tokens=max_tokens, strategy=selection_strategy)
    
    context_text = selection_result.context_text
    llm_response = generate_answer(context=context_text, question=question)
    
    elapsed = int((time.perf_counter() - start) * 1000)
    
    return PipelineResult(
        query=question,
        answer=llm_response.answer,
        retrieved=retrieved_chunks,
        dedup_result=dedup_result,
        scoring_result=scoring_result,
        selection_result=selection_result,
        llm_response=llm_response,
        pipeline_latency_ms=elapsed,
    )