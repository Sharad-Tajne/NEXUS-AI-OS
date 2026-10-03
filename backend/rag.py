import os
import numpy as np
from dotenv import load_dotenv
from google import genai

load_dotenv()

client = genai.Client(
    api_key=os.getenv("GEMINI_API_KEY")
)


# =========================================================
# CREATE EMBEDDING
# =========================================================

def create_embedding(text: str):

    if not text or not text.strip():
        return []

    response = client.models.embed_content(
        model="gemini-embedding-001",
        contents=text.strip()
    )

    return response.embeddings[0].values


# =========================================================
# COSINE SIMILARITY
# =========================================================

def cosine_similarity(vector_a, vector_b):

    if not vector_a or not vector_b:
        return 0.0

    a = np.array(
        vector_a,
        dtype=float
    )

    b = np.array(
        vector_b,
        dtype=float
    )

    denominator = (
        np.linalg.norm(a)
        * np.linalg.norm(b)
    )

    if denominator == 0:
        return 0.0

    return float(
        np.dot(a, b) / denominator
    )


# =========================================================
# RANK DOCUMENTS
# =========================================================

def rank_documents(
    query,
    documents
):

    query_embedding = create_embedding(
        query
    )

    ranked = []

    for document in documents:

        document_embedding = document.get(
            "embedding",
            []
        )

        if not document_embedding:
            continue

        score = cosine_similarity(
            query_embedding,
            document_embedding
        )

        ranked.append({
            "document": document,
            "score": score
        })

    ranked.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return ranked


# =========================================================
# SMART RELEVANCE SEARCH
# =========================================================

def get_relevant_documents(
    query,
    documents,
    top_k=5,
    minimum_score=0.65
):

    # Never allow a weak threshold.
    # This also protects us if main.py
    # passes something like 0.30.

    minimum_score = max(
        minimum_score,
        0.65
    )

    ranked = rank_documents(
        query,
        documents
    )

    relevant = []

    for item in ranked:

        score = item["score"]

        # Ignore weak semantic matches
        if score < minimum_score:
            continue

        document = item["document"].copy()

        document["similarity"] = round(
            score,
            4
        )

        relevant.append(
            document
        )

        if len(relevant) >= top_k:
            break

    return relevant


# =========================================================
# SEMANTIC KNOWLEDGE SEARCH
# =========================================================

def search_knowledge_semantically(
    query,
    documents,
    top_k=5,
    minimum_score=0.65
):

    """
    Search stored knowledge using
    semantic similarity.

    Minimum relevance is always 65%.
    """

    return get_relevant_documents(
        query=query,
        documents=documents,
        top_k=top_k,
        minimum_score=minimum_score
    )