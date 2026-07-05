#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from typing import Any

from globalroamer_ai.core.exceptions import RetryAdvisorError

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
    This service DOES NOT execute retries.
    It only provides operational recommendations.
    """

    def __init__(
        self,
        low_retry_success_threshold: float = 0.05,
        min_historical_matches: int = 3,
        cooldown_minutes: int = 30,
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
        chunk: dict[str, Any],
        similar_incidents: list[dict[str, Any]],
    ) -> dict[str, Any]:
        """
        Generate retry recommendation based on:
        - operational telecom signals
        - severity
        - historical similarity
        - retry/failure patterns
        """

        try:

            event_families = set(
                chunk.get("event_families", [])
            )

            causes = set(
                chunk.get("causes", [])
            )

            tags = set(
                chunk.get("tags", [])
            )

            has_failure = chunk.get(
                "has_failure",
                False,
            )

            has_high_severity = chunk.get(
                "has_high_severity",
                False,
            )

            similarity_scores = [
                incident.get("distance", 0)
                for incident in similar_incidents
                if incident.get("distance") is not None
            ]

            average_distance = (
                sum(similarity_scores) / len(similarity_scores)
                if similarity_scores else 0
            )

            recommendation = self._build_recommendation(
                event_families=event_families,
                causes=causes,
                tags=tags,
                has_failure=has_failure,
                has_high_severity=has_high_severity,
                similar_incidents=similar_incidents,
                average_distance=average_distance,
            )

            result = {
                "chunk_id": chunk.get("chunk_id"),
                "trace_id": chunk.get("trace_id"),
                "testcase_id": chunk.get("testcase_id"),

                "retry_decision": recommendation["decision"],
                "retry_reason": recommendation["reason"],
                "cooldown_minutes": recommendation["cooldown_minutes"],
                "risk_level": recommendation["risk_level"],

                "historical_match_count": len(
                    similar_incidents
                ),

                "average_distance": round(
                    average_distance,
                    6,
                ),

                "event_families": list(event_families),
                "causes": list(causes),
                "tags": list(tags),

                "has_failure": has_failure,
                "has_high_severity": has_high_severity,
            }

            logger.info(
                f"Retry recommendation generated "
                f"for chunk={chunk.get('chunk_id')} "
                f"decision={recommendation['decision']}"
            )

            return result

        except Exception as exc:

            logger.error(
                f"Retry analysis failed "
                f"for chunk={chunk.get('chunk_id')}: {exc}"
            )

            raise RetryAdvisorError(
                f"Retry analysis failed: {exc}"
            )

    def _build_recommendation(
        self,
        event_families: set[str],
        causes: set[str],
        tags: set[str],
        has_failure: bool,
        has_high_severity: bool,
        similar_incidents: list[dict[str, Any]],
        average_distance: float,
    ) -> dict[str, Any]:
        """
        Core retry recommendation logic.
        """

        historical_count = len(similar_incidents)

        # =================================================
        # CRITICAL / HIGH SEVERITY
        # =================================================

        if has_high_severity:

            return {
                "decision": "escalate",
                "reason": (
                    "High severity telecom failure detected. "
                    "Manual investigation recommended."
                ),
                "cooldown_minutes": None,
                "risk_level": "critical",
            }

        # =================================================
        # RETRY STORM / REPEATED FAILURES
        # =================================================

        if (
            historical_count >= self.min_historical_matches
            and average_distance <= 0.01
            and has_failure
        ):

            return {
                "decision": "do_not_retry",
                "reason": (
                    "Highly similar recurring telecom failure "
                    "pattern detected. "
                    "Retry probability appears low."
                ),
                "cooldown_minutes": None,
                "risk_level": "high",
            }

        # =================================================
        # NETWORK INSTABILITY
        # =================================================

        if (
            "timing" in event_families
            or "network_state" in event_families
            or "TIMEOUT" in causes
            or "RETRY" in causes
            or "timeout" in tags
        ):

            return {
                "decision": "retry_after_cooldown",
                "reason": (
                    "Possible transient telecom/network instability "
                    "detected."
                ),
                "cooldown_minutes": self.cooldown_minutes,
                "risk_level": "medium",
            }

        # =================================================
        # AUTH / REGISTRATION FAILURES
        # =================================================

        if (
            "authentication" in event_families
            or "registration" in event_families
            or "NAS_NOT_REGISTERED" in causes
            or "REJECT_SIGNAL" in tags
        ):

            return {
                "decision": "escalate",
                "reason": (
                    "Authentication/registration rejection likely "
                    "requires operator investigation."
                ),
                "cooldown_minutes": None,
                "risk_level": "high",
            }

        # =================================================
        # FAILURE DEFAULT
        # =================================================

        if has_failure:

            return {
                "decision": "retry",
                "reason": (
                    "Operational failure detected but no strong "
                    "evidence against retry."
                ),
                "cooldown_minutes": 5,
                "risk_level": "low",
            }

        # =================================================
        # HEALTHY / NORMAL EVENTS
        # =================================================

        return {
            "decision": "no_retry_needed",
            "reason": (
                "Chunk does not indicate retry-worthy failure."
            ),
            "cooldown_minutes": None,
            "risk_level": "none",
        }
