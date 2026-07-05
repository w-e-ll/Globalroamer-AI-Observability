#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os

from typing import Any

from dotenv import load_dotenv
from openai import OpenAI

from globalroamer_ai.core.exceptions import RootCauseAnalysisError

load_dotenv()

logger = logging.getLogger("root_cause_service")


SYSTEM_PROMPT = """
You are an AI root-cause analysis assistant for telecom roaming diagnostics.

You help engineers investigate GlobalRoamer operational traces.

Rules:
- Do not invent facts.
- Treat your output as an engineering hypothesis, not a final truth.
- Use only evidence from the provided chunk and similar incidents.
- If evidence is weak, explicitly say confidence is low.
- Separate evidence from hypothesis.
- Prefer operationally useful explanations.
- Suggest what should be inspected next.
- Do not claim final root cause without enough evidence.

Focus on:
- Location Update failures
- PLMN not allowed
- registration denied
- NAS registered / not registered states
- PS attach / detach state
- PDP context activation / deactivation
- timeout and retry behavior
- operator / country / roaming configuration patterns
- transient vs persistent behavior
- escalation indicators
"""


class RootCauseService:
    def __init__(self, model: str, max_input_chars: int = 14000):
        self.model = model
        self.max_input_chars = max_input_chars
        self.api_key = os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            raise RootCauseAnalysisError("OPENAI_API_KEY is not configured")

        self.client = OpenAI(api_key=self.api_key)

        logger.info(f"RootCauseService initialized with model={self.model}")

    def analyze_chunk(
            self,
            chunk: dict[str, Any],
            similar_incidents: list[dict[str, Any]] | None = None
    ) -> dict[str, Any]:
        similar_incidents = similar_incidents or []

        try:
            prompt = self._build_root_cause_prompt(chunk=chunk, similar_incidents=similar_incidents)

            response = self.client.chat.completions.create(
                model=self.model,
                temperature=0.1,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT.strip()},
                    {"role": "user", "content": prompt},
                ],
            )

            text = response.choices[0].message.content.strip()

            result = {
                "chunk_id": chunk.get("chunk_id"),
                "trace_id": chunk.get("trace_id"),
                "testcase_id": chunk.get("testcase_id"),
                "root_cause_analysis": text,
                "event_names": chunk.get("event_names", []),
                "event_families": chunk.get("event_families", []),
                "causes": chunk.get("causes", []),
                "operators": chunk.get("operators", []),
                "countries": chunk.get("countries", []),
                "network_domains": chunk.get("network_domains", []),
                "severities": chunk.get("severities", []),
                "tags": chunk.get("tags", []),
                "similar_incident_count": len(similar_incidents),
            }

            logger.info(f"Generated root-cause analysis for chunk={chunk.get('chunk_id')}")

            return result

        except Exception as exc:
            logger.error(f"Failed root-cause analysis for chunk={chunk.get('chunk_id')}: {exc}")
            raise RootCauseAnalysisError(f"Failed root-cause analysis for chunk {chunk.get('chunk_id')}: {exc}")

    def analyze_many(
            self,
            chunks: list[dict[str, Any]],
            similarity_results_by_chunk: dict[str, list[dict[str, Any]]] | None = None
    ) -> list[dict[str, Any]]:
        similarity_results_by_chunk = similarity_results_by_chunk or {}
        reports = []

        for chunk in chunks:
            similar_incidents = similarity_results_by_chunk.get(chunk.get("chunk_id"), [])
            report = self.analyze_chunk(chunk=chunk, similar_incidents=similar_incidents)
            reports.append(report)

        logger.info(f"Generated {len(reports)} root-cause reports")

        return reports

    def _build_root_cause_prompt(self, chunk: dict[str, Any], similar_incidents: list[dict[str, Any]]) -> str:
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

Trace evidence:
{chunk_text}

Similar historical incidents:
{similar_text}

Return the analysis with these sections:

1. Probable root cause
2. Evidence from trace
3. Similar historical patterns
4. Confidence level: low / medium / high
5. What to inspect next
6. Retry recommendation: retry / wait / do not retry / escalate
""".strip()

    def _format_similar_incidents(self, similar_incidents: list[dict[str, Any]], max_items: int = 5) -> str:
        if not similar_incidents:
            return "No similar historical incidents provided."

        lines = []

        for index, item in enumerate(similar_incidents[:max_items], start=1):
            metadata = item.get("metadata", {})

            lines.append(
                json.dumps(
                    {
                        "rank": index,
                        "chunk_id": item.get("chunk_id"),
                        "distance": item.get("distance"),
                        "metadata": metadata,
                    },
                    ensure_ascii=False,
                    default=str,
                )
            )

        return "\n".join(lines)

    def _safe_text(self, value: Any, max_chars: int) -> str:
        text = str(value or "")
        if len(text) <= max_chars:
            return text
        return text[:max_chars] + "\n...[truncated]"
