import re
from dataclasses import dataclass
from pathlib import Path
from pypdf import PdfReader

@dataclass
class Chunk:
    """A single text chunk from a document."""
    text: str
    chunk_index: int
    token_count: int = 0
    page_number: int = None

    def __post_init__(self):
        if self.token_count == 0:
            self.token_count = len(self.text.split())

@dataclass
class Document:
    """A processed document with its chunks."""
    filename: str
    file_type: str
    file_size_bytes: int
    chunks: list

    @property
    def chunk_count(self):
        return len(self.chunks)

def extract_text_from_pdf(file_path):
    """Extract text from each page of a PDF."""
    reader = PdfReader(str(file_path))
    pages = []
    for i, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append((i, text))  # (page_number, page_text)
    return pages

def chunk_text(text, chunk_size=500, chunk_overlap=50, page_number=None):
    """
    Split text into overlapping chunks using sentence boundaries.
    Overlap prevents information loss at chunk edges.
    """
    sentences = re.split(r"(?<=[.!?])\s+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    
    if not sentences:
        return []
    
    chunks = []
    current_words = []
    current_count = 0
    
    for sentence in sentences:
        words = sentence.split()
        word_count = len(words)
        
        # Finalizing current chunk if adding this sentence exceeds chunk_size
        if current_words and current_count + word_count > chunk_size:
            chunks.append(Chunk(
                text=" ".join(current_words),
                chunk_index=len(chunks),
                page_number=page_number
            ))
            # Keeping last N words as overlap for next chunk
            overlap_words = current_words[-chunk_overlap:] if chunk_overlap > 0 else []
            current_words = overlap_words
            current_count = len(overlap_words)
        
        current_words.extend(words)
        current_count += word_count
    
    # last chunk
    if current_words:
        chunks.append(Chunk(
            text=" ".join(current_words),
            chunk_index=len(chunks),
            page_number=page_number
        ))
    
    return chunks

def process_pdf(file_path, chunk_size=500, chunk_overlap=50):
    """Full pipeline: extract text from PDF and chunk it page by page."""
    path = Path(file_path)
    file_size = path.stat().st_size
    pages = extract_text_from_pdf(path)
    
    all_chunks = []
    for page_num, page_text in pages:
        all_chunks.extend(chunk_text(page_text, chunk_size, chunk_overlap, page_num))
    
    # Re-index chunks across the entire document
    for i, chunk in enumerate(all_chunks):
        chunk.chunk_index = i
    
    return Document(
        filename=path.name,
        file_type=path.suffix.lower().lstrip("."),
        file_size_bytes=file_size,
        chunks=all_chunks
    )