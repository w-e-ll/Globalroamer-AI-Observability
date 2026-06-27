#!/usr/bin/env bash

set -euo pipefail

# =========================================================
# GlobalRoamer AI Cleanup Script
# =========================================================
#
# Purpose:
# - cleanup old logs
# - cleanup old AI outputs
# - cleanup temporary normalized/chunk data
#
# Usage:
#   bash bash_files/cleanup_folders.sh
#
# Cron example:
#   30 3 * * * /home/<user>/apps/globalroamer_ai_observability/bash_files/cleanup_folders.sh
#
# =========================================================

APP_BASE="/home/<user>/apps/globalroamer_ai_observability"

LOG_DIR="${APP_BASE}/var/log"

NORMALIZED_DIR="${APP_BASE}/var/data/normalized_events"
CHUNKS_DIR="${APP_BASE}/var/data/chunks"

AI_SUMMARY_DIR="${APP_BASE}/var/output/ai_summaries"
ROOT_CAUSE_DIR="${APP_BASE}/var/output/root_cause_reports"
CAMPAIGN_HEALTH_DIR="${APP_BASE}/var/output/campaign_health"

WORKFLOW_LOG="${LOG_DIR}/cleanup.log"

# =========================================================
# Retention settings
# =========================================================

LOG_RETENTION_DAYS=14

NORMALIZED_RETENTION_DAYS=7
CHUNK_RETENTION_DAYS=7

AI_REPORT_RETENTION_DAYS=30

# =========================================================
# Logging
# =========================================================

mkdir -p "${LOG_DIR}"

log() {
  echo "$(date -u '+%Y-%m-%dT%H:%M:%SZ') $1" \
    | tee -a "${WORKFLOW_LOG}"
}

log "========================================================="
log "GlobalRoamer AI cleanup started"

# =========================================================
# Cleanup logs
# =========================================================

log "Cleaning old logs > ${LOG_RETENTION_DAYS} days"

find "${LOG_DIR}" \
  -type f \
  -name "*.log*" \
  -mtime +"${LOG_RETENTION_DAYS}" \
  -print \
  -delete \
  >> "${WORKFLOW_LOG}" 2>&1 || true

# =========================================================
# Cleanup normalized events
# =========================================================

log "Cleaning normalized events > ${NORMALIZED_RETENTION_DAYS} days"

find "${NORMALIZED_DIR}" \
  -type f \
  -name "*.json" \
  -mtime +"${NORMALIZED_RETENTION_DAYS}" \
  -print \
  -delete \
  >> "${WORKFLOW_LOG}" 2>&1 || true

# =========================================================
# Cleanup chunks
# =========================================================

log "Cleaning chunks > ${CHUNK_RETENTION_DAYS} days"

find "${CHUNKS_DIR}" \
  -type f \
  -name "*.json" \
  -mtime +"${CHUNK_RETENTION_DAYS}" \
  -print \
  -delete \
  >> "${WORKFLOW_LOG}" 2>&1 || true

# =========================================================
# Cleanup AI summaries
# =========================================================

log "Cleaning AI summaries > ${AI_REPORT_RETENTION_DAYS} days"

find "${AI_SUMMARY_DIR}" \
  -type f \
  \( -name "*.json" -o -name "*.md" \) \
  -mtime +"${AI_REPORT_RETENTION_DAYS}" \
  -print \
  -delete \
  >> "${WORKFLOW_LOG}" 2>&1 || true

# =========================================================
# Cleanup root-cause reports
# =========================================================

log "Cleaning root-cause reports > ${AI_REPORT_RETENTION_DAYS} days"

find "${ROOT_CAUSE_DIR}" \
  -type f \
  \( -name "*.json" -o -name "*.md" \) \
  -mtime +"${AI_REPORT_RETENTION_DAYS}" \
  -print \
  -delete \
  >> "${WORKFLOW_LOG}" 2>&1 || true

# =========================================================
# Cleanup campaign health reports
# =========================================================

log "Cleaning campaign health reports > ${AI_REPORT_RETENTION_DAYS} days"

find "${CAMPAIGN_HEALTH_DIR}" \
  -type f \
  \( -name "*.json" -o -name "*.md" \) \
  -mtime +"${AI_REPORT_RETENTION_DAYS}" \
  -print \
  -delete \
  >> "${WORKFLOW_LOG}" 2>&1 || true

# =========================================================
# Cleanup empty directories
# =========================================================

log "Cleaning empty directories"

find "${APP_BASE}/var" \
  -type d \
  -empty \
  -print \
  -delete \
  >> "${WORKFLOW_LOG}" 2>&1 || true

log "GlobalRoamer AI cleanup finished"


