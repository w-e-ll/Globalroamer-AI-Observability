#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from datetime import datetime, timezone
from typing import Dict, List, Optional

from globalroamer_ai.lib.exceptions import TraceNormalizationError

logger = logging.getLogger("trace_normalizer")


def normalize_parsed_trace(parsed_trace: Dict) -> Dict:
    """
    Convert parsed trace events into normalized operational events.

    Output is designed for:
    - chunking
    - embeddings
    - vector search
    - AI root-cause analysis
    - campaign health scoring
    """

    try:
        normalized_events = []

        for event in parsed_trace.get("events", []):
            normalized_event = normalize_event(event)

            if normalized_event:
                normalized_events.append(normalized_event)

        normalized = {
            "trace_id": parsed_trace.get("trace_id"),
            "metadata": parsed_trace.get("metadata", {}),
            "event_count": len(normalized_events),
            "signals_summary": build_signals_summary(normalized_events),
            "normalized_events": normalized_events,
        }

        logger.info(
            f"Normalized trace {normalized.get('trace_id')} "
            f"with {len(normalized_events)} events"
        )

        return normalized

    except Exception as e:
        logger.error(
            f"Failed to normalize trace "
            f"{parsed_trace.get('trace_id')}: {e}"
        )

        raise TraceNormalizationError(
            f"Failed to normalize trace: {parsed_trace.get('trace_id')}"
        )


def normalize_event(event: Dict) -> Optional[Dict]:
    """
    Normalize one parsed event into AI-friendly operational format.
    """

    raw = event.get("raw", "")
    event_name = normalize_event_name(event.get("event_name", "unknown"))
    timestamp_ms = event.get("timestamp")

    normalized = {
        "line_number": event.get("line_number"),
        "event_name": event_name,
        "event_type": classify_event_type(event_name, raw, event.get("signals", [])),
        "timestamp_ms": timestamp_ms,
        "timestamp_iso": timestamp_to_iso(timestamp_ms),
        "fields": normalize_fields(event.get("fields", {})),
        "signals": sorted(set(event.get("signals", []))),
        "severity": infer_severity(raw, event.get("signals", [])),
        "raw": raw,
    }

    return normalized


def normalize_event_name(event_name: str) -> str:
    """
    Normalize event name for grouping and matching.
    """

    if not event_name:
        return "unknown"

    return (
        event_name.strip()
        .replace('"', "")
        .replace("'", "")
        .replace(" ", "_")
        .lower()
    )


def normalize_fields(fields: Dict[str, str]) -> Dict[str, str]:
    """
    Normalize extracted fields.
    """

    normalized = {}

    for key, value in fields.items():
        if key is None:
            continue

        clean_key = (
            str(key)
            .strip()
            .replace(" ", "_")
            .lower()
        )

        clean_value = str(value).strip()

        normalized[clean_key] = clean_value

    return normalized


def timestamp_to_iso(timestamp_ms: Optional[int]) -> Optional[str]:
    """
    Convert timestamp in milliseconds to ISO UTC datetime.
    """

    if not timestamp_ms:
        return None

    try:
        # Some traces may contain seconds, not milliseconds.
        if timestamp_ms < 10_000_000_000:
            timestamp_s = timestamp_ms
        else:
            timestamp_s = timestamp_ms / 1000

        return datetime.fromtimestamp(
            timestamp_s,
            tz=timezone.utc
        ).isoformat()

    except Exception:
        return None


def classify_event_type(
    event_name: str,
    raw: str,
    signals: List[str]
) -> str:
    """
    Classify event into higher-level operational category.
    """

    text = f"{event_name} {raw}".lower()
    signal_set = set(signals or [])

    if {"failure", "error", "timeout", "reject"} & signal_set:
        return "failure_event"

    if {"attach", "registration", "authentication"} & signal_set:
        return "network_registration_event"

    if {"detach", "disconnect", "release"} & signal_set:
        return "session_teardown_event"

    if {"call", "volte"} & signal_set:
        return "voice_or_ims_event"

    if "sms" in signal_set:
        return "sms_event"

    if "paging" in signal_set:
        return "paging_event"

    if "retry" in signal_set:
        return "retry_event"

    if "sim" in text or "msisdn" in text or "imsi" in text:
        return "subscriber_identity_event"

    return "generic_trace_event"


def infer_severity(raw: str, signals: List[str]) -> str:
    """
    Infer operational severity from raw line and extracted signals.
    """

    lowered = raw.lower()
    signal_set = set(signals or [])

    if "fatal" in lowered or "critical" in lowered:
        return "critical"

    if {"failure", "error", "timeout", "reject", "abort"} & signal_set:
        return "error"

    if {"retry", "retransmission"} & signal_set:
        return "warning"

    return "info"


def build_signals_summary(events: List[Dict]) -> Dict[str, int]:
    """
    Count operational signals across normalized events.
    """

    summary = {}

    for event in events:
        for signal in event.get("signals", []):
            summary[signal] = summary.get(signal, 0) + 1

    return dict(sorted(summary.items()))
