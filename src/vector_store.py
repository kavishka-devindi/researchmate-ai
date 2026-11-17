import time

import chromadb
from google import genai
from google.genai import types, errors

from src.config import GEMINI_API_KEY, EMBEDDING_MODEL, EMBEDDING_DIM, CHROMA_DIR

client = genai.Client(api_key=GEMINI_API_KEY)
chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)

BATCH_SIZE = 50


class VectorStoreError(Exception):
    """Raised with a user-friendly message when embedding or storage fails."""


def _embed_batch(batch, task_type):
    """Embed one batch of texts, retrying on temporary errors."""
    for attempt in range(4):
        try:
            result = client.models.embed_content(
                model=EMBEDDING_MODEL,
                contents=batch,
                config=types.EmbedContentConfig(
                    task_type=task_type,
                    output_dimensionality=EMBEDDING_DIM,
                ),
            )
            return [e.values for e in result.embeddings]
        except errors.APIError as e:
            if e.code in (400, 401, 403):
                raise VectorStoreError(
                    "The embedding request was rejected. Check your API key."
                ) from e
            if e.code in (429, 500, 503, 504) and attempt < 3:
                time.sleep(15 * (attempt + 1))  # wait 15s, 30s, 45s
                continue
            raise VectorStoreError(
                "The embedding service is busy or rate-limited. Please try again in a minute."
            ) from e
        except Exception as e:
            raise VectorStoreError(
                "Could not reach the embedding service. Check your internet connection."
            ) from e


def embed_texts(texts, task_type="RETRIEVAL_DOCUMENT"):
    """Turn a list of texts into a list of vectors (same order)."""
    vectors = []
    for start in range(0, len(texts), BATCH_SIZE):
        vectors.extend(_embed_batch(texts[start:start + BATCH_SIZE], task_type))
    return vectors


def get_collection():
    """Open (or create) the ChromaDB collection that holds our chunks."""
    return chroma_client.get_or_create_collection(
        name="documents",
        configuration={"hnsw": {"space": "cosine"}},
    )


def add_chunks(chunks):
    """Embed new chunks and store them. Returns how many were newly added."""
    if not chunks:
        return 0
    collection = get_collection()

    ids = [c["chunk_id"] for c in chunks]
    existing = set(collection.get(ids=ids)["ids"])
    new_chunks = [c for c in chunks if c["chunk_id"] not in existing]
    if not new_chunks:
        return 0

    vectors = embed_texts([c["text"] for c in new_chunks])
    collection.upsert(
        ids=[c["chunk_id"] for c in new_chunks],
        embeddings=vectors,
        documents=[c["text"] for c in new_chunks],
        metadatas=[{"source": c["source"], "page": c["page"]} for c in new_chunks],
    )
    return len(new_chunks)

def search_chunks(question, k=4):
    """Return the k chunks most similar in meaning to the question.

    Each result: {"text", "source", "page", "score"}  (score: 1.0 = identical meaning)
    """
    collection = get_collection()
    if collection.count() == 0:
        return []

    query_vector = embed_texts([question], task_type="RETRIEVAL_QUERY")[0]
    results = collection.query(
        query_embeddings=[query_vector],
        n_results=min(k, collection.count()),
        include=["documents", "metadatas", "distances"],
    )

    hits = []
    for text, meta, dist in zip(
        results["documents"][0], results["metadatas"][0], results["distances"][0]
    ):
        hits.append(
            {
                "text": text,
                "source": meta["source"],
                "page": meta["page"],
                "score": round(1 - dist, 3),
            }
        )
    return hits

def stored_documents():
    """List the documents in the database with their chunk counts."""
    data = get_collection().get(include=["metadatas"])
    counts = {}
    for meta in data["metadatas"]:
        counts[meta["source"]] = counts.get(meta["source"], 0) + 1
    return [{"File": name, "Chunks": n} for name, n in sorted(counts.items())]


def clear_collection():
    """Delete all stored documents."""
    try:
        chroma_client.delete_collection("documents")
    except Exception:
        pass