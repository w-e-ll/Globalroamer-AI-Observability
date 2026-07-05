#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from typing import Dict, List, Optional

import chromadb

from chromadb.config import Settings

from globalroamer_ai.core.exceptions import VectorStoreError

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
            "testcase_id": chunk.get("testcase_id"),
            "chunk_index": chunk.get("chunk_index"),

            "event_count": chunk.get("event_count"),

            "event_names": ",".join(chunk.get("event_names", [])),
            "event_families": ",".join(chunk.get("event_families", [])),
            "severities": ",".join(chunk.get("severities", [])),
            "causes": ",".join(chunk.get("causes", [])),

            "operators": ",".join(chunk.get("operators", [])),
            "countries": ",".join(chunk.get("countries", [])),
            "network_domains": ",".join(chunk.get("network_domains", [])),

            "tags": ",".join(chunk.get("tags", [])),

            "has_failure": chunk.get("has_failure", False),
            "has_high_severity": chunk.get("has_high_severity", False),
            "has_retry_recommended": chunk.get(
                "has_retry_recommended",
                False
            ),

            "source_trace": chunk.get("source_trace"),
            "source_result": chunk.get("source_result"),
            "source_report": chunk.get("source_report"),
        }

