#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from typing import Dict, List

from globalroamer_ai.lib.exceptions import RetryAdvisorError

logger = logging.getLogger("retry_advisor")


class RetryAdvisor:
    """
    AI-assisted retry intelligence service.

    Purpose:
    - reduce useless retries
    - identify retry storms
    - recommend escalation
    - detect unstable operator patterns
    - estimate retry recovery probability

    Important:
    This service does NOT execute retries.
    It only provides operational recommendations.
    """

    def __init__(
        self,
        low_retry_success_threshold: float = 0.05,
        min_historical_matches: int = 3,
        cooldown_minutes: int = 30
    ):
        self.low_retry_success_threshold = (
            low_retry_success_threshold
        )

        self.min_historical_matches = (
            min_historical_matches
        )

        self.cooldown_minutes = cooldown_minutes

        logger.info(
            "RetryAdvisor initialized: "
            f"low_retry_success_threshold="
            f"{self.low_retry_success_threshold}, "
            f"min_historical_matches="
            f"{self.min_historical_matches}, "
            f"cooldown_minutes="
            f"{self.cooldown_minutes}"
        )

    def analyze_retry_strategy(
        self,
        chunk: Dict,
        similar_incidents: List[Dict]
    ) -> Dict:
        """
        Generate retry recommendation based on:
        - operational signals
        - severity
        - historical similarity
        - observed retry patterns
        """

        try:
            signals = set(
                chunk.get("signals", [])
            )

            severities = set(
                chunk.get("severities", [])
            )

            event_types = set(
                chunk.get("event_types", [])
            )

            similarity_scores = [
                incident.get("similarity_score", 0)
                for incident in similar_incidents
                if incident.get("similarity_score") is not None
            ]

            average_similarity = (
                sum(similarity_scores) / len(similarity_scores)
                if similarity_scores else 0
            )

            recommendation = self._build_recommendation(
                signals=signals,
                severities=severities,
                event_types=event_types,
                similar_incidents=similar_incidents,
                average_similarity=average_similarity
            )

            result = {
                "chunk_id": chunk.get("chunk_id"),
                "trace_id": chunk.get("trace_id"),
                "source_file": chunk.get("source_file"),

                "retry_decision": recommendation["decision"],
                "retry_reason": recommendation["reason"],
                "cooldown_minutes": recommendation["cooldown_minutes"],

                "risk_level": recommendation["risk_level"],

                "historical_match_count": len(similar_incidents),
                "average_similarity": round(
                    average_similarity,
                    4
                ),

                "signals": list(signals),
                "event_types": list(event_types),
            }

            logger.info(
                f"Retry recommendation generated "
                f"for chunk={chunk.get('chunk_id')} "
                f"decision={recommendation['decision']}"
            )

            return result

        except Exception as e:
            logger.error(
                f"Retry analysis failed "
                f"for chunk={chunk.get('chunk_id')}: {e}"
            )

            raise RetryAdvisorError(
                f"Retry analysis failed: {e}"
            )

    def _build_recommendation(
        self,
        signals: set,
        severities: set,
        event_types: set,
        similar_incidents: List[Dict],
        average_similarity: float
    ) -> Dict:
        """
        Core retry decision logic.
        """

        historical_count = len(similar_incidents)

        # -------------------------------------------------
        # Critical failures
        # -------------------------------------------------

        if "critical" in severities:
            return {
                "decision": "escalate",
                "reason": (
                    "Critical severity detected. "
                    "Manual investigation recommended."
                ),
                "cooldown_minutes": None,
                "risk_level": "critical"
            }

        # -------------------------------------------------
        # Retry storm / repeated failures
        # -------------------------------------------------

        if (
            historical_count >= self.min_historical_matches
            and average_similarity >= 0.90
            and (
                "failure" in signals
                or "timeout" in signals
            )
        ):
            return {
                "decision": "do_not_retry",
                "reason": (
                    "Highly similar recurring historical "
                    "failure pattern detected. "
                    "Low probability of successful retry."
                ),
                "cooldown_minutes": None,
                "risk_level": "high"
            }

        # -------------------------------------------------
        # Network instability
        # -------------------------------------------------

        if (
            "timeout" in signals
            or "paging" in signals
            or "registration" in signals
        ):
            return {
                "decision": "retry_after_cooldown",
                "reason": (
                    "Possible transient telecom/network instability."
                ),
                "cooldown_minutes": self.cooldown_minutes,
                "risk_level": "medium"
            }

        # -------------------------------------------------
        # Authentication issues
        # -------------------------------------------------

        if (
            "authentication" in signals
            or "reject" in signals
        ):
            return {
                "decision": "escalate",
                "reason": (
                    "Authentication or registration rejection "
                    "likely requires operator investigation."
                ),
                "cooldown_minutes": None,
                "risk_level": "high"
            }

        # -------------------------------------------------
        # Generic retry
        # -------------------------------------------------

        return {
            "decision": "retry",
            "reason": (
                "No strong evidence against retry."
            ),
            "cooldown_minutes": 5,
            "risk_level": "low"
        }
