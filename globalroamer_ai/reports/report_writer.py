#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import logging
import os

from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from globalroamer_ai.core.exceptions import ReportGenerationError

logger = logging.getLogger("report_writer")


class ReportWriter:
    """
    Writes GlobalRoamer AI observability outputs.

    Outputs:
    - JSON reports
    - Markdown reports
    """

    def __init__(
        self,
        ai_summary_dir: str,
        root_cause_dir: str,
        campaign_health_dir: str,
    ):
        self.ai_summary_dir = ai_summary_dir
        self.root_cause_dir = root_cause_dir
        self.campaign_health_dir = campaign_health_dir

        self._ensure_directories()

        logger.info("ReportWriter initialized")

    def write_ai_summaries(
        self,
        summaries: list[dict[str, Any]],
        report_name: str = "ai_summaries",
    ) -> dict[str, str]:

        try:
            json_path = Path(self.ai_summary_dir) / f"{report_name}.json"
            md_path = Path(self.ai_summary_dir) / f"{report_name}.md"

            write_json(json_path, summaries)
            write_text(
                md_path,
                render_ai_summaries_markdown(summaries),
            )

            logger.info(
                f"Wrote AI summaries: {json_path}, {md_path}"
            )

            return {
                "json": str(json_path),
                "markdown": str(md_path),
            }

        except Exception as exc:
            logger.error(
                f"Failed writing AI summaries: {exc}"
            )

            raise ReportGenerationError(
                f"Failed writing AI summaries: {exc}"
            )

    def write_root_cause_reports(
        self,
        reports: list[dict[str, Any]],
        report_name: str = "root_cause_reports",
    ) -> dict[str, str]:

        try:
            json_path = Path(self.root_cause_dir) / f"{report_name}.json"
            md_path = Path(self.root_cause_dir) / f"{report_name}.md"

            write_json(json_path, reports)

            write_text(
                md_path,
                render_root_cause_markdown(reports),
            )

            logger.info(
                f"Wrote root-cause reports: {json_path}, {md_path}"
            )

            return {
                "json": str(json_path),
                "markdown": str(md_path),
            }

        except Exception as exc:
            logger.error(
                f"Failed writing root-cause reports: {exc}"
            )

            raise ReportGenerationError(
                f"Failed writing root-cause reports: {exc}"
            )

    def write_campaign_health(
        self,
        health_report: dict[str, Any],
        report_name: str = "campaign_health",
    ) -> dict[str, str]:

        try:
            json_path = (
                Path(self.campaign_health_dir)
                / f"{report_name}.json"
            )

            md_path = (
                Path(self.campaign_health_dir)
                / f"{report_name}.md"
            )

            write_json(json_path, health_report)

            write_text(
                md_path,
                render_campaign_health_markdown(
                    health_report
                ),
            )

            logger.info(
                f"Wrote campaign health report: "
                f"{json_path}, {md_path}"
            )

            return {
                "json": str(json_path),
                "markdown": str(md_path),
            }

        except Exception as exc:
            logger.error(
                f"Failed writing campaign health report: {exc}"
            )

            raise ReportGenerationError(
                f"Failed writing campaign health report: {exc}"
            )

    def write_full_report(
        self,
        summaries: list[dict[str, Any]],
        root_cause_reports: list[dict[str, Any]],
        retry_reports: list[dict[str, Any]],
        health_report: dict[str, Any],
        report_name: str = "globalroamer_ai_report",
    ) -> dict[str, str]:

        try:
            full_report = {
                "generated_at": datetime.now(
                    timezone.utc
                ).isoformat(),

                "campaign_health": health_report,
                "ai_summaries": summaries,
                "root_cause_reports": root_cause_reports,
                "retry_reports": retry_reports,
            }

            json_path = (
                Path(self.campaign_health_dir)
                / f"{report_name}.json"
            )

            md_path = (
                Path(self.campaign_health_dir)
                / f"{report_name}.md"
            )

            write_json(json_path, full_report)

            markdown = render_full_markdown(
                summaries=summaries,
                root_cause_reports=root_cause_reports,
                retry_reports=retry_reports,
                health_report=health_report,
            )

            write_text(md_path, markdown)

            logger.info(
                f"Wrote full AI observability report: "
                f"{json_path}, {md_path}"
            )

            return {
                "json": str(json_path),
                "markdown": str(md_path),
            }

        except Exception as exc:
            logger.error(
                f"Failed writing full report: {exc}"
            )

            raise ReportGenerationError(
                f"Failed writing full report: {exc}"
            )

    def _ensure_directories(self) -> None:

        for directory in [
            self.ai_summary_dir,
            self.root_cause_dir,
            self.campaign_health_dir,
        ]:
            os.makedirs(directory, exist_ok=True)


