import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String, Text, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, relationship, sessionmaker

load_dotenv()

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}"
    f":{os.getenv('POSTGRES_PASSWORD', 'postgres')}"
    f"@{os.getenv('POSTGRES_HOST', 'localhost')}"
    f":{os.getenv('POSTGRES_PORT', '5432')}"
    f"/{os.getenv('POSTGRES_DB', 'contextforge')}"
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True) 
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)

class Base(DeclarativeBase):
    pass

# Models

class Document(Base):
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(512), nullable=False)
    file_type = Column(String(32), nullable=False)
    file_size_bytes = Column(Integer, nullable=False)
    chunk_count = Column(Integer, nullable=False, default=0)
    uploaded_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    chunks = relationship("Chunk", back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    document_id = Column(Integer, ForeignKey("documents.id", ondelete="CASCADE"), nullable=False)
    chunk_index = Column(Integer, nullable=False)
    text = Column(Text, nullable=False)
    token_count = Column(Integer, nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    
    document = relationship("Document", back_populates="chunks")

class SearchHistory(Base):
    """Logs every query — which chunks were retrieved, deduped, scored, selected."""
    __tablename__ = "search_history"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    chunk_id = Column(Integer, ForeignKey("chunks.id", ondelete="SET NULL"), nullable=True)
    retrieval_score = Column(Float, nullable=True)
    relevance_score = Column(Float, nullable=True)
    was_selected = Column(Integer, nullable=False, default=0)
    stage = Column(String(32), nullable=False)  # retrieved, deduplicated, scored, selected
    searched_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

class EvaluationMetric(Base):
    """Tracks answer quality and pipeline performance."""
    __tablename__ = "evaluation_metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    query_text = Column(Text, nullable=False)
    answer_text = Column(Text, nullable=False)
    relevance_score = Column(Float, nullable=True)
    latency_ms = Column(Integer, nullable=True)
    token_usage = Column(Integer, nullable=True)
    evaluated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

# Init

def init_db():
    """Create all tables if they don't exist."""
    Base.metadata.create_all(bind=engine)