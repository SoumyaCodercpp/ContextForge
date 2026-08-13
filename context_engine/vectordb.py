import os
from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.http import models as qdrant_models
from qdrant_client.http.exceptions import UnexpectedResponse

load_dotenv()

QDRANT_HOST = os.getenv("QDRANT_HOST", "localhost")
QDRANT_PORT = int(os.getenv("QDRANT_PORT", "6333"))
COLLECTION_NAME = os.getenv("QDRANT_COLLECTION_NAME", "contextforge_docs")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", "")

if QDRANT_API_KEY:
    client = QdrantClient(url=QDRANT_HOST, api_key=QDRANT_API_KEY)
else:
    client = QdrantClient(host=QDRANT_HOST, port=QDRANT_PORT)

def collection_exists(name=COLLECTION_NAME):
    try:
        client.get_collection(name)
        return True
    except (UnexpectedResponse, ValueError):
        return False

def create_collection(name=COLLECTION_NAME, vector_size=1024, distance="Cosine"):
    if collection_exists(name):
        return
    client.create_collection(
        collection_name=name,
        vectors_config=qdrant_models.VectorParams(size=vector_size, distance=distance),
    )

def get_collection_info(name=COLLECTION_NAME):
    return client.get_collection(name).model_dump()

def delete_collection(name=COLLECTION_NAME):
    client.delete_collection(name)

# Vector operations

def upsert_vectors(points, collection_name=COLLECTION_NAME):
    """Insert or update points. Each point: {id, vector, payload}."""
    qdrant_points = []

    """
    [
        {"id": 1, "vector": [0.023, -0.451, ...], "payload": {"text": "...", "document_id": 1}},
        {"id": 2, "vector": [0.018, -0.432, ...], "payload": {"text": "...", "document_id": 1}},
    ]
    """
    for p in points:
        qdrant_points.append(
            qdrant_models.PointStruct(
                id=p["id"],
                vector=p["vector"],
                payload=p.get("payload", {})
            )
        )
    client.upsert(collection_name=collection_name, points=qdrant_points) #Sends all points to Qdrant    

def search_vectors(query_vector, top_k=20, collection_name=COLLECTION_NAME, query_filter=None):
    """Find top_k nearest vectors to query_vector. Returns [{id, score, payload}]."""
    search_filter = None
    if query_filter:
        search_filter = qdrant_models.Filter(**query_filter)
    
    results = client.query_points(
        collection_name=collection_name,
        query=query_vector,
        limit=top_k,
        query_filter=search_filter,
        with_payload=True,
    )
    
    output = []
    for hit in results.points:
        output.append({
            "id": hit.id,
            "score": hit.score,
            "payload": hit.payload,
        })
    return output

def delete_vectors(point_ids, collection_name=COLLECTION_NAME):
    """Delete specific points by ID."""
    client.delete(
        collection_name=collection_name,
        points_selector=qdrant_models.PointIdsList(points=point_ids),
    )

def delete_by_filter(filter_dict, collection_name=COLLECTION_NAME):
    """Delete all points matching a filter (e.g., all chunks from a document)."""
    client.delete(
        collection_name=collection_name,
        points_selector=qdrant_models.FilterSelector(
            filter=qdrant_models.Filter(**filter_dict)
        ),
    )