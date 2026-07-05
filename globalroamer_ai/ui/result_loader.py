from __future__ import annotations

import json

from pathlib import Path
from typing import Any


class ResultLoader:
    def __init__(self, base_dir: str | Path):
        self.base_dir = Path(base_dir)
        self.data_dir = self.base_dir / "var" / "data"
        self.output_dir = self.base_dir / "var" / "output"

    def load_chunks(self) -> list[dict[str, Any]]:
        return self._load_json_list_from_dir(self.data_dir / "chunks", "*_chunks.json")

    def load_events(self) -> list[dict[str, Any]]:
        events = []

        for path in sorted((self.data_dir / "normalized_events").glob("*_events.json")):
            data = self._read_json(path)
            if isinstance(data, list):
                events.extend(data)

        return events

    def load_parsed_traces(self) -> list[dict[str, Any]]:
        return self._load_json_list_from_dir(self.data_dir / "normalized_events", "*_parsed.json")

    def load_similarity_results(self) -> dict[str, list[dict[str, Any]]]:
        result = {}
        similarity_dir = self.output_dir / "ai_summaries" / "similarity_results"

        if not similarity_dir.exists():
            return result

        for path in sorted(similarity_dir.glob("*_similarity.json")):
            data = self._read_json(path)
            if isinstance(data, list):
                result[path.stem.replace("_similarity", "")] = data

        return result

    def load_ai_summaries(self) -> list[dict[str, Any]]:
        return self._load_json_list_from_dir(self.output_dir / "ai_summaries", "*.json")

    def load_campaign_health(self) -> dict[str, Any]:
        return self._load_first_existing_json([
            self.output_dir / "campaign_health" / "campaign_health.json",
            self.output_dir / "campaign_health.json",
        ])

    def load_root_cause_report(self) -> dict[str, Any]:
        return self._load_first_existing_json([
            self.output_dir / "root_cause_reports" / "root_cause_reports.json",
            self.output_dir / "root_cause_report.json",
        ])

    def load_markdown_reports(self) -> dict[str, str]:
        reports = {}

        for path in [
            self.output_dir / "ai_summaries" / "ai_summaries.md",
            self.output_dir / "campaign_health" / "campaign_health.md",
            self.output_dir / "root_cause_reports" / "root_cause_reports.md",
            self.output_dir / "globalroamer_ai_report.md",
        ]:
            if path.is_file():
                reports[path.stem] = path.read_text(encoding="utf-8", errors="replace")

        return reports

    def testcase_ids(self) -> list[str]:
        ids = set()

        for event in self.load_events():
            testcase_id = event.get("testcase_id")
            if testcase_id:
                ids.add(str(testcase_id))

        return sorted(ids)

    def testcase_events(self, testcase_id: str) -> list[dict[str, Any]]:
        return [
            event
            for event in self.load_events()
            if str(event.get("testcase_id")) == str(testcase_id)
        ]

    def testcase_chunks(self, testcase_id: str) -> list[dict[str, Any]]:
        return [
            chunk
            for chunk in self.load_chunks()
            if str(chunk.get("testcase_id")) == str(testcase_id)
        ]

    def testcase_summaries(self, testcase_id: str) -> list[dict[str, Any]]:
        return [
            summary
            for summary in self.load_ai_summaries()
            if str(summary.get("testcase_id")) == str(testcase_id)
        ]

    def testcase_overview(self) -> list[dict[str, Any]]:
        overview = {}

        for event in self.load_events():
            testcase_id = str(event.get("testcase_id", "unknown"))

            if testcase_id not in overview:
                overview[testcase_id] = {
                    "testcase_id": testcase_id,
                    "operator": event.get("operator"),
                    "country": event.get("country"),
                    "severity": event.get("severity"),
                    "events": 0,
                    "failures": 0,
                    "retry_recommended": 0,
                }

            overview[testcase_id]["events"] += 1

            if event.get("result") == "failed" or event.get("event_family") == "failure":
                overview[testcase_id]["failures"] += 1

            if event.get("retry_recommended"):
                overview[testcase_id]["retry_recommended"] += 1

            if event.get("severity") == "high":
                overview[testcase_id]["severity"] = "high"
            elif event.get("severity") == "medium" and overview[testcase_id]["severity"] != "high":
                overview[testcase_id]["severity"] = "medium"

        return sorted(overview.values(), key=lambda item: item["testcase_id"])

    def _load_json_list_from_dir(self, directory: Path, pattern: str) -> list[dict[str, Any]]:
        result = []

        if not directory.exists():
            return result

        for path in sorted(directory.glob(pattern)):
            data = self._read_json(path)

            if isinstance(data, list):
                result.extend(item for item in data if isinstance(item, dict))
            elif isinstance(data, dict):
                result.append(data)

        return result

    def _load_first_existing_json(self, paths: list[Path]) -> dict[str, Any]:
        for path in paths:
            if path.is_file():
                data = self._read_json(path)
                if isinstance(data, dict):
                    return data

        return {}

    def _read_json(self, path: Path) -> Any:
        try:
            return json.loads(path.read_text(encoding="utf-8", errors="replace"))
        except Exception:
            return None
