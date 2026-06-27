#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from typing import Dict, List, Optional

import chromadb

from chromadb.config import Settings

from globalroamer_ai.lib.exceptions import VectorStoreError

logger = logging.getLogger("vector_store")


class VectorStore:
    """
    ChromaDB-backed vector storage for GlobalRoamer trace chunks.

    Stores:
    - chunk text
    - embedding vector
    - operational metadata
    """

    def __init__(
        self,
        persist_directory: str,
        collection_name: str
    ):
        self.persist_directory = persist_directory
        self.collection_name = collection_name

        try:
            self.client = chromadb.PersistentClient(
                path=self.persist_directory,
                settings=Settings(
                    anonymized_telemetry=False
                )
            )

            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={
                    "description": (
                        "GlobalRoamer telecom trace chunks "
                        "for AI observability and similarity search"
                    )
                }
            )

            logger.info(
                f"VectorStore initialized: "
                f"collection={self.collection_name}, "
                f"path={self.persist_directory}"
            )

        except Exception as e:
            logger.error(
                f"Failed to initialize VectorStore: {e}"
            )

            raise VectorStoreError(
                f"Failed to initialize VectorStore: {e}"
            )

    def upsert_chunks(
        self,
        chunks: List[Dict],
        embeddings: List[List[float]]
    ) -> None:
        """
        Upsert trace chunks and embeddings into ChromaDB.
        """

        if len(chunks) != len(embeddings):
            raise VectorStoreError(
                "Chunks and embeddings length mismatch"
            )

        if not chunks:
            logger.info("No chunks to upsert")
            return

        try:
            ids = []
            documents = []
            metadatas = []

            for chunk, embedding in zip(chunks, embeddings):
                ids.append(chunk["chunk_id"])
                documents.append(chunk["text"])
                metadatas.append(
                    self._build_metadata(chunk)
                )

            self.collection.upsert(
                ids=ids,
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas
            )

            logger.info(
                f"Upserted {len(chunks)} chunks "
                f"into collection={self.collection_name}"
            )

        except Exception as e:
            logger.error(
                f"Failed to upsert chunks: {e}"
            )

            raise VectorStoreError(
                f"Failed to upsert chunks: {e}"
            )

    def query_similar(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        where: Optional[Dict] = None
    ) -> Dict:
        """
        Query similar chunks by embedding.
        """

        try:
            result = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=top_k,
                where=where
            )

            logger.info(
                f"Similarity search returned "
                f"{len(result.get('ids', [[]])[0])} results"
            )

            return result

        except Exception as e:
            logger.error(
                f"Vector search failed: {e}"
            )

            raise VectorStoreError(
                f"Vector search failed: {e}"
            )

    def count(self) -> int:
        """
        Return number of stored chunks.
        """

        try:
            return self.collection.count()

        except Exception as e:
            logger.error(
                f"Failed to count vector collection: {e}"
            )

            raise VectorStoreError(
                f"Failed to count vector collection: {e}"
            )

    @staticmethod
    def _build_metadata(chunk: Dict) -> Dict:
        """
        Convert chunk metadata into Chroma-compatible metadata.

        Chroma metadata values must be scalar:
        str, int, float, bool, or None.
        """

        return {
            "trace_id": chunk.get("trace_id"),
            "chunk_index": chunk.get("chunk_index"),
            "source_file": chunk.get("source_file"),
            "source_path": chunk.get("source_path"),
            "event_count": chunk.get("event_count"),
            "event_types": ",".join(chunk.get("event_types", [])),
            "signals": ",".join(chunk.get("signals", [])),
            "severities": ",".join(chunk.get("severities", [])),
        }
