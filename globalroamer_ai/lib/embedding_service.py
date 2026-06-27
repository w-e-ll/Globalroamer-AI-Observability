#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

from typing import List

from dotenv import load_dotenv
from openai import OpenAI

from globalroamer_ai.lib.exceptions import EmbeddingGenerationError

load_dotenv()

logger = logging.getLogger("embedding_service")


class EmbeddingService:
    """
    Service for generating embeddings for normalized telecom trace chunks.

    Initial implementation uses OpenAI embeddings.
    Later this can be replaced or extended with:
    - SentenceTransformers
    - local embedding models
    - enterprise-hosted embedding endpoints
    """

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise EmbeddingGenerationError(
                "OPENAI_API_KEY is not configured"
            )

        self.client = OpenAI(api_key=self.api_key)

        logger.info(
            f"EmbeddingService initialized with model={self.model}"
        )

    def embed_text(self, text: str) -> List[float]:
        """
        Generate embedding for a single text.
        """

        if not text or not text.strip():
            raise EmbeddingGenerationError(
                "Cannot embed empty text"
            )

        try:
            response = self.client.embeddings.create(
                model=self.model,
                input=text
            )

            embedding = response.data[0].embedding

            logger.info(
                f"Generated embedding with dimension={len(embedding)}"
            )

            return embedding

        except Exception as e:
            logger.error(
                f"Failed to generate embedding: {e}"
            )

            raise EmbeddingGenerationError(
                f"Failed to generate embedding: {e}"
            )

    def embed_batch(
        self,
        texts: List[str],
        batch_size: int = 50
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts.

        Uses batching to reduce API overhead.
        """

        if not texts:
            return []

        embeddings = []

        try:
            for start in range(0, len(texts), batch_size):
                batch = texts[start:start + batch_size]

                logger.info(
                    f"Generating embeddings for batch "
                    f"{start} - {start + len(batch)}"
                )

                response = self.client.embeddings.create(
                    model=self.model,
                    input=batch
                )

                batch_embeddings = [
                    item.embedding
                    for item in response.data
                ]

                embeddings.extend(batch_embeddings)

            logger.info(
                f"Generated {len(embeddings)} embeddings"
            )

            return embeddings

        except Exception as e:
            logger.error(
                f"Failed to generate batch embeddings: {e}"
            )

            raise EmbeddingGenerationError(
                f"Failed to generate batch embeddings: {e}"
            )