def write_json(path: Path, data: Any) -> None:

    with open(path, "w", encoding="utf-8") as file:
        json.dump(
            data,
            file,
            indent=2,
            ensure_ascii=False,
            default=str,
        )


def write_text(path: Path, content: str) -> None:

    with open(path, "w", encoding="utf-8") as file:
        file.write(content)


def render_ai_summaries_markdown(
    summaries: list[dict[str, Any]],
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
            f"- Testcase ID: `{item.get('testcase_id')}`",
            f"- Similar Incidents: {item.get('similar_incident_count')}",
            f"- Operators: {', '.join(item.get('operators', []))}",
            f"- Countries: {', '.join(item.get('countries', []))}",
            f"- Event Families: {', '.join(item.get('event_families', []))}",
            "",
            item.get("summary", ""),
            "",
            "---",
            "",
        ])

    return "\n".join(lines)


def render_root_cause_markdown(
    reports: list[dict[str, Any]],
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
            f"- Testcase ID: `{item.get('testcase_id')}`",
            f"- Similar Incidents: {item.get('similar_incident_count')}",
            f"- Event Families: {', '.join(item.get('event_families', []))}",
            f"- Causes: {', '.join(item.get('causes', []))}",
            "",
            item.get("root_cause_analysis", ""),
            "",
            "---",
            "",
        ])

    return "\n".join(lines)


def render_campaign_health_markdown(
    report: dict[str, Any],
) -> str:

    lines = [
        "# GlobalRoamer Campaign Health",
        "",
        f"Generated at: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"- Health Score: **{report.get('campaign_health_score')}**",
        f"- Status: **{report.get('campaign_status')}**",
        f"- Total Chunks: {report.get('total_chunks')}",
        f"- Failure Chunks: {report.get('failure_chunk_count')}",
        f"- Retry Chunks: {report.get('retry_chunk_count')}",
        f"- High Severity Chunks: {report.get('high_severity_chunk_count')}",
        "",
        "## Main Issue Cluster",
        "",
        report.get("main_issue_cluster", "N/A"),
        "",
        "## Recommended Action",
        "",
        report.get("recommended_action", "N/A"),
        "",
        "## Dominant Event Families",
        "",
    ]

    for name, count in report.get(
        "dominant_event_families",
        [],
    ):
        lines.append(f"- {name}: {count}")

    lines.extend([
        "",
        "## Dominant Causes",
        "",
    ])

    for name, count in report.get(
        "dominant_causes",
        [],
    ):
        lines.append(f"- {name}: {count}")

    lines.extend([
        "",
        "## Retry Decision Distribution",
        "",
    ])

    for name, count in report.get(
        "retry_decision_distribution",
        {},
    ).items():
        lines.append(f"- {name}: {count}")

    return "\n".join(lines)


def render_full_markdown(
    summaries: list[dict[str, Any]],
    root_cause_reports: list[dict[str, Any]],
    retry_reports: list[dict[str, Any]],
    health_report: dict[str, Any],
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
        "---",
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
