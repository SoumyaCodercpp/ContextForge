import os
import tempfile
import time
from pathlib import Path
from dotenv import load_dotenv
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from context_engine.index import ingest_pdfs, query
from context_engine.metadata import Document, EvaluationMetric, SearchHistory, SessionLocal, init_db
from context_engine.vectordb import collection_exists, create_collection, get_collection_info
from context_engine.embedder import get_embedding_dimension

load_dotenv()

DEFAULT_TOP_K = int(os.getenv("DEFAULT_TOP_K", "20"))
MAX_CONTEXT_TOKENS = int(os.getenv("MAX_CONTEXT_TOKENS", "4096"))
MAX_UPLOAD_SIZE_MB = int(os.getenv("MAX_UPLOAD_SIZE_MB", "50"))

app = FastAPI(
    title="ContextForge API",
    description="Intelligent Context Optimization Engine for Enterprise RAG Systems",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    """Initialize databases on server start."""
    init_db()
    if not collection_exists():
        vector_dim = get_embedding_dimension()
        create_collection(vector_size=vector_dim)


# Request / Response Models

class SearchRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000)
    top_k: int = Field(DEFAULT_TOP_K, ge=1, le=100)
    max_tokens: int = Field(MAX_CONTEXT_TOKENS, ge=256, le=32768)
    selection_strategy: str = Field("greedy_by_density", pattern="^(greedy_by_density|greedy_by_score)$")
    document_ids: list[int] = Field(None)


class UploadResponse(BaseModel):
    message: str
    document_ids: list[int]
    filenames: list[str]
    total_chunks: int
    processing_time_ms: int


# Endpoints

@app.get("/health")
async def health():
    # Health check endpoint.
    return {"status": "healthy", "service": "ContextForge API", "version": "0.1.0"}


@app.post("/upload")
async def upload(files: list[UploadFile] = File(...)):
    # Upload and index PDF documents.
    start = time.perf_counter()
    
    if not files:
        raise HTTPException(status_code=400, detail="No files provided.")
    
    tmp_dir = Path(tempfile.gettempdir()) / "contextforge_uploads"
    tmp_dir.mkdir(exist_ok=True)
    
    saved_paths = []
    filenames = []
    
    for file in files:
        if not file.filename or not file.filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail=f"'{file.filename}' is not a PDF.")
        
        content = await file.read()
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_UPLOAD_SIZE_MB:
            raise HTTPException(status_code=400, detail="File too large")
        
        tmp_path = tmp_dir / file.filename
        tmp_path.write_bytes(content)
        saved_paths.append(tmp_path)
        filenames.append(file.filename)
    
    try:
        document_ids = ingest_pdfs(saved_paths)
    except Exception as e:
        for p in saved_paths:
            try:
                p.unlink()
            except:
                pass
        raise HTTPException(status_code=500, detail=str(e))
    
    for p in saved_paths:
        try:
            p.unlink()
        except:
            pass
    
    session = SessionLocal()
    try:
        chunk_counts = session.query(Document.chunk_count).filter(Document.id.in_(document_ids)).all()
        total_chunks = 0
        for count_tuple in chunk_counts:
            total_chunks += count_tuple[0]
    finally:
        session.close()
    
    elapsed = int((time.perf_counter() - start) * 1000)
    
    return UploadResponse(
        message=f"Indexed {len(document_ids)} document(s)",
        document_ids=document_ids,
        filenames=filenames,
        total_chunks=total_chunks,
        processing_time_ms=elapsed,
    )


