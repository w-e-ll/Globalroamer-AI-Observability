#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os

from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

from globalroamer_ai.lib.exceptions import ReportGenerationError

logger = logging.getLogger("report_writer")


class ReportWriter:
    """
    Writes GlobalRoamer AI observability outputs.

    Supported outputs:
    - JSON reports for machine processing
    - Markdown reports for human review
    """

    def __init__(
        self,
        ai_summary_dir: str,
        root_cause_dir: str,
        campaign_health_dir: str
    ):
        self.ai_summary_dir = ai_summary_dir
        self.root_cause_dir = root_cause_dir
        self.campaign_health_dir = campaign_health_dir

        self._ensure_directories()

        logger.info("ReportWriter initialized")

    def write_ai_summaries(
        self,
        summaries: List[Dict],
        report_name: str = "ai_summaries"
    ) -> Dict[str, str]:
        """
        Write AI summaries to JSON and Markdown.
        """

        try:
            json_path = Path(self.ai_summary_dir) / f"{report_name}.json"
            md_path = Path(self.ai_summary_dir) / f"{report_name}.md"

            write_json(json_path, summaries)
            write_text(md_path, render_ai_summaries_markdown(summaries))

            logger.info(
                f"Wrote AI summaries: {json_path}, {md_path}"
            )

            return {
                "json": str(json_path),
                "markdown": str(md_path)
            }

        except Exception as e:
            logger.error(
                f"Failed writing AI summaries: {e}"
            )

            raise ReportGenerationError(
                f"Failed writing AI summaries: {e}"
            )

    def write_root_cause_reports(
        self,
        reports: List[Dict],
        report_name: str = "root_cause_reports"
    ) -> Dict[str, str]:
        """
        Write root-cause reports to JSON and Markdown.
        """

        try:
            json_path = Path(self.root_cause_dir) / f"{report_name}.json"
            md_path = Path(self.root_cause_dir) / f"{report_name}.md"

            write_json(json_path, reports)
            write_text(md_path, render_root_cause_markdown(reports))

            logger.info(
                f"Wrote root-cause reports: {json_path}, {md_path}"
            )

            return {
                "json": str(json_path),
                "markdown": str(md_path)
            }

        except Exception as e:
            logger.error(
                f"Failed writing root-cause reports: {e}"
            )

            raise ReportGenerationError(
                f"Failed writing root-cause reports: {e}"
            )

    def write_campaign_health(
        self,
        health_report: Dict,
        report_name: str = "campaign_health"
    ) -> Dict[str, str]:
        """
        Write campaign health report to JSON and Markdown.
        """

        try:
            json_path = Path(self.campaign_health_dir) / f"{report_name}.json"
            md_path = Path(self.campaign_health_dir) / f"{report_name}.md"

            write_json(json_path, health_report)
            write_text(md_path, render_campaign_health_markdown(health_report))

            logger.info(
                f"Wrote campaign health report: {json_path}, {md_path}"
            )

            return {
                "json": str(json_path),
                "markdown": str(md_path)
            }

        except Exception as e:
            logger.error(
                f"Failed writing campaign health report: {e}"
            )

            raise ReportGenerationError(
                f"Failed writing campaign health report: {e}"
            )

    def write_full_report(
        self,
        summaries: List[Dict],
        root_cause_reports: List[Dict],
        retry_reports: List[Dict],
        health_report: Dict,
        report_name: str = "globalroamer_ai_report"
    ) -> Dict[str, str]:
        """
        Write combined AI observability report.
        """

        try:
            full_report = {
                "generated_at": datetime.now(timezone.utc).isoformat(),
                "campaign_health": health_report,
                "ai_summaries": summaries,
                "root_cause_reports": root_cause_reports,
                "retry_reports": retry_reports,
            }

            json_path = Path(self.campaign_health_dir) / f"{report_name}.json"
            md_path = Path(self.campaign_health_dir) / f"{report_name}.md"

            write_json(json_path, full_report)

            markdown = render_full_markdown(
                summaries=summaries,
                root_cause_reports=root_cause_reports,
                retry_reports=retry_reports,
                health_report=health_report,
            )

            write_text(md_path, markdown)

            logger.info(
                f"Wrote full AI observability report: {json_path}, {md_path}"
            )

            return {
                "json": str(json_path),
                "markdown": str(md_path)
            }

        except Exception as e:
            logger.error(
                f"Failed writing full report: {e}"
            )

            raise ReportGenerationError(
                f"Failed writing full report: {e}"
            )

    def _ensure_directories(self) -> None:
        """
        Ensure output directories exist.
        """

        for directory in [
            self.ai_summary_dir,
            self.root_cause_dir,
            self.campaign_health_dir
        ]:
            os.makedirs(directory, exist_ok=True)


