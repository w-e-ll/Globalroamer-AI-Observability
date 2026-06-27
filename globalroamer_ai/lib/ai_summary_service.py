#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging
import os

from typing import Dict, List

from dotenv import load_dotenv
from openai import OpenAI

from globalroamer_ai.lib.exceptions import AISummaryError

load_dotenv()

logger = logging.getLogger("ai_summary_service")


class AISummaryService:
    """
    LLM-based summary service for GlobalRoamer trace chunks.

    Purpose:
    - summarize noisy telecom traces
    - explain operational symptoms
    - highlight failure signals
    - make trace investigation faster for engineers
    """

    def __init__(self, model: str):
        self.model = model
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise AISummaryError(
                "OPENAI_API_KEY is not configured"
            )

        self.client = OpenAI(api_key=self.api_key)

        logger.info(
            f"AISummaryService initialized with model={self.model}"
        )

    def summarize_chunk(
        self,
        chunk: Dict,
        similar_incidents: List[Dict] = None
    ) -> Dict:
        """
        Generate AI summary for one trace chunk.
        """

        similar_incidents = similar_incidents or []

        try:
            prompt = build_summary_prompt(
                chunk=chunk,
                similar_incidents=similar_incidents
            )

            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.2,
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
                "summary": text,
                "input_signals": chunk.get("signals", []),
                "input_event_types": chunk.get("event_types", []),
                "similar_incident_count": len(similar_incidents),
            }

            logger.info(
                f"Generated AI summary for chunk={chunk.get('chunk_id')}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Failed to summarize chunk "
                f"{chunk.get('chunk_id')}: {e}"
            )

            raise AISummaryError(
                f"Failed to summarize chunk {chunk.get('chunk_id')}: {e}"
            )

    def summarize_many(
        self,
        chunks: List[Dict],
        similarity_results_by_chunk: Dict[str, List[Dict]] = None
    ) -> List[Dict]:
        """
        Generate AI summaries for multiple chunks.
        """

        similarity_results_by_chunk = similarity_results_by_chunk or {}

        summaries = []

        for chunk in chunks:
            similar_incidents = similarity_results_by_chunk.get(
                chunk.get("chunk_id"),
                []
            )

            summary = self.summarize_chunk(
                chunk=chunk,
                similar_incidents=similar_incidents
            )

            summaries.append(summary)

        logger.info(
            f"Generated {len(summaries)} AI summaries"
        )

        return summaries


SYSTEM_PROMPT = """
You are an AI observability assistant for telecom roaming diagnostics.

Your task is to help engineers understand noisy GlobalRoamer trace data.

Be concise, technical, and operational.
Do not invent facts.
If evidence is weak, say so.
Focus on:
- likely operational symptoms
- failure indicators
- affected workflow stage
- retry relevance
- similar historical patterns if provided
- what an engineer should inspect next
"""


def build_summary_prompt(
    chunk: Dict,
    similar_incidents: List[Dict]
) -> str:
    """
    Build prompt for LLM summary.
    """

    similar_text = format_similar_incidents(
        similar_incidents
    )

    return f"""
Analyze the following GlobalRoamer telecom trace chunk.

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

Return a compact operational summary with these sections:

1. What happened
2. Failure or anomaly indicators
3. Likely workflow stage
4. Similarity observations
5. Suggested next engineering checks
"""


def format_similar_incidents(
    similar_incidents: List[Dict],
    max_items: int = 5
) -> str:
    """
    Format similar incidents for prompt context.
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
            f"event_types={metadata.get('event_types')}"
        )

    return "\n".join(lines)
