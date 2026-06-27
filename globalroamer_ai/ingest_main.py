#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os

from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

from globalroamer_ai.lib.app_config import load_yaml_config
from globalroamer_ai.lib.setup_logger import setup_logger

from globalroamer_ai.lib.trace_loader import (
    load_all_traces
)

from globalroamer_ai.lib.trace_parser import (
    parse_trace_content
)

from globalroamer_ai.lib.trace_normalizer import (
    normalize_parsed_trace
)

from globalroamer_ai.lib.trace_chunker import (
    chunk_normalized_trace
)

from globalroamer_ai.lib.exceptions import (
    GlobalRoamerAIException
)

load_dotenv()

logger = logging.getLogger("ingest_main")


def save_normalized_trace(
    normalized_trace: dict,
    output_dir: str
) -> Path:
    """
    Save normalized trace JSON.
    """

    os.makedirs(output_dir, exist_ok=True)

    trace_id = normalized_trace["trace_id"]

    output_file = Path(output_dir) / f"{trace_id}.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            normalized_trace,
            f,
            indent=2,
            ensure_ascii=False
        )

    logger.info(
        f"Saved normalized trace: {output_file}"
    )

    return output_file


def save_chunks(
    chunks: list,
    output_dir: str
) -> Path:
    """
    Save chunks JSON.
    """

    os.makedirs(output_dir, exist_ok=True)

    if not chunks:
        raise ValueError("No chunks to save")

    trace_id = chunks[0]["trace_id"]

    output_file = Path(output_dir) / f"{trace_id}_chunks.json"

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(
            chunks,
            f,
            indent=2,
            ensure_ascii=False
        )

    logger.info(
        f"Saved chunks: {output_file}"
    )

    return output_file


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--config-dir",
        required=True,
        help="Path to config directory"
    )

    args = parser.parse_args()

    # -----------------------------------------------------
    # Load config
    # -----------------------------------------------------

    cfg = load_yaml_config(
        args.config_dir
    )

    # -----------------------------------------------------
    # Logger
    # -----------------------------------------------------

    logfile = os.path.join(
        cfg.log_dir,
        "ingest.log"
    )

    setup_logger(logfile)

    logger.info(
        "=== GlobalRoamer AI Ingest Started ==="
    )

    logger.info(
        f"Environment: {cfg.env}"
    )

    logger.info(
        f"Trace input directory: "
        f"{cfg.input_trace_dir}"
    )

    try:

        # -------------------------------------------------
        # Load traces
        # -------------------------------------------------

        traces = load_all_traces(
            trace_dir=cfg.input_trace_dir,
            supported_extensions=[
                ext.lower()
                for ext in [
                    ".csv",
                    ".log",
                    ".txt"
                ]
            ]
        )

        logger.info(
            f"Loaded {len(traces)} trace files"
        )

        # -------------------------------------------------
        # Process traces
        # -------------------------------------------------

        for trace in traces:

            metadata = trace["metadata"]
            content = trace["content"]

            trace_name = metadata["filename"]

            logger.info(
                f"Processing trace: {trace_name}"
            )

            # ---------------------------------------------
            # Parse
            # ---------------------------------------------

            parsed_trace = parse_trace_content(
                content=content,
                metadata=metadata
            )

            # ---------------------------------------------
            # Normalize
            # ---------------------------------------------

            normalized_trace = normalize_parsed_trace(
                parsed_trace
            )

            # ---------------------------------------------
            # Save normalized JSON
            # ---------------------------------------------

            save_normalized_trace(
                normalized_trace,
                cfg.normalized_dir
            )

            # ---------------------------------------------
            # Chunking
            # ---------------------------------------------

            chunks = chunk_normalized_trace(
                normalized_trace=normalized_trace,
                chunk_size=cfg.chunk_size,
                chunk_overlap=cfg.chunk_overlap
            )

            logger.info(
                f"Generated {len(chunks)} chunks "
                f"for {trace_name}"
            )

            # ---------------------------------------------
            # Save chunks
            # ---------------------------------------------

            save_chunks(
                chunks,
                cfg.chunks_dir
            )

        logger.info(
            "=== GlobalRoamer AI Ingest Finished ==="
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
