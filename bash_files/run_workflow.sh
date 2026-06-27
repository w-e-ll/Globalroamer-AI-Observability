#!/usr/bin/env bash

set -euo pipefail

# =========================================================
# GlobalRoamer AI Observability Workflow
# =========================================================
#
# Steps:
# 1. Ingest trace/result files
# 2. Parse, normalize, and chunk traces
# 3. Generate embeddings and similarity search
# 4. Generate AI summaries, root-cause analysis, retry advice,
#    and campaign health reports
#
# Usage:
#   bash bash_files/run_workflow.sh
#
# Cron example:
#   0 */2 * * * /home/<user>/apps/globalroamer_ai_observability/bash_files/run_workflow.sh > /dev/null 2>&1
# =========================================================

APP_BASE="/home/<user>/apps/globalroamer_ai_observability"
PYTHON_BIN="${APP_BASE}/venv/bin/python"
CONFIG_DIR="${APP_BASE}/etc"

LOG_DIR="${APP_BASE}/var/log"
WORKFLOW_LOG="${LOG_DIR}/workflow.log"

mkdir -p "${LOG_DIR}"

echo "=========================================================" >> "${WORKFLOW_LOG}"
echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') GlobalRoamer AI workflow started" >> "${WORKFLOW_LOG}"
echo "APP_BASE=${APP_BASE}" >> "${WORKFLOW_LOG}"
echo "CONFIG_DIR=${CONFIG_DIR}" >> "${WORKFLOW_LOG}"

cd "${APP_BASE}"

echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') Step 1: ingest_main.py" >> "${WORKFLOW_LOG}"
"${PYTHON_BIN}" -m globalroamer_ai.ingest_main \
  --config-dir "${CONFIG_DIR}" \
  >> "${WORKFLOW_LOG}" 2>&1

echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') Step 2: analyze_main.py" >> "${WORKFLOW_LOG}"
"${PYTHON_BIN}" -m globalroamer_ai.analyze_main \
  --config-dir "${CONFIG_DIR}" \
  --top-k 5 \
  >> "${WORKFLOW_LOG}" 2>&1

echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') Step 3: report_main.py" >> "${WORKFLOW_LOG}"
"${PYTHON_BIN}" -m globalroamer_ai.report_main \
  --config-dir "${CONFIG_DIR}" \
  >> "${WORKFLOW_LOG}" 2>&1

echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') GlobalRoamer AI workflow finished successfully" >> "${WORKFLOW_LOG}"

