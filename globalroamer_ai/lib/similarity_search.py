#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from typing import Dict, List, Optional

from globalroamer_ai.lib.embedding_service import EmbeddingService
from globalroamer_ai.lib.vector_store import VectorStore
from globalroamer_ai.lib.exceptions import SimilaritySearchError

logger = logging.getLogger("similarity_search")


class SimilaritySearchService:
    """
    High-level service for finding operationally similar telecom trace chunks.

    This combines:
    - embedding generation
    - vector DB query
    - result formatting
    """

    def __init__(
        self,
        embedding_service: EmbeddingService,
        vector_store: VectorStore
    ):
        self.embedding_service = embedding_service
        self.vector_store = vector_store

        logger.info("SimilaritySearchService initialized")

    def search_by_text(
        self,
        query_text: str,
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Find similar historical chunks using free-text query.

        Example:
        "LTE attach failure with authentication timeout"
        """

        if not query_text or not query_text.strip():
            raise SimilaritySearchError(
                "Query text cannot be empty"
            )

        try:
            logger.info(
                f"Running similarity search by text, top_k={top_k}"
            )

            query_embedding = self.embedding_service.embed_text(
                query_text
            )

            raw_result = self.vector_store.query_similar(
                query_embedding=query_embedding,
                top_k=top_k,
                where=where
            )

            return format_chroma_results(raw_result)

        except Exception as e:
            logger.error(
                f"Similarity search by text failed: {e}"
            )

            raise SimilaritySearchError(
                f"Similarity search by text failed: {e}"
            )

    def search_by_chunk(
        self,
        chunk: Dict,
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> List[Dict]:
        """
        Find similar historical chunks using an existing trace chunk.
        """

        try:
            query_text = chunk.get("text", "")

            if not query_text:
                raise SimilaritySearchError(
                    "Chunk does not contain text"
                )

            logger.info(
                f"Running similarity search for chunk={chunk.get('chunk_id')}"
            )

            return self.search_by_text(
                query_text=query_text,
                top_k=top_k,
                where=where
            )

        except Exception as e:
            logger.error(
                f"Similarity search by chunk failed: {e}"
            )

            raise SimilaritySearchError(
                f"Similarity search by chunk failed: {e}"
            )

    def search_by_failure_signals(
        self,
        signals: List[str],
        top_k: int = 5
    ) -> List[Dict]:
        """
        Find similar chunks based on operational signals.

        Example:
        ["attach", "authentication", "timeout"]
        """

        if not signals:
            raise SimilaritySearchError(
                "Signals list cannot be empty"
            )

        query_text = (
            "Telecom roaming trace failure involving: "
            + ", ".join(signals)
        )

        logger.info(
            f"Running similarity search by signals={signals}"
        )

        return self.search_by_text(
            query_text=query_text,
            top_k=top_k
        )


def format_chroma_results(raw_result: Dict) -> List[Dict]:
    """
    Convert ChromaDB query result into clean list of matches.
    """

    try:
        ids = raw_result.get("ids", [[]])[0]
        documents = raw_result.get("documents", [[]])[0]
        metadatas = raw_result.get("metadatas", [[]])[0]
        distances = raw_result.get("distances", [[]])[0]

        results = []

        for index, chunk_id in enumerate(ids):
            results.append({
                "rank": index + 1,
                "chunk_id": chunk_id,
                "distance": distances[index] if index < len(distances) else None,
                "similarity_score": distance_to_similarity(
                    distances[index] if index < len(distances) else None
                ),
                "text": documents[index] if index < len(documents) else "",
                "metadata": metadatas[index] if index < len(metadatas) else {},
            })

        logger.info(
            f"Formatted {len(results)} similarity results"
        )

        return results

    except Exception as e:
        logger.error(
            f"Failed to format similarity results: {e}"
        )

        raise SimilaritySearchError(
            f"Failed to format similarity results: {e}"
        )


def distance_to_similarity(distance: Optional[float]) -> Optional[float]:
    """
    Convert vector distance into simple approximate similarity score.

    Chroma distance depends on collection metric.
    This function gives an operationally readable score.
    """

    if distance is None:
        return None

    try:
        score = 1 / (1 + distance)
        return round(score, 4)

    except Exception:
        return None
