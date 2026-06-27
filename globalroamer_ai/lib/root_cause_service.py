#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from globalroamer_ai.lib.exceptions import RootCauseAnalysisError

load_dotenv()

logger = logging.getLogger("root_cause_service")


class RootCauseService:
    """
    LLM-based root-cause analysis service for GlobalRoamer traces.

    Purpose:
    - inspect normalized trace chunks
    - correlate operational signals
    - use similar historical incidents as context
    - suggest probable root cause without replacing engineer judgement
    """

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise RootCauseAnalysisError(
                "OPENAI_API_KEY is not configured"
            )

        self.client = OpenAI(api_key=self.api_key)

        logger.info(
            f"RootCauseService initialized with model={self.model}"
        )

    def analyze_chunk(
        self,
        chunk: Dict,
        similar_incidents: List[Dict] = None
    ) -> Dict:
        """
        Generate probable root-cause analysis for one trace chunk.
        """

        similar_incidents = similar_incidents or []

        try:
            prompt = build_root_cause_prompt(
                chunk=chunk,
                similar_incidents=similar_incidents
            )

            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {
                        "role": "system",
                        "content": SYSTEM_PROMPT
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )

            text = response.choices[0].message.content.strip()

            result = {
                "chunk_id": chunk.get("chunk_id"),
                "trace_id": chunk.get("trace_id"),
                "source_file": chunk.get("source_file"),
                "root_cause_analysis": text,
                "input_signals": chunk.get("signals", []),
                "input_event_types": chunk.get("event_types", []),
                "similar_incident_count": len(similar_incidents),
            }

            logger.info(
                f"Generated root-cause analysis "
                f"for chunk={chunk.get('chunk_id')}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed root-cause analysis for "
                f"chunk={chunk.get('chunk_id')}: {e}"
            )

            raise RootCauseAnalysisError(
                f"Failed root-cause analysis "
                f"for chunk {chunk.get('chunk_id')}: {e}"
            )

    def analyze_many(
        self,
        chunks: List[Dict],
        similarity_results_by_chunk: Dict[str, List[Dict]] = None
    ) -> List[Dict]:
        """
        Generate root-cause analysis for multiple chunks.
        """

        similarity_results_by_chunk = similarity_results_by_chunk or {}

        reports = []

        for chunk in chunks:
            similar_incidents = similarity_results_by_chunk.get(
                chunk.get("chunk_id"),
                []
            )

            report = self.analyze_chunk(
                chunk=chunk,
                similar_incidents=similar_incidents
            )

            reports.append(report)

        logger.info(
            f"Generated {len(reports)} root-cause reports"
        )

        return reports


SYSTEM_PROMPT = """
You are an AI root-cause analysis assistant for telecom roaming diagnostics.

You help engineers investigate GlobalRoamer test traces.

Rules:
- Do not invent facts.
- Treat your output as an engineering hypothesis, not a final truth.
- Use only evidence from the trace chunk and provided similar incidents.
- If evidence is weak, explicitly say that confidence is low.
- Prefer operationally useful explanations over generic statements.
- Separate evidence from hypothesis.
- Suggest what should be inspected next.

Focus on:
- LTE attach / detach behavior
- IMS registration / deregistration
- authentication / authorization failures
- paging / call setup / call release
- SMS / VoLTE execution stages
- retries / repeated failures
- timing anomalies
- operator or SIM-related instability
"""


def build_root_cause_prompt(
    chunk: Dict,
    similar_incidents: List[Dict]
) -> str:
    """
    Build root-cause analysis prompt.
    """

    similar_text = format_similar_incidents(
        similar_incidents
    )

    return f"""
Analyze this GlobalRoamer telecom trace chunk and produce a probable root-cause hypothesis.

Trace metadata:
- chunk_id: {chunk.get("chunk_id")}
- trace_id: {chunk.get("trace_id")}
- source_file: {chunk.get("source_file")}
- event_types: {chunk.get("event_types")}
- signals: {chunk.get("signals")}
- severities: {chunk.get("severities")}
- event_count: {chunk.get("event_count")}

Trace chunk:
{chunk.get("text")}

Similar historical incidents:
{similar_text}

Return the analysis with these sections:

1. Probable root cause
2. Evidence from trace
3. Similar historical patterns
4. Confidence level: low / medium / high
5. What to inspect next
6. Retry recommendation: retry / wait / do not retry / escalate
"""


def format_similar_incidents(
    similar_incidents: List[Dict],
    max_items: int = 5
) -> str:
    """
    Format similar incidents for root-cause prompt.
    """

    if not similar_incidents:
        return "No similar historical incidents provided."

    lines = []

    for item in similar_incidents[:max_items]:
        metadata = item.get("metadata", {})

        lines.append(
            f"- rank={item.get('rank')}, "
            f"score={item.get('similarity_score')}, "
            f"chunk_id={item.get('chunk_id')}, "
            f"source_file={metadata.get('source_file')}, "
            f"signals={metadata.get('signals')}, "
            f"event_types={metadata.get('event_types')}, "
            f"severities={metadata.get('severities')}"
        )

    return "\n".join(lines)