@app.post("/search")
async def search(request: SearchRequest):
    """Run the full ContextForge pipeline and return answer + all stage results."""
    try:
        result = query(
            question=request.question,
            top_k=request.top_k,
            max_tokens=request.max_tokens,
            selection_strategy=request.selection_strategy,
            document_ids=request.document_ids,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    
    _log_search(request, result)
    return _build_response(result)


@app.get("/metrics")
async def metrics():
    """Return aggregate pipeline statistics."""
    session = SessionLocal()
    try:
        total_docs = session.query(Document).count()
        
        chunk_counts = session.query(Document.chunk_count).all()
        total_chunks = 0
        for count_tuple in chunk_counts:
            total_chunks += count_tuple[0]
        
        total_searches = session.query(SearchHistory).count()
        
        from sqlalchemy import func
        avg_latency_result = session.query(func.avg(EvaluationMetric.latency_ms)).first()
        if avg_latency_result and avg_latency_result[0]:
            avg_latency = round(avg_latency_result[0], 2)
        else:
            avg_latency = 0.0
    finally:
        session.close()
    
    try:
        vector_info = get_collection_info()
    except:
        vector_info = {"error": "Qdrant unavailable"}
    
    return {
        "total_documents": total_docs,
        "total_chunks": total_chunks,
        "total_searches": total_searches,
        "avg_pipeline_latency_ms": avg_latency,
        "vector_collection_info": vector_info,
    }


@app.get("/documents")
async def list_documents():
    """List all uploaded documents."""
    session = SessionLocal()
    try:
        docs = session.query(Document).order_by(Document.uploaded_at.desc()).all()
        result = []
        for d in docs:
            result.append({
                "id": d.id,
                "filename": d.filename,
                "file_type": d.file_type,
                "file_size_bytes": d.file_size_bytes,
                "chunk_count": d.chunk_count,
                "uploaded_at": d.uploaded_at.isoformat(),
            })
        return result
    finally:
        session.close()

@app.delete("/documents/{document_id}")
async def delete_document(document_id: int):
    """Delete a document and all its chunks."""
    from context_engine.vectordb import delete_by_filter
    
    session = SessionLocal()
    try:
        # Delete from PostgreSQL
        doc = session.query(Document).filter(Document.id == document_id).first()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")
        
        session.delete(doc)
        session.commit()
        
        # Delete from Qdrant
        delete_by_filter({
            "must": [{"key": "document_id", "match": {"value": document_id}}]
        })
        
        return {"message": f"Deleted document {document_id}"}
    except HTTPException:
        raise
    except Exception as e:
        session.rollback()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        session.close()


# Helpers

def _build_response(result):
    """Convert pipeline result to API response format."""
    
    retrieved_list = []
    for c in result.retrieved:
        retrieved_list.append(_chunk_to_dict(c))
    
    dedup_kept = []
    dedup_removed = []
    if result.dedup_result:
        for c in result.dedup_result.kept:
            dedup_kept.append(_chunk_to_dict(c))
        for c in result.dedup_result.removed:
            dedup_removed.append(_chunk_to_dict(c))
    
    scored_list = []
    if result.scoring_result:
        for sc in result.scoring_result.ranked_chunks:
            scored_list.append(_scored_to_dict(sc))
    
    selected_list = []
    if result.selection_result:
        for sc in result.selection_result.selected:
            selected_list.append(_scored_to_dict(sc))
    
    response = {
        "query": result.query,
        "answer": result.answer,
        "pipeline_latency_ms": result.pipeline_latency_ms,
        "stages": result.stages_summary,
        "token_summary": result.token_summary,
        "retrieved": retrieved_list,
        "dedup": {
            "kept_count": len(dedup_kept),
            "removed_count": len(dedup_removed),
            "threshold": result.dedup_result.threshold if result.dedup_result else 0.0,
            "kept": dedup_kept,
            "removed": dedup_removed,
        },
        "scored": scored_list,
        "selection": {
            "selected_count": len(selected_list),
            "total_tokens": result.selection_result.total_tokens if result.selection_result else 0,
            "max_budget": result.selection_result.max_budget if result.selection_result else MAX_CONTEXT_TOKENS,
            "strategy": result.selection_result.strategy if result.selection_result else "",
            "savings": result.selection_result.savings if result.selection_result else {},
            "selected": selected_list,
        },
        "llm_usage": {},
    }
    
    if result.llm_response:
        response["llm_usage"] = {
            "model": result.llm_response.model,
            "prompt_tokens": result.llm_response.token_usage.get("prompt_tokens", 0),
            "completion_tokens": result.llm_response.token_usage.get("completion_tokens", 0),
            "total_tokens": result.llm_response.total_tokens,
            "latency_ms": result.llm_response.latency_ms,
        }
    
    return response


def _chunk_to_dict(c):
    """Convert a RetrievedChunk to a dictionary."""
    return {
        "chunk_id": c.chunk_id,
        "document_id": c.document_id,
        "text": c.text,
        "score": c.score,
        "chunk_index": c.chunk_index,
        "page_number": c.page_number,
    }


def _scored_to_dict(sc):
    """Convert a ScoredChunk to a dictionary."""
    return {
        "chunk_id": sc.chunk.chunk_id,
        "document_id": sc.chunk.document_id,
        "text": sc.chunk.text,
        "context_score": sc.context_score,
        "semantic_similarity": sc.semantic_similarity,
        "freshness_score": sc.freshness_score,
        "authority_score": sc.authority_score,
        "density_score": sc.density_score,
        "chunk_index": sc.chunk.chunk_index,
        "page_number": sc.chunk.page_number,
    }


def _log_search(request, result):
    """Log search data to PostgreSQL. Best-effort, never blocks the response."""
    try:
        session = SessionLocal()
        
        for chunk in result.retrieved:
            session.add(SearchHistory(
                query_text=request.question,
                chunk_id=chunk.chunk_id,
                retrieval_score=chunk.score,
                stage="retrieved",
            ))
        
        if result.llm_response:
            session.add(EvaluationMetric(
                query_text=request.question,
                answer_text=result.answer,
                latency_ms=result.pipeline_latency_ms,
                token_usage=result.llm_response.total_tokens,
            ))
        
        session.commit()
        session.close()
    except:
        try:
            session.close()
        except:
            pass