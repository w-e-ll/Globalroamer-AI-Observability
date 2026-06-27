#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import logging

from collections import Counter, defaultdict
from typing import Dict, List

from globalroamer_ai.lib.exceptions import CampaignHealthError

logger = logging.getLogger("campaign_health")


class CampaignHealthScorer:
    """
    Campaign-level operational health scoring.

    Purpose:
    - aggregate trace chunk signals
    - detect degraded campaigns
    - summarize dominant failure patterns
    - provide high-level monitoring output

    This service does not replace deterministic campaign status.
    It adds an AI/observability-style health layer.
    """

    def __init__(
        self,
        degraded_threshold: float = 0.75,
        critical_threshold: float = 0.50
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
        chunks: List[Dict],
        retry_reports: List[Dict] = None,
        root_cause_reports: List[Dict] = None
    ) -> Dict:
        """
        Calculate campaign health from chunk-level outputs.
        """

        retry_reports = retry_reports or []
        root_cause_reports = root_cause_reports or []

        try:
            if not chunks:
                raise CampaignHealthError(
                    "Cannot score campaign without chunks"
                )

            total_chunks = len(chunks)

            signal_counter = Counter()
            severity_counter = Counter()
            event_type_counter = Counter()
            source_files = set()

            for chunk in chunks:
                signal_counter.update(chunk.get("signals", []))
                severity_counter.update(chunk.get("severities", []))
                event_type_counter.update(chunk.get("event_types", []))

                if chunk.get("source_file"):
                    source_files.add(chunk.get("source_file"))

            error_weight = (
                severity_counter.get("error", 0) * 0.20
                + severity_counter.get("critical", 0) * 0.40
                + signal_counter.get("failure", 0) * 0.15
                + signal_counter.get("timeout", 0) * 0.10
                + signal_counter.get("reject", 0) * 0.10
                + signal_counter.get("abort", 0) * 0.10
            )

            normalized_penalty = min(
                error_weight / max(total_chunks, 1),
                1.0
            )

            health_score = round(
                max(0.0, 1.0 - normalized_penalty),
                4
            )

            status = self._classify_health(
                health_score
            )

            retry_decision_counter = Counter(
                report.get("retry_decision")
                for report in retry_reports
                if report.get("retry_decision")
            )

            result = {
                "campaign_health_score": health_score,
                "campaign_status": status,

                "total_chunks": total_chunks,
                "source_file_count": len(source_files),

                "dominant_signals": signal_counter.most_common(10),
                "dominant_event_types": event_type_counter.most_common(10),
                "severity_distribution": dict(severity_counter),

                "retry_decision_distribution": dict(retry_decision_counter),

                "main_issue_cluster": self._infer_main_issue_cluster(
                    signal_counter=signal_counter,
                    event_type_counter=event_type_counter,
                    severity_counter=severity_counter
                ),

                "recommended_action": self._recommend_action(
                    health_status=status,
                    retry_decision_counter=retry_decision_counter,
                    signal_counter=signal_counter
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

        except Exception as e:
            logger.error(
                f"Failed to score campaign health: {e}"
            )

            raise CampaignHealthError(
                f"Failed to score campaign health: {e}"
            )

    def _classify_health(
        self,
        health_score: float
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
        signal_counter: Counter,
        event_type_counter: Counter,
        severity_counter: Counter
    ) -> str:
        """
        Infer campaign-level issue cluster from dominant signals.
        """

        if signal_counter.get("authentication", 0) or signal_counter.get("reject", 0):
            return "Authentication / registration rejection pattern"

        if signal_counter.get("timeout", 0):
            return "Timeout / network instability pattern"

        if signal_counter.get("paging", 0):
            return "Paging / call setup instability pattern"

        if signal_counter.get("detach", 0) or signal_counter.get("disconnect", 0):
            return "Detach / session teardown instability pattern"

        if event_type_counter.get("voice_or_ims_event", 0):
            return "Voice / IMS workflow anomaly pattern"

        if severity_counter.get("error", 0) or severity_counter.get("critical", 0):
            return "Generic failure-heavy campaign pattern"

        return "No dominant failure cluster detected"

    @staticmethod
    def _recommend_action(
        health_status: str,
        retry_decision_counter: Counter,
        signal_counter: Counter
    ) -> str:
        """
        Produce campaign-level operational recommendation.
        """

        if health_status == "CRITICAL":
            return "Stop automatic retries and escalate for manual investigation."

        if retry_decision_counter.get("do_not_retry", 0) > 0:
            return "Avoid further retries for matching failure clusters and escalate."

        if retry_decision_counter.get("retry_after_cooldown", 0) > 0:
            return "Retry after cooldown and monitor whether the same pattern repeats."

        if signal_counter.get("authentication", 0) or signal_counter.get("reject", 0):
            return "Escalate to roaming/operator investigation before repeating tests."

        if health_status == "DEGRADED":
            return "Continue monitoring and retry only selected tests with clear transient symptoms."

        return "No immediate action required beyond normal monitoring."
