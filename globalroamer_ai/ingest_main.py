#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import json
import logging
import os

from dataclasses import asdict
from pathlib import Path

from dotenv import load_dotenv

from globalroamer_ai.core.app_config import load_yaml_config
from globalroamer_ai.core.exceptions import GlobalRoamerAIException
from globalroamer_ai.core.setup_logger import setup_logger
from globalroamer_ai.ingestion.trace_loader import TraceLoader
from globalroamer_ai.ingestion.trace_normalizer import TraceNormalizer
from globalroamer_ai.ingestion.trace_parser import TraceParser

load_dotenv()

logger = logging.getLogger("ingest_main")


def save_json(data: object, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, default=str), encoding="utf-8")


def resolve_path(value: str | None, fallback: str) -> str:
    return value if value else fallback


def main() -> None:
    parser = argparse.ArgumentParser(prog="ingest_main.py")
    parser.add_argument("--config-dir", required=True)
    parser.add_argument("--trace-dir", required=False)
    parser.add_argument("--report-dir", required=False)
    parser.add_argument("--result-dir", required=False)
    parser.add_argument("--mapping-path", required=False)
    parser.add_argument("--output-dir", required=False)
    args = parser.parse_args()

    cfg = load_yaml_config(args.config_dir)

    logfile = os.path.join(cfg.log_dir, "ingest.log")
    setup_logger(logfile)

    trace_dir = resolve_path(args.trace_dir, cfg.input_trace_dir)
    result_dir = resolve_path(args.result_dir, cfg.input_result_dir)
    report_dir = resolve_path(args.report_dir, cfg.input_report_dir)
    output_dir = Path(resolve_path(args.output_dir, cfg.normalized_dir))

    logger.info("=== GlobalRoamer AI Ingest Started ===")
    logger.info(f"Environment: {cfg.env}")
    logger.info(f"Trace input directory: {trace_dir}")
    logger.info(f"Result input directory: {result_dir}")
    logger.info(f"Report input directory: {report_dir}")
    logger.info(f"Output directory: {output_dir}")

    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        loader = TraceLoader(trace_dir=trace_dir, result_dir=result_dir, report_dir=report_dir, template_dir=cfg.input_template_dir)
        trace_parser = TraceParser()
        normalizer = TraceNormalizer()

        artifacts = loader.discover()

        logger.info(f"Discovered {len(artifacts)} artifacts")

        total_events = 0

        for artifact in artifacts:
            logger.info(f"Processing testcase: {artifact.testcase_id}")

            parsed = trace_parser.parse(source=artifact, mapping_path=args.mapping_path)
            events = normalizer.normalize(parsed)

            parsed_path = output_dir / f"{artifact.testcase_id}_parsed.json"
            events_path = output_dir / f"{artifact.testcase_id}_events.json"

            save_json(asdict(parsed), parsed_path)
            save_json([asdict(event) for event in events], events_path)

            total_events += len(events)

            logger.info(f"Processed testcase={artifact.testcase_id}, evidences={len(parsed.evidences)}, events={len(events)}")
            print(f"Processed testcase={artifact.testcase_id}, evidences={len(parsed.evidences)}, events={len(events)}")

        logger.info(f"=== GlobalRoamer AI Ingest Finished. Testcases={len(artifacts)}, events={total_events} ===")

    except GlobalRoamerAIException as exc:
        logger.error(f"Application error: {exc}")
        raise

    except Exception as exc:
        logger.exception(f"Unexpected fatal error: {exc}")
        raise


if __name__ == "__main__":
    main()
