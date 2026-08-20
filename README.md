# ContextForge — Intelligent Context Optimization for RAG

A production-grade RAG optimization engine that reduces LLM token costs by 50-70% through a 3-stage context refinement pipeline.

Unlike standard RAG systems that dump all retrieved chunks into the LLM, ContextForge treats every chunk as a candidate — not all deserve to reach the prompt.

**Live Demo** | **GitHub** | **Backend API**

---

## The Core Insight

Most RAG systems send every retrieved chunk to the LLM — duplicates, headers, boilerplate and all. ContextForge treats retrieval as a filtering problem:

- Near-duplicate chunks get removed before scoring (cosine ≥ 0.85)
- Low-quality chunks get downweighted (headers, whitespace, filler words)
- High-value chunks get selected within token budget (greedy knapsack)
- The LLM sees only the best context — saving tokens, improving answers

---

## Architecture

```
User Question
│
▼
┌──────────────────────────────────────────┐
│ STAGE 1: DEDUPLICATION │
│ Greedy score-priority cosine similarity │
│ Removes near-duplicate chunks │
└──────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────┐
│ STAGE 2: SCORING │
│ 4-factor weighted model │
│ Semantic 45% + Density 25% │
│ Freshness 15% + Authority 15% │
└──────────────────────────────────────────┘
│
▼
┌──────────────────────────────────────────┐
│ STAGE 3: SELECTION │
│ Greedy knapsack by value-density │
│ Picks optimal subset within budget │
└──────────────────────────────────────────┘
│
▼
LLM (Groq) → Answer + Pipeline Viz

```

---

## The 3 Optimization Stages

### 1. Deduplication
Removes near-duplicate chunks using embedding cosine similarity.
Algorithm: Greedy score-priority
Threshold: 0.85 (configurable)
Result: 80% duplicate removal in benchmark tests


### 2. Scoring
Ranks each chunk on 4 weighted factors:

| Factor | Weight | What It Measures |
|--------|--------|------------------|
| Semantic | 45% | How well does chunk match question? |
| Density | 25% | How much actual information? |
| Freshness | 15% | How recently was it indexed? |
| Authority | 15% | How trustworthy is the source? |

### 3. Selection
Picks the best subset that fits within token budget.
Problem: 0/1 Knapsack (NP-Hard)
Solution: Greedy approximation by value-density
Strategies: greedy_by_density (default) or greedy_by_score


---

## Tech Stack

| Layer | Technology |
|-------|------------|
| Backend | Python, FastAPI |
| Frontend | Next.js, TypeScript, TailwindCSS |
| Vector DB | Qdrant (1024-dim vectors) |
| Metadata DB | PostgreSQL (4 tables) |
| Embeddings | Jina AI v3 (asymmetric embeddings) |
| LLM | Groq (OpenAI-compatible) |
| Deployment | Render (backend) + Vercel (frontend) |

---

## Features

- 📄 **Multi-PDF ingestion** — batch upload, auto-chunking, embeddings stored in Qdrant
- 🔍 **Semantic search** — question-to-vector retrieval with cosine similarity
- 🧹 **Deduplication** — removes near-duplicates before LLM inference
- ⭐ **4-factor scoring** — semantic, density, freshness, authority
- ✂️ **Token-budget selection** — knapsack-optimized chunk picking
- 📊 **Pipeline dashboard** — visualizes all 7 stages in real-time
- 💰 **Token savings** — 50-70% reduction in LLM input tokens
- 🗑️ **Document management** — list, view, and delete indexed documents

---

## Getting Started

### Prerequisites
- Python 3.10+
- Node.js 18+
- Docker Desktop (for local databases)
- Free accounts: Jina, Groq, Qdrant, Render (optional)


### Installation

```bash
# Clone the repo
git clone https://github.com/SoumyaCodercpp/ContextForge.git
cd ContextForge

# Install backend dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
```

### Environment Variables

Fill in your `.env` file with your API keys and database URLs:

```text
# Embeddings
JINA_API_KEY=your-jina-key
JINA_EMBEDDING_MODEL=jina-embeddings-v3

# LLM
OPENAI_API_KEY=your-groq-key
OPENAI_MODEL=llama-3.1-8b-instant
OPENAI_BASE_URL=https://api.groq.com/openai/v1

# Qdrant
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION_NAME=contextforge_docs

# PostgreSQL
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=contextforge
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Pipeline
CHUNK_SIZE=500
CHUNK_OVERLAP=50
DEFAULT_TOP_K=20
MAX_CONTEXT_TOKENS=1500
DEDUP_THRESHOLD=0.85
```

### Run Locally

```bash
# Start databases (Docker)
docker run -d -p 6333:6333 qdrant/qdrant
docker run -d -p 5432:5432 -e POSTGRES_USER=postgres -e POSTGRES_PASSWORD=postgres -e POSTGRES_DB=contextforge postgres:16

# Start backend
uvicorn api:app --reload

# Start frontend
cd frontend
npm install
npm run dev
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/upload` | Upload and index PDF documents |
| POST | `/search` | Run full optimization pipeline |
| GET | `/documents` | List all indexed documents |
| DELETE | `/documents/{id}` | Delete document, chunks, and vectors |
| GET | `/metrics` | Aggregate pipeline statistics |
| GET | `/health` | Health check |

---

## Project Structure

```text

├── api.py                        ← FastAPI server
├── context_engine/
│   ├── chunker.py                ← PDF → text chunks
│   ├── embedder.py               ← Jina embeddings
│   ├── vectordb.py               ← Qdrant operations
│   ├── metadata.py               ← PostgreSQL models
│   ├── retriever.py              ← Query → vector search
│   ├── llm.py                    ← LLM API
│   ├── index.py                  ← Orchestrator
│   └── context/
│       ├── deduplicator.py       ← Stage 1
│       ├── scorer.py             ← Stage 2
│       └── selector.py           ← Stage 3

```


---

## What Makes It Different

| Feature | Standard RAG | ContextForge |
|---------|--------------|--------------|
| Chunks sent to LLM | All retrieved (10-20) | Only best 3-5 |
| Duplicate handling | None | 80% removed |
| Scoring | Retrieval score only | 4-factor composite |
| Token budget | Ignored | Knapsack-optimized |
| Cost savings | 0% | 50-70% |
| Pipeline visibility | None | Full 7-stage dashboard |

---

## How I'd Scale This

- **Async ingestion** — Celery/Redis for large PDF batches
- **Qdrant cluster** — for millions of vectors
- **PostgreSQL read replicas** — for analytics queries
- **Rate limiting** — on LLM and embedding API calls
- **Caching** — Redis for frequently asked questions
- **Monitoring** — Prometheus/Grafana for pipeline metrics

---

Built with Python, FastAPI, Next.js, Qdrant, PostgreSQL, Jina AI, and Groq.
