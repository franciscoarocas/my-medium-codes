from functools import lru_cache

import numpy as np


EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_model():
    """
        Load the embedding model only once (it is downloaded the first time).
        Returns:
            A SentenceTransformer model
    """

    from sentence_transformers import SentenceTransformer

    return SentenceTransformer(EMBEDDING_MODEL)


def embed(text: str) -> np.ndarray:
    """
        Convert a text into its embedding: a list of numbers that represents its meaning.
        Params:
            - text: Any text
        Returns:
            The embedding vector
    """

    return get_model().encode(text)


def cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    """
        Cosine similarity between two vectors: 1 = same direction, 0 = unrelated.
        Params:
            - a: First vector
            - b: Second vector
        Returns:
            Similarity between -1 and 1
    """

    return float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))


def semantic_similarity(reference: str, answer: str) -> float:
    """
        Compare the MEANING of two texts using embeddings.
        Params:
            - reference: Reference answer we know is correct
            - answer: Answer returned by the model
        Returns:
            Cosine similarity between both embeddings
    """

    return cosine_similarity(embed(reference), embed(answer))
