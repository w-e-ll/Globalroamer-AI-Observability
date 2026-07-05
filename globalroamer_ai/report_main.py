#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

from globalroamer_ai.ai.ai_summary_service import AISummaryService
from globalroamer_ai.core.app_config import load_yaml_config
from globalroamer_ai.reports.campaign_health import CampaignHealthScorer
from globalroamer_ai.core.exceptions import GlobalRoamerAIException
from globalroamer_ai.reports.report_writer import ReportWriter
from globalroamer_ai.ai.retry_advisor import RetryAdvisor
from globalroamer_ai.ai.root_cause_service import RootCauseService
from globalroamer_ai.core.setup_logger import setup_logger

load_dotenv()

logger = logging.getLogger("report_main")


def load_json_file(path: Path) -> Any:
    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def load_chunks(chunks_dir: str) -> list[dict[str, Any]]:
    chunks = []
    chunk_path = Path(chunks_dir)

    if not chunk_path.exists():
        logger.warning(f"Chunks directory does not exist: {chunk_path}")
        return chunks

    for chunk_file in sorted(chunk_path.glob("*_chunks.json")):
        logger.info(f"Loading chunks: {chunk_file}")
        data = load_json_file(chunk_file)

        if isinstance(data, list):
            chunks.extend(data)
        else:
            logger.warning(f"Skipping invalid chunk file format: {chunk_file}")

    logger.info(f"Loaded {len(chunks)} chunks")
    return chunks


def load_similarity_results(ai_summary_dir: str) -> dict[str, list[dict[str, Any]]]:
    similarity_dir = Path(ai_summary_dir) / "similarity_results"
    results_by_chunk = {}

    if not similarity_dir.exists():
        logger.warning(f"Similarity results directory does not exist: {similarity_dir}")
        return results_by_chunk

    for result_file in sorted(similarity_dir.glob("*_similarity.json")):
        logger.info(f"Loading similarity result: {result_file}")
        results = load_json_file(result_file)

        if not isinstance(results, list) or not results:
            continue

        chunk_id = extract_chunk_id_from_similarity_file(result_file, results)

        if chunk_id:
            results_by_chunk[chunk_id] = results

    logger.info(f"Loaded similarity results for {len(results_by_chunk)} chunks")
    return results_by_chunk


def extract_chunk_id_from_similarity_file(result_file: Path, results: list[dict[str, Any]]) -> str | None:
    for item in results:
        metadata = item.get("metadata", {})
        chunk_id = metadata.get("chunk_id") or item.get("chunk_id")

        if chunk_id:
            return chunk_id

    filename = result_file.name

    if filename.endswith("_similarity.json"):
        return filename.replace("_similarity.json", "").replace("__", ":")

    return None


def filter_chunks(chunks: list[dict[str, Any]], max_chunks: int | None = None) -> list[dict[str, Any]]:
    selected = []

    for chunk in chunks:
        if chunk.get("has_failure") or chunk.get("has_high_severity") or chunk.get("has_retry_recommended"):
            selected.append(chunk)

    if not selected:
        selected = chunks

    if max_chunks:
        selected = selected[:max_chunks]

    return selected


def generate_retry_reports(
        chunks: list[dict[str, Any]],
        similarity_results_by_chunk: dict[str, list[dict[str, Any]]],
        retry_advisor: RetryAdvisor
) -> list[dict[str, Any]]:
    reports = []

    for chunk in chunks:
        chunk_id = chunk.get("chunk_id")
        similar_incidents = similarity_results_by_chunk.get(chunk_id, [])

        retry_report = retry_advisor.analyze_retry_strategy(
            chunk=chunk,
            similar_incidents=similar_incidents
        )

        reports.append(retry_report)

    return reports


def main() -> None:
    parser = argparse.ArgumentParser(prog="report_main.py")
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--chunks-dir", required=False)
    parser.add_argument("--max-chunks", type=int, required=False)
    parser.add_argument("--skip-ai", action="store_true")
    args = parser.parse_args()

    cfg = load_yaml_config(args.config_dir)

    logfile = os.path.join(cfg.log_dir, "report.log")
    setup_logger(logfile)

    logger.info("=== GlobalRoamer AI Report Started ===")

    try:
        chunks_dir = args.chunks_dir or cfg.chunks_dir
        chunks = load_chunks(chunks_dir)

        if not chunks:
            logger.warning("No chunks available for report generation")
            return

        report_chunks = filter_chunks(chunks, max_chunks=args.max_chunks)
        similarity_results_by_chunk = load_similarity_results(cfg.ai_summary_dir)

        retry_advisor = RetryAdvisor()
        health_scorer = CampaignHealthScorer()
        report_writer = ReportWriter(
            ai_summary_dir=cfg.ai_summary_dir,
            root_cause_dir=cfg.root_cause_dir,
            campaign_health_dir=cfg.campaign_health_dir
        )

        retry_reports = generate_retry_reports(report_chunks, similarity_results_by_chunk, retry_advisor)

        if args.skip_ai:
            summaries = []
            root_cause_reports = []
        else:
            summary_service = AISummaryService(model=cfg.llm_model)
            root_cause_service = RootCauseService(model=cfg.llm_model)

            summaries = summary_service.summarize_many(
                chunks=report_chunks,
                similarity_results_by_chunk=similarity_results_by_chunk
            )

            root_cause_reports = root_cause_service.analyze_many(
                chunks=report_chunks,
                similarity_results_by_chunk=similarity_results_by_chunk
            )

        health_report = health_scorer.score_campaign(
            chunks=report_chunks,
            retry_reports=retry_reports,
            root_cause_reports=root_cause_reports
        )

        report_writer.write_ai_summaries(summaries=summaries)
        report_writer.write_root_cause_reports(reports=root_cause_reports)
        report_writer.write_campaign_health(health_report=health_report)
        report_writer.write_full_report(
            summaries=summaries, root_cause_reports=root_cause_reports,
            retry_reports=retry_reports, health_report=health_report
        )

        logger.info(
            f"=== GlobalRoamer AI Report Finished. "
            f"chunks={len(report_chunks)} "
            f"retry_reports={len(retry_reports)} "
            f"summaries={len(summaries)} "
            f"root_causes={len(root_cause_reports)} ==="
        )

    except GlobalRoamerAIException as exc:
        logger.error(f"Application error: {exc}")
        raise

    except Exception as exc:
        logger.exception(f"Unexpected fatal error: {exc}")
        raise


if __name__ == "__main__":
    main()
