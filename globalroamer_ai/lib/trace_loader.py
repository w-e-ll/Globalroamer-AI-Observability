#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import logging
from pathlib import Path
from typing import List, Dict

from globalroamer_ai.lib.exceptions import TraceLoaderError

logger = logging.getLogger("trace_loader")


def discover_trace_files(
    trace_dir: str,
    supported_extensions: List[str]
) -> List[Path]:
    """
    Discover trace files recursively.

    Args:
        trace_dir: Root traces directory
        supported_extensions: Allowed file extensions

    Returns:
        List of trace file paths
    """

    logger.info(
        f"Scanning trace directory: {trace_dir}"
    )

    if not os.path.isdir(trace_dir):
        raise TraceLoaderError(
            f"Trace directory does not exist: {trace_dir}"
        )

    trace_files = []

    for root, _, files in os.walk(trace_dir):
        for file in files:
            file_path = Path(root) / file

            if file_path.suffix.lower() in supported_extensions:
                trace_files.append(file_path)

    logger.info(
        f"Discovered {len(trace_files)} trace files"
    )

    return sorted(trace_files)


def load_trace_file(
    trace_path: Path,
    encoding: str = "utf-8"
) -> str:
    """
    Load raw trace file content.

    Args:
        trace_path: Path to trace file
        encoding: File encoding

    Returns:
        Raw file content
    """

    logger.info(
        f"Loading trace file: {trace_path}"
    )

    if not trace_path.exists():
        raise TraceLoaderError(
            f"Trace file does not exist: {trace_path}"
        )

    try:
        with open(
            trace_path,
            "r",
            encoding=encoding,
            errors="replace"
        ) as f:
            content = f.read()

        logger.info(
            f"Loaded trace file successfully: "
            f"{trace_path.name}"
        )

        return content

    except Exception as e:
        logger.error(
            f"Failed loading trace file "
            f"{trace_path}: {e}"
        )

        raise TraceLoaderError(
            f"Failed loading trace file: {trace_path}"
        )


def build_trace_metadata(
    trace_path: Path
) -> Dict:
    """
    Build trace metadata dictionary.

    Args:
        trace_path: Path to trace file

    Returns:
        Metadata dictionary
    """

    try:
        stat = trace_path.stat()

        metadata = {
            "filename": trace_path.name,
            "full_path": str(trace_path),
            "extension": trace_path.suffix.lower(),
            "size_bytes": stat.st_size,
            "created_at": stat.st_ctime,
            "modified_at": stat.st_mtime,
            "parent_dir": str(trace_path.parent),
        }

        logger.info(
            f"Built metadata for: {trace_path.name}"
        )

        return metadata

    except Exception as e:
        logger.error(
            f"Failed building metadata "
            f"for {trace_path}: {e}"
        )

        raise TraceLoaderError(
            f"Failed building metadata: {trace_path}"
        )


def load_all_traces(
    trace_dir: str,
    supported_extensions: List[str]
) -> List[Dict]:
    """
    Load all traces with metadata.

    Returns:
        [
            {
                "metadata": {...},
                "content": "..."
            }
        ]
    """

    traces = []

    trace_files = discover_trace_files(
        trace_dir,
        supported_extensions
    )

    for trace_file in trace_files:
        try:
            metadata = build_trace_metadata(
                trace_file
            )

            content = load_trace_file(
                trace_file
            )

            traces.append({
                "metadata": metadata,
                "content": content
            })

        except Exception as e:
            logger.error(
                f"Skipping trace file "
                f"{trace_file}: {e}"
            )

    logger.info(
        f"Loaded {len(traces)} traces successfully"
    )

    return traces
