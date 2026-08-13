import os
import requests
from dotenv import load_dotenv

load_dotenv()

JINA_API_KEY = os.getenv("JINA_API_KEY")
JINA_MODEL = os.getenv("JINA_EMBEDDING_MODEL", "jina-embeddings-v3")
JINA_URL = "https://api.jina.ai/v1/embeddings"

def _call_jina(texts, task):

    # HTTP headers dictionary
    headers = {"Authorization": f"Bearer {JINA_API_KEY}", "Content-Type": "application/json"}

    #request body dictionary
    payload = {"model": JINA_MODEL, "input": texts, "task": task}
    
    response = requests.post(JINA_URL, json=payload, headers=headers, timeout=60)
    
    if response.status_code == 200:
        data = response.json()
        """
        {
            "data": [
                {"embedding": [0.023, -0.451, 0.789, ...]},
                {"embedding": [0.018, -0.432, 0.801, ...]}
            ]
        }
        """
        embeddings = []
        for item in data["data"]:
            embeddings.append(item["embedding"])
        return embeddings
    
    raise RuntimeError(f"Jina API failed: {response.status_code}")

def embed_chunks(texts):
    """Convert document chunks to vectors — batched for efficiency."""
    all_embeddings = []
    batch_size = 100
    
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        all_embeddings.extend(_call_jina(batch, task="retrieval.passage"))
    
    return all_embeddings

def embed_query(query):
    """Convert a user question to a vector."""
    return _call_jina([query], task="retrieval.query")[0]

def get_embedding_dimension():
    """Auto-detect vector size from API (currently 1024 for Jina v3)."""
    return len(embed_query("test"))