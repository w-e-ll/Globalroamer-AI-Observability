from __future__ import annotations

import os
import subprocess
import sys

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass
class PipelineResult:
    command: list[str]
    return_code: int | None
    started_at: str
    finished_at: str | None
    stdout: str
    stderr: str
    success: bool


class PipelineRunner:
    def __init__(self, project_root: str | Path):
        self.project_root = Path(project_root)

    def run_ingest(self, config_dir: str = "etc") -> PipelineResult:
        return self._run_module(
            module="globalroamer_ai.ingest_main",
            args=[
                "--config-dir",
                config_dir,
            ],
        )

    def run_analyze(
        self,
        config_dir: str = "etc",
        skip_embedding: bool = False,
        skip_similarity: bool = False,
    ) -> PipelineResult:
        args = [
            "--config-dir",
            config_dir,
        ]

        if skip_embedding:
            args.append("--skip-embedding")

        if skip_similarity:
            args.append("--skip-similarity")

        return self._run_module(
            module="globalroamer_ai.analyze_main",
            args=args,
        )

    def run_report(
        self,
        config_dir: str = "etc",
        max_chunks: int | None = None,
        skip_ai: bool = False,
    ) -> PipelineResult:
        args = [
            "--config-dir",
            config_dir,
        ]

        if max_chunks is not None:
            args.extend(["--max-chunks", str(max_chunks)])

        if skip_ai:
            args.append("--skip-ai")

        return self._run_module(
            module="globalroamer_ai.report_main",
            args=args,
        )

    def run_full_pipeline(
        self,
        config_dir: str = "etc",
        max_chunks: int | None = None,
        skip_embedding: bool = False,
        skip_similarity: bool = False,
        skip_ai: bool = False,
    ) -> list[PipelineResult]:
        results = []

        ingest_result = self.run_ingest(config_dir=config_dir)
        results.append(ingest_result)

        if not ingest_result.success:
            return results

        analyze_result = self.run_analyze(
            config_dir=config_dir,
            skip_embedding=skip_embedding,
            skip_similarity=skip_similarity,
        )
        results.append(analyze_result)

        if not analyze_result.success:
            return results

        report_result = self.run_report(
            config_dir=config_dir,
            max_chunks=max_chunks,
            skip_ai=skip_ai,
        )
        results.append(report_result)

        return results

    def _run_module(self, module: str, args: list[str]) -> PipelineResult:
        command = [
            sys.executable,
            "-m",
            module,
            *args,
        ]

        started_at = datetime.now().isoformat(timespec="seconds")

        process = subprocess.run(
            command,
            cwd=self.project_root,
            env=self._build_env(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

        finished_at = datetime.now().isoformat(timespec="seconds")

        return PipelineResult(
            command=command,
            return_code=process.returncode,
            started_at=started_at,
            finished_at=finished_at,
            stdout=process.stdout or "",
            stderr=process.stderr or "",
            success=process.returncode == 0,
        )

    def _build_env(self) -> dict[str, str]:
        env = os.environ.copy()
        env["PYTHONUNBUFFERED"] = "1"
        return env
