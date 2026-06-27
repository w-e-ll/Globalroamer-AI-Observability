#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os

from pathlib import Path

from dotenv import load_dotenv

from globalroamer_ai.lib.app_config import load_yaml_config
from globalroamer_ai.lib.setup_logger import setup_logger

from globalroamer_ai.lib.embedding_service import (
    EmbeddingService
)

from globalroamer_ai.lib.vector_store import (
    VectorStore
)

from globalroamer_ai.lib.similarity_search import (
    SimilaritySearchService
)

from globalroamer_ai.lib.exceptions import (
    GlobalRoamerAIException
)

load_dotenv()

logger = logging.getLogger("analyze_main")


def load_chunks(chunks_dir: str):
    """
    Load chunk JSON files from chunk directory.
    """

    chunks = []

    chunk_files = sorted(
        Path(chunks_dir).glob("*_chunks.json")
    )

    logger.info(
        f"Discovered {len(chunk_files)} chunk files"
    )

    for chunk_file in chunk_files:

        logger.info(
            f"Loading chunk file: {chunk_file}"
        )

        with open(chunk_file, "r", encoding="utf-8") as f:
            data = json.load(f)

            if isinstance(data, list):
                chunks.extend(data)

    logger.info(
        f"Loaded {len(chunks)} total chunks"
    )

    return chunks


def save_similarity_results(
    chunk_id: str,
    results: list,
    output_dir: str
):
    """
    Save similarity search results.
    """

    os.makedirs(output_dir, exist_ok=True)

    safe_chunk_id = (
        chunk_id
        .replace("/", "_")
        .replace(":", "_")
    )

    output_file = (
        Path(output_dir)
        / f"{safe_chunk_id}_similarity.json"
    )

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            results,
            f,
            indent=2,
            ensure_ascii=False
        )

    logger.info(
        f"Saved similarity results: {output_file}"
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config-dir",
        required=True,
        help="Path to config directory"
    )

    parser.add_argument(
        "--top-k",
        type=int,
        default=5,
        help="Top similar incidents to retrieve"
    )

    args = parser.parse_args()

    # -----------------------------------------------------
    # Config
    # -----------------------------------------------------

    cfg = load_yaml_config(
        args.config_dir
    )

    # -----------------------------------------------------
    # Logger
    # -----------------------------------------------------

    logfile = os.path.join(
        cfg.log_dir,
        "analyze.log"
    )

    setup_logger(logfile)

    logger.info(
        "=== GlobalRoamer AI Analysis Started ==="
    )

    try:

        # -------------------------------------------------
        # Embedding service
        # -------------------------------------------------

        embedding_service = EmbeddingService(
            model=cfg.embedding_model
        )

        # -------------------------------------------------
        # Vector DB
        # -------------------------------------------------

        vector_store = VectorStore(
            persist_directory=cfg.vector_db_dir,
            collection_name=cfg.vector_collection
        )

        # -------------------------------------------------
        # Similarity service
        # -------------------------------------------------

        similarity_service = SimilaritySearchService(
            embedding_service=embedding_service,
            vector_store=vector_store
        )

        # -------------------------------------------------
        # Load chunks
        # -------------------------------------------------

        chunks = load_chunks(
            cfg.chunks_dir
        )

        logger.info(
            f"Loaded {len(chunks)} chunks for analysis"
        )

        if not chunks:
            logger.warning(
                "No chunks available for analysis"
            )
            return

        # -------------------------------------------------
        # Generate embeddings
        # -------------------------------------------------

        texts = [
            chunk["text"]
            for chunk in chunks
        ]

        embeddings = embedding_service.embed_batch(
            texts=texts
        )

        logger.info(
            f"Generated {len(embeddings)} embeddings"
        )

        # -------------------------------------------------
        # Store embeddings
        # -------------------------------------------------

        vector_store.upsert_chunks(
            chunks=chunks,
            embeddings=embeddings
        )

        logger.info(
            f"Vector collection count="
            f"{vector_store.count()}"
        )

        # -------------------------------------------------
        # Similarity analysis
        # -------------------------------------------------

        similarity_output_dir = os.path.join(
            cfg.ai_summary_dir,
            "similarity_results"
        )

        for chunk in chunks:

            logger.info(
                f"Running similarity analysis "
                f"for chunk={chunk['chunk_id']}"
            )

            similar_results = (
                similarity_service.search_by_chunk(
                    chunk=chunk,
                    top_k=args.top_k
                )
            )

            save_similarity_results(
                chunk_id=chunk["chunk_id"],
                results=similar_results,
                output_dir=similarity_output_dir
            )

        logger.info(
            "=== GlobalRoamer AI Analysis Finished ==="
        )

    except GlobalRoamerAIException as e:

        logger.error(
            f"Application error: {e}"
        )

        raise

    except Exception as e:

        logger.exception(
            f"Unexpected fatal error: {e}"
        )

        raise


if __name__ == "__main__":
    main()
