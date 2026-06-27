#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import re

from typing import Dict, List, Optional

from globalroamer_ai.lib.exceptions import TraceParserError

logger = logging.getLogger("trace_parser")


def parse_trace_content(
    content: str,
    metadata: Optional[Dict] = None
) -> Dict:
    """
    Parse raw GlobalRoamer trace content into structured events.

    The goal is not to fully understand every telecom protocol field,
    but to extract enough operational signals for AI observability:
    - event names
    - raw lines
    - timestamps if available
    - key/value fields
    - error/failure indicators
    """

    metadata = metadata or {}

    try:
        lines = content.splitlines()

        events = []

        for line_number, raw_line in enumerate(lines, start=1):
            line = raw_line.strip()

            if not line:
                continue

            event = parse_trace_line(line, line_number)

            if event:
                events.append(event)

        parsed = {
            "trace_id": metadata.get("filename"),
            "metadata": metadata,
            "event_count": len(events),
            "events": events,
        }

        logger.info(
            f"Parsed trace {metadata.get('filename')} "
            f"with {len(events)} events"
        )

        return parsed

    except Exception as e:
        logger.error(
            f"Failed to parse trace "
            f"{metadata.get('filename')}: {e}"
        )

        raise TraceParserError(
            f"Failed to parse trace: {metadata.get('filename')}"
        )


def parse_trace_line(
    line: str,
    line_number: int
) -> Optional[Dict]:
    """
    Parse a single trace line.

    Supports common GlobalRoamer trace styles:
    - Key; value
    - Key = value
    - EventName: timestamp/value
    - noisy protocol log lines
    """

    try:
        event = {
            "line_number": line_number,
            "raw": line,
            "event_name": extract_event_name(line),
            "timestamp": extract_timestamp(line),
            "fields": extract_key_values(line),
            "signals": extract_operational_signals(line),
        }

        return event

    except Exception as e:
        logger.warning(
            f"Failed to parse line {line_number}: {e}"
        )
        return None


def extract_event_name(line: str) -> str:
    """
    Extract best-effort event name from trace line.
    """

    # Example: CallSetup: 1731932299000
    colon_match = re.match(r"^([A-Za-z0-9_.\-]+)\s*:", line)
    if colon_match:
        return colon_match.group(1)

    # Example: CallRelease; DATETIME=...
    semicolon_match = re.match(r"^([A-Za-z0-9_.\-]+)\s*;", line)
    if semicolon_match:
        return semicolon_match.group(1)

    # Example: SomeKey = SomeValue
    equals_match = re.match(r"^([A-Za-z0-9_.\-]+)\s*=", line)
    if equals_match:
        return equals_match.group(1)

    # Fallback: first token
    return line.split()[0][:80] if line.split() else "unknown"


def extract_timestamp(line: str) -> Optional[int]:
    """
    Extract timestamp in milliseconds if present.

    Supports:
    - 1731932299000
    - DATETIME=1731932299000
    - DATETIME(1731932299000)
    """

    patterns = [
        r"DATETIME\s*=\s*(\d{10,16})",
        r"DATETIME\((\d{10,16})\)",
        r":\s*\"?(\d{10,16})",
        r":\s*(\d{10,16})",
    ]

    for pattern in patterns:
        match = re.search(pattern, line)
        if match:
            try:
                return int(match.group(1))
            except ValueError:
                return None

    return None


def extract_key_values(line: str) -> Dict[str, str]:
    """
    Extract simple key/value pairs from line.
    """

    fields = {}

    # Pattern: key=value
    for key, value in re.findall(
        r"([A-Za-z0-9_.\-]+)\s*=\s*([^;,\s]+)",
        line
    ):
        fields[key] = clean_value(value)

    # Pattern: Key; value
    semicolon_match = re.match(
        r"^([A-Za-z0-9_.\-]+)\s*;\s*(.+)$",
        line
    )
    if semicolon_match:
        fields[semicolon_match.group(1)] = clean_value(
            semicolon_match.group(2)
        )

    # Pattern: Key: value
    colon_match = re.match(
        r"^([A-Za-z0-9_.\-]+)\s*:\s*(.+)$",
        line
    )
    if colon_match:
        fields[colon_match.group(1)] = clean_value(
            colon_match.group(2)
        )

    return fields


def clean_value(value: str) -> str:
    """
    Normalize extracted field value.
    """

    return (
        value
        .strip()
        .strip("'")
        .strip('"')
        .strip()
    )


def extract_operational_signals(line: str) -> List[str]:
    """
    Extract operational signals useful for AI diagnostics.
    """

    lowered = line.lower()
    signals = []

    signal_patterns = {
        "failure": ["fail", "failed", "failure"],
        "error": ["error", "exception"],
        "timeout": ["timeout", "timed out"],
        "retry": ["retry", "retransmission"],
        "abort": ["abort", "aborted"],
        "detach": ["detach", "detached"],
        "attach": ["attach", "attached"],
        "registration": ["registration", "register"],
        "authentication": ["auth", "authentication"],
        "paging": ["paging"],
        "reject": ["reject", "rejected"],
        "disconnect": ["disconnect", "disconnected"],
        "release": ["release", "released"],
        "handover": ["handover"],
        "sms": ["sms"],
        "call": ["call", "voice"],
        "volte": ["volte", "ims"],
    }

    for signal, keywords in signal_patterns.items():
        if any(keyword in lowered for keyword in keywords):
            signals.append(signal)

    return signals
