#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os
from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from globalroamer_ai.core.exceptions import AISummaryError

load_dotenv()

logger = logging.getLogger("ai_summary_service")


SYSTEM_PROMPT = """
You are an AI observability assistant for telecom roaming diagnostics.

Your task is to help engineers understand GlobalRoamer operational trace chunks.

Be concise, technical and operational.
Do not invent facts.
Use only the provided evidence.
If evidence is weak, say that confidence is limited.
Prefer deterministic observations over speculation.

Focus on:
- failure symptoms
- retry relevance
- network registration state
- mobility management signals
- timeout/reject/failure patterns
- similar historical incidents
- next checks for an engineer
"""


class AISummaryService:
    def __init__(self, model: str, max_input_chars: int = 12000):
        self.model = model
        self.max_input_chars = max_input_chars
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise AISummaryError("OPENAI_API_KEY is not configured")

        self.client = OpenAI(
            api_key=self.api_key,
            timeout=30,
            max_retries=2
        )
        logger.info(f"AISummaryService initialized with model={self.model}")

    def summarize_chunk(
            self,
            chunk: dict[str, Any],
            similar_incidents: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        similar_incidents = similar_incidents or []

        try:
            prompt = self._build_summary_prompt(chunk=chunk, similar_incidents=similar_incidents)

            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": prompt},
                ],
            )

            summary = response.choices[0].message.content.strip()

            result = {
                "chunk_id": chunk.get("chunk_id"),
                "trace_id": chunk.get("trace_id"),
                "testcase_id": chunk.get("testcase_id"),
                "summary": summary,
                "event_count": chunk.get("event_count"),
                "event_names": chunk.get("event_names", []),
                "event_families": chunk.get("event_families", []),
                "severities": chunk.get("severities", []),
                "causes": chunk.get("causes", []),
                "operators": chunk.get("operators", []),
                "countries": chunk.get("countries", []),
                "network_domains": chunk.get("network_domains", []),
                "has_failure": chunk.get("has_failure"),
                "has_high_severity": chunk.get("has_high_severity"),
                "has_retry_recommended": chunk.get("has_retry_recommended"),
                "similar_incident_count": len(similar_incidents),
            }

            logger.info(f"Generated AI summary for chunk={chunk.get('chunk_id')}")
            return result

        except Exception as exc:
            logger.error(f"Failed to summarize chunk {chunk.get('chunk_id')}: {exc}")
            raise AISummaryError(f"Failed to summarize chunk {chunk.get('chunk_id')}: {exc}")

    def summarize_many(
            self,
            chunks: list[dict[str, Any]],
            similarity_results_by_chunk: dict[str, list[dict[str, Any]]] | None = None,
            max_chunks: int | None = None
    ) -> list[dict[str, Any]]:
        similarity_results_by_chunk = similarity_results_by_chunk or {}
        selected_chunks = chunks[:max_chunks] if max_chunks else chunks
        summaries = []

        for chunk in selected_chunks:
            chunk_id = chunk.get("chunk_id")
            similar_incidents = similarity_results_by_chunk.get(chunk_id, [])
            summaries.append(self.summarize_chunk(chunk=chunk, similar_incidents=similar_incidents))

        logger.info(f"Generated {len(summaries)} AI summaries")
        return summaries

    def _build_summary_prompt(self, chunk: dict[str, Any], similar_incidents: list[dict[str, Any]]) -> str:
        chunk_text = self._safe_text(chunk.get("text", ""), self.max_input_chars)
        similar_text = self._format_similar_incidents(similar_incidents)

        payload = {
            "chunk_id": chunk.get("chunk_id"),
            "trace_id": chunk.get("trace_id"),
            "testcase_id": chunk.get("testcase_id"),
            "event_count": chunk.get("event_count"),
            "event_names": chunk.get("event_names", []),
            "event_families": chunk.get("event_families", []),
            "severities": chunk.get("severities", []),
            "causes": chunk.get("causes", []),
            "operators": chunk.get("operators", []),
            "countries": chunk.get("countries", []),
            "network_domains": chunk.get("network_domains", []),
            "tags": chunk.get("tags", []),
            "has_failure": chunk.get("has_failure"),
            "has_high_severity": chunk.get("has_high_severity"),
            "has_retry_recommended": chunk.get("has_retry_recommended"),
        }

        return f"""
Analyze this GlobalRoamer telecom operational chunk.

Chunk metadata:
{json.dumps(payload, indent=2, ensure_ascii=False, default=str)}

Chunk evidence:
{chunk_text}

Similar historical chunks:
{similar_text}

Return only this structure:

Operational summary:
- 

Failure indicators:
- 

Retry relevance:
- 

Similarity observations:
- 

Recommended next checks:
- 

Confidence:
- high / medium / low with short reason
""".strip()

    def _format_similar_incidents(self, similar_incidents: list[dict[str, Any]], max_items: int = 5) -> str:
        if not similar_incidents:
            return "No similar historical chunks provided."

        lines = []

        for index, item in enumerate(similar_incidents[:max_items], start=1):
            metadata = item.get("metadata", {})
            distance = item.get("distance")
            chunk_id = item.get("chunk_id") or metadata.get("chunk_id")

            lines.append(
                json.dumps(
                    {
                        "rank": index,
                        "chunk_id": chunk_id,
                        "distance": distance,
                        "event_names": metadata.get("event_names"),
                        "event_families": metadata.get("event_families"),
                        "causes": metadata.get("causes"),
                        "countries": metadata.get("countries"),
                        "operators": metadata.get("operators"),
                        "network_domains": metadata.get("network_domains"),
                        "has_failure": metadata.get("has_failure"),
                        "has_high_severity": metadata.get("has_high_severity"),
                        "has_retry_recommended": metadata.get("has_retry_recommended"),
                    },
                    ensure_ascii=False,
                    default=str,
                )
            )

        return "\n".join(lines)

    def _safe_text(self, value: Any, max_chars: int) -> str:
        text = str(value or "").strip()

        if len(text) <= max_chars:
            return text

        return text[:max_chars] + "\n...[truncated]"