def write_json(
    path: Path,
    data
) -> None:
    """
    Write JSON file.
    """

    with open(path, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            indent=2,
            ensure_ascii=False
        )


def write_text(
    path: Path,
    content: str
) -> None:
    """
    Write text/markdown file.
    """

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def render_ai_summaries_markdown(
    summaries: List[Dict]
) -> str:
    lines = [
        "# GlobalRoamer AI Summaries",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    for item in summaries:
        lines.extend([
            f"## Chunk: {item.get('chunk_id')}",
            "",
            f"- Trace ID: `{item.get('trace_id')}`",
            f"- Source File: `{item.get('source_file')}`",
            f"- Similar Incidents: {item.get('similar_incident_count')}",
            "",
            item.get("summary", ""),
            "",
            "---",
            "",
        ])

    return "\n".join(lines)


def render_root_cause_markdown(
    reports: List[Dict]
) -> str:
    lines = [
        "# GlobalRoamer Root-Cause Reports",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
    ]

    for item in reports:
        lines.extend([
            f"## Chunk: {item.get('chunk_id')}",
            "",
            f"- Trace ID: `{item.get('trace_id')}`",
            f"- Source File: `{item.get('source_file')}`",
            f"- Similar Incidents: {item.get('similar_incident_count')}",
            "",
            item.get("root_cause_analysis", ""),
            "",
            "---",
            "",
        ])

    return "\n".join(lines)


def render_campaign_health_markdown(
    report: Dict
) -> str:
    lines = [
        "# GlobalRoamer Campaign Health",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"- Health Score: **{report.get('campaign_health_score')}**",
        f"- Status: **{report.get('campaign_status')}**",
        f"- Total Chunks: {report.get('total_chunks')}",
        f"- Source Files: {report.get('source_file_count')}",
        "",
        "## Main Issue Cluster",
        "",
        report.get("main_issue_cluster", "N/A"),
        "",
        "## Recommended Action",
        "",
        report.get("recommended_action", "N/A"),
        "",
        "## Dominant Signals",
        "",
    ]

    for signal, count in report.get("dominant_signals", []):
        lines.append(f"- {signal}: {count}")

    lines.extend([
        "",
        "## Retry Decision Distribution",
        "",
    ])

    for decision, count in report.get("retry_decision_distribution", {}).items():
        lines.append(f"- {decision}: {count}")

    return "\n".join(lines)


def render_full_markdown(
    summaries: List[Dict],
    root_cause_reports: List[Dict],
    retry_reports: List[Dict],
    health_report: Dict
) -> str:
    lines = [
        "# GlobalRoamer AI Observability Report",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Campaign Health",
        "",
        f"- Health Score: **{health_report.get('campaign_health_score')}**",
        f"- Status: **{health_report.get('campaign_status')}**",
        f"- Main Issue Cluster: {health_report.get('main_issue_cluster')}",
        f"- Recommended Action: {health_report.get('recommended_action')}",
        "",
        "## Retry Recommendations",
        "",
    ]

    for report in retry_reports:
        lines.extend([
            f"### Chunk: {report.get('chunk_id')}",
            "",
            f"- Decision: **{report.get('retry_decision')}**",
            f"- Risk Level: **{report.get('risk_level')}**",
            f"- Reason: {report.get('retry_reason')}",
            f"- Cooldown Minutes: {report.get('cooldown_minutes')}",
            "",
        ])

    lines.extend([
        "---",
        "",
        "## Root-Cause Analysis",
        "",
    ])

    for report in root_cause_reports:
        lines.extend([
            f"### Chunk: {report.get('chunk_id')}",
            "",
            report.get("root_cause_analysis", ""),
            "",
        ])

    lines.extend([
        "---",
        "",
        "## AI Summaries",
        "",
    ])

    for summary in summaries:
        lines.extend([
            f"### Chunk: {summary.get('chunk_id')}",
            "",
            summary.get("summary", ""),
            "",
        ])

    return "\n".join(lines)
