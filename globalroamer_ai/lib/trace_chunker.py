#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
from typing import Dict, List

from globalroamer_ai.lib.exceptions import TraceChunkingError

logger = logging.getLogger("trace_chunker")


def chunk_normalized_trace(
    normalized_trace: Dict,
    chunk_size: int = 4000,
    chunk_overlap: int = 400
) -> List[Dict]:
    """
    Convert normalized trace events into AI-ready chunks.

    Important:
    We do not embed raw trace files directly.
    We first build logical operational chunks from normalized events.
    """

    try:
        trace_id = normalized_trace.get("trace_id")
        events = normalized_trace.get("normalized_events", [])

        chunks = []
        current_lines = []
        current_events = []
        current_size = 0
        chunk_index = 0

        for event in events:
            event_text = event_to_text(event)
            event_size = len(event_text)

            if current_size + event_size > chunk_size and current_lines:
                chunk = build_chunk(
                    trace_id=trace_id,
                    chunk_index=chunk_index,
                    lines=current_lines,
                    events=current_events,
                    normalized_trace=normalized_trace,
                )
                chunks.append(chunk)
                chunk_index += 1

                overlap_lines = build_overlap_lines(
                    current_lines,
                    chunk_overlap
                )
                overlap_events = current_events[-max(1, len(current_events) // 10):]

                current_lines = overlap_lines
                current_events = overlap_events
                current_size = sum(len(line) for line in current_lines)

            current_lines.append(event_text)
            current_events.append(event)
            current_size += event_size

        if current_lines:
            chunk = build_chunk(
                trace_id=trace_id,
                chunk_index=chunk_index,
                lines=current_lines,
                events=current_events,
                normalized_trace=normalized_trace,
            )
            chunks.append(chunk)

        logger.info(
            f"Created {len(chunks)} chunks "
            f"for trace {trace_id}"
        )

        return chunks

    except Exception as e:
        logger.error(
            f"Failed to chunk trace "
            f"{normalized_trace.get('trace_id')}: {e}"
        )

        raise TraceChunkingError(
            f"Failed to chunk trace: {normalized_trace.get('trace_id')}"
        )


def event_to_text(event: Dict) -> str:
    """
    Convert normalized event into compact text for embeddings.
    """

    fields = event.get("fields", {})
    signals = event.get("signals", [])

    field_text = ", ".join(
        f"{key}={value}" for key, value in fields.items()
    )

    signal_text = ", ".join(signals)

    return (
        f"line={event.get('line_number')} | "
        f"type={event.get('event_type')} | "
        f"name={event.get('event_name')} | "
        f"severity={event.get('severity')} | "
        f"timestamp={event.get('timestamp_iso')} | "
        f"signals=[{signal_text}] | "
        f"fields=[{field_text}] | "
        f"raw={event.get('raw')}"
    )


def build_chunk(
    trace_id: str,
    chunk_index: int,
    lines: List[str],
    events: List[Dict],
    normalized_trace: Dict,
) -> Dict:
    """
    Build chunk object with text and metadata.
    """

    chunk_text = "\n".join(lines)

    event_types = sorted(
        set(event.get("event_type") for event in events if event.get("event_type"))
    )

    signals = sorted(
        set(
            signal
            for event in events
            for signal in event.get("signals", [])
        )
    )

    severities = sorted(
        set(event.get("severity") for event in events if event.get("severity"))
    )

    metadata = normalized_trace.get("metadata", {})

    return {
        "chunk_id": f"{trace_id}::chunk_{chunk_index}",
        "trace_id": trace_id,
        "chunk_index": chunk_index,
        "text": chunk_text,
        "event_count": len(events),
        "event_types": event_types,
        "signals": signals,
        "severities": severities,
        "source_file": metadata.get("filename"),
        "source_path": metadata.get("full_path"),
    }


def build_overlap_lines(
    lines: List[str],
    overlap_chars: int
) -> List[str]:
    """
    Keep approximate character overlap between chunks.
    """

    if overlap_chars <= 0:
        return []

    overlap = []
    total = 0

    for line in reversed(lines):
        overlap.insert(0, line)
        total += len(line)

        if total >= overlap_chars:
            break

    return overlap
