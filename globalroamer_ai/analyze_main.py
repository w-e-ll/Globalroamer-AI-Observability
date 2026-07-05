#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os

from pathlib import Path

from dotenv import load_dotenv

from globalroamer_ai.core.app_config import load_yaml_config
from globalroamer_ai.ai.embedding_service import EmbeddingService
from globalroamer_ai.core.exceptions import GlobalRoamerAIException
from globalroamer_ai.core.setup_logger import setup_logger
from globalroamer_ai.ai.similarity_search import SimilaritySearchService, build_semantic_chunk_text
from globalroamer_ai.ingestion.trace_chunker import chunk_normalized_trace
from globalroamer_ai.ai.vector_store import VectorStore


load_dotenv()

logger = logging.getLogger("analyze_main")


def load_event_files(normalized_dir: str) -> list[dict]:
    event_files = sorted(Path(normalized_dir).glob("*_events.json"))
    traces = []

    logger.info(f"Discovered {len(event_files)} normalized event files")

    for event_file in event_files:
        with open(event_file, "r", encoding="utf-8") as f:
            events = json.load(f)

        if not isinstance(events, list):
            logger.warning(f"Skipping non-list events file: {event_file}")
            continue

        testcase_id = event_file.name.replace("_events.json", "")

        traces.append({
            "trace_id": testcase_id,
            "testcase_id": testcase_id,
            "normalized_events": events,
            "source_file": str(event_file),
        })

    logger.info(f"Loaded {len(traces)} normalized traces")
    return traces


def save_chunks(chunks: list[dict], output_file: Path) -> None:
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"Saved chunks: {output_file}")


def build_chunks(normalized_dir: str, chunks_dir: str, chunk_size: int, chunk_overlap: int) -> list[dict]:
    traces = load_event_files(normalized_dir)
    all_chunks = []

    for trace in traces:
        chunks = chunk_normalized_trace(trace, chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        testcase_id = trace["testcase_id"]
        output_file = Path(chunks_dir) / f"{testcase_id}_chunks.json"
        save_chunks(chunks, output_file)
        all_chunks.extend(chunks)
        logger.info(f"Chunked testcase={testcase_id}, chunks={len(chunks)}")
        print(f"Chunked testcase={testcase_id}, chunks={len(chunks)}")

    logger.info(f"Created {len(all_chunks)} total chunks")
    return all_chunks


def load_chunks(chunks_dir: str) -> list[dict]:
    chunks = []
    chunk_files = sorted(Path(chunks_dir).glob("*_chunks.json"))

    logger.info(f"Discovered {len(chunk_files)} chunk files")

    for chunk_file in chunk_files:
        with open(chunk_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, list):
            chunks.extend(data)

    logger.info(f"Loaded {len(chunks)} total chunks")
    return chunks


def save_similarity_results(chunk_id: str, results: list, output_dir: str) -> None:
    os.makedirs(output_dir, exist_ok=True)
    safe_chunk_id = chunk_id.replace("/", "_").replace("\\", "_").replace(":", "_")
    output_file = Path(output_dir) / f"{safe_chunk_id}_similarity.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)

    logger.info(f"Saved similarity results: {output_file}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="analyze_main.py")
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--normalized-dir", required=False)
    parser.add_argument("--chunks-dir", required=False)
    parser.add_argument("--skip-embedding", action="store_true")
    parser.add_argument("--skip-similarity", action="store_true")
    parser.add_argument("--top-k", type=int, default=5)
    args = parser.parse_args()

    cfg = load_yaml_config(args.config_dir)

    logfile = os.path.join(cfg.log_dir, "analyze.log")
    setup_logger(logfile)

    normalized_dir = args.normalized_dir or cfg.normalized_dir
    chunks_dir = args.chunks_dir or cfg.chunks_dir

    logger.info("=== GlobalRoamer AI Analysis Started ===")
    logger.info(f"Normalized input directory: {normalized_dir}")
    logger.info(f"Chunks output directory: {chunks_dir}")

    try:
        chunks = build_chunks(normalized_dir=normalized_dir, chunks_dir=chunks_dir, chunk_size=cfg.chunk_size, chunk_overlap=cfg.chunk_overlap)

        if not chunks:
            logger.warning("No chunks created for analysis")
            return

        if args.skip_embedding:
            logger.info("Skipping embedding/vector stage")
            return

        embedding_service = EmbeddingService(model=cfg.embedding_model)
        vector_store = VectorStore(persist_directory=cfg.vector_db_dir, collection_name=cfg.vector_collection)
        similarity_service = SimilaritySearchService(embedding_service=embedding_service, vector_store=vector_store)

        texts = []

        for chunk in chunks:
            semantic_text = build_semantic_chunk_text(chunk)

            texts.append(semantic_text.strip())

        embeddings = embedding_service.embed_batch(texts=texts, batch_size=20)

        logger.info(f"Generated {len(embeddings)} embeddings")

        vector_store.upsert_chunks(chunks=chunks, embeddings=embeddings)

        logger.info(f"Vector collection count={vector_store.count()}")

        if args.skip_similarity:
            logger.info("Skipping similarity stage")
            return

        similarity_output_dir = os.path.join(cfg.ai_summary_dir, "similarity_results")

        for chunk in chunks:
            similar_results = similarity_service.search_by_chunk(chunk=chunk, top_k=args.top_k)
            save_similarity_results(chunk_id=chunk["chunk_id"], results=similar_results, output_dir=similarity_output_dir)

        logger.info("=== GlobalRoamer AI Analysis Finished ===")

    except GlobalRoamerAIException as exc:
        logger.error(f"Application error: {exc}")
        raise

    except Exception as exc:
        logger.exception(f"Unexpected fatal error: {exc}")
        raise


if __name__ == "__main__":
    main()
