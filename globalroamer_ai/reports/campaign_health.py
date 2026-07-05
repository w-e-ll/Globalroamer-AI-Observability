#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from collections import Counter
from typing import Any

from globalroamer_ai.core.exceptions import CampaignHealthError

logger = logging.getLogger("campaign_health")


class CampaignHealthScorer:
    """
    Campaign-level operational health scoring.

    Purpose:
    - aggregate operational trace chunks
    - detect degraded campaigns
    - summarize dominant failure patterns
    - provide observability-oriented operational scoring
    """

    def __init__(
        self,
        degraded_threshold: float = 0.75,
        critical_threshold: float = 0.50,
    ):
        self.degraded_threshold = degraded_threshold
        self.critical_threshold = critical_threshold

        logger.info(
            "CampaignHealthScorer initialized: "
            f"degraded_threshold={self.degraded_threshold}, "
            f"critical_threshold={self.critical_threshold}"
        )

    def score_campaign(
        self,
        chunks: list[dict[str, Any]],
        retry_reports: list[dict[str, Any]] | None = None,
        root_cause_reports: list[dict[str, Any]] | None = None,
    ) -> dict[str, Any]:
        """
        Calculate campaign health from operational chunks.
        """

        retry_reports = retry_reports or []
        root_cause_reports = root_cause_reports or []

        try:
            if not chunks:
                raise CampaignHealthError(
                    "Cannot score campaign without chunks"
                )

            total_chunks = len(chunks)

            event_family_counter = Counter()
            severity_counter = Counter()
            event_name_counter = Counter()
            cause_counter = Counter()
            operator_counter = Counter()
            country_counter = Counter()
            domain_counter = Counter()
            tag_counter = Counter()

            failure_chunks = 0
            retry_chunks = 0
            high_severity_chunks = 0

            trace_ids = set()
            testcase_ids = set()

            for chunk in chunks:
                event_family_counter.update(
                    chunk.get("event_families", [])
                )

                severity_counter.update(
                    chunk.get("severities", [])
                )

                event_name_counter.update(
                    chunk.get("event_names", [])
                )

                cause_counter.update(
                    chunk.get("causes", [])
                )

                operator_counter.update(
                    chunk.get("operators", [])
                )

                country_counter.update(
                    chunk.get("countries", [])
                )

                domain_counter.update(
                    chunk.get("network_domains", [])
                )

                tag_counter.update(
                    chunk.get("tags", [])
                )

                if chunk.get("has_failure"):
                    failure_chunks += 1

                if chunk.get("has_retry_recommended"):
                    retry_chunks += 1

                if chunk.get("has_high_severity"):
                    high_severity_chunks += 1

                if chunk.get("trace_id"):
                    trace_ids.add(chunk.get("trace_id"))

                if chunk.get("testcase_id"):
                    testcase_ids.add(chunk.get("testcase_id"))

            penalty = (
                failure_chunks * 0.20
                + retry_chunks * 0.10
                + high_severity_chunks * 0.30
                + severity_counter.get("critical", 0) * 0.20
                + event_family_counter.get("timing", 0) * 0.05
                + event_family_counter.get("network_state", 0) * 0.05
            )

            normalized_penalty = min(
                penalty / max(total_chunks, 1),
                1.0,
            )

            health_score = round(
                max(0.0, 1.0 - normalized_penalty),
                4,
            )

            status = self._classify_health(
                health_score
            )

            retry_decision_counter = Counter(
                report.get("retry_recommendation")
                for report in retry_reports
                if report.get("retry_recommendation")
            )

            result = {
                "campaign_health_score": health_score,
                "campaign_status": status,
                "total_chunks": total_chunks,
                "unique_trace_count": len(trace_ids),
                "unique_testcase_count": len(testcase_ids),

                "failure_chunk_count": failure_chunks,
                "retry_chunk_count": retry_chunks,
                "high_severity_chunk_count": high_severity_chunks,

                "dominant_event_families": event_family_counter.most_common(10),
                "dominant_event_names": event_name_counter.most_common(10),
                "dominant_causes": cause_counter.most_common(10),
                "dominant_operators": operator_counter.most_common(10),
                "dominant_countries": country_counter.most_common(10),
                "dominant_network_domains": domain_counter.most_common(10),
                "dominant_tags": tag_counter.most_common(20),

                "severity_distribution": dict(severity_counter),
                "retry_decision_distribution": dict(retry_decision_counter),

                "main_issue_cluster": self._infer_main_issue_cluster(
                    event_family_counter=event_family_counter,
                    event_name_counter=event_name_counter,
                    cause_counter=cause_counter,
                    severity_counter=severity_counter,
                ),

                "recommended_action": self._recommend_action(
                    health_status=status,
                    retry_decision_counter=retry_decision_counter,
                    cause_counter=cause_counter,
                    event_family_counter=event_family_counter,
                ),

                "root_cause_report_count": len(root_cause_reports),
            }

            logger.info(
                f"Campaign health calculated: "
                f"score={health_score}, status={status}"
            )

            return result

        except CampaignHealthError:
            raise

        except Exception as exc:
            logger.error(
                f"Failed to score campaign health: {exc}"
            )

            raise CampaignHealthError(
                f"Failed to score campaign health: {exc}"
            )

    def _classify_health(
        self,
        health_score: float,
    ) -> str:
        """
        Convert numeric health score into operational status.
        """

        if health_score < self.critical_threshold:
            return "CRITICAL"

        if health_score < self.degraded_threshold:
            return "DEGRADED"

        return "HEALTHY"

    @staticmethod
    def _infer_main_issue_cluster(
        event_family_counter: Counter,
        event_name_counter: Counter,
        cause_counter: Counter,
        severity_counter: Counter,
    ) -> str:
        """
        Infer dominant operational issue cluster.
        """

        if (
            cause_counter.get("PLMN_NOT_ALLOWED", 0)
            or event_name_counter.get("REJECT_SIGNAL", 0)
        ):
            return "Roaming registration rejection pattern"

        if (
            cause_counter.get("TIMEOUT", 0)
            or event_family_counter.get("timing", 0)
        ):
            return "Timeout / instability pattern"

        if (
            event_name_counter.get("NAS_NOT_REGISTERED", 0)
            or event_name_counter.get("DETACHED", 0)
        ):
            return "Registration instability pattern"

        if (
            event_family_counter.get("failure", 0)
            and severity_counter.get("critical", 0)
        ):
            return "Critical failure-heavy operational pattern"

        if event_family_counter.get("retry", 0):
            return "Transient retry-heavy pattern"

        return "No dominant operational issue cluster detected"

    @staticmethod
    def _recommend_action(
        health_status: str,
        retry_decision_counter: Counter,
        cause_counter: Counter,
        event_family_counter: Counter,
    ) -> str:
        """
        Produce operational recommendation.
        """

        if health_status == "CRITICAL":
            return (
                "Stop automated retries and escalate "
                "for manual telecom investigation."
            )

        if retry_decision_counter.get("do_not_retry", 0):
            return (
                "Avoid repeated retries for identical "
                "failure clusters."
            )

        if retry_decision_counter.get("retry_after_cooldown", 0):
            return (
                "Retry after cooldown and monitor "
                "whether instability persists."
            )

        if (
            cause_counter.get("PLMN_NOT_ALLOWED", 0)
            or event_family_counter.get("network_state", 0)
        ):
            return (
                "Escalate to roaming/operator validation "
                "before re-running campaign."
            )

        if health_status == "DEGRADED":
            return (
                "Continue monitoring and retry only "
                "selected transient failures."
            )

        return (
            "No immediate operational action required."
        )
