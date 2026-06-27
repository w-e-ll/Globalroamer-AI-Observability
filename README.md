# GlobalRoamer AI Observability Layer

AI-assisted roaming diagnostics and operational intelligence platform.

This project is a prototype AI observability layer for GlobalRoamer-style telecom testing systems.
It analyzes noisy telecom trace/result files, extracts operational signals, finds similar historical incidents, generates AI summaries, suggests probable root causes, recommends retry strategies, and produces campaign-level health reports.

The goal is not to replace deterministic telecom validation logic.
The goal is to reduce mean-time-to-diagnosis for roaming failures and improve monitoring, observability, and operational decision-making.

---

## 1. Problem Context

GlobalRoamer-style telecom testing platforms generate large amounts of operational data:

* trace files;
* result files;
* campaign metadata;
* SIM / MSISDN / IMSI information;
* operator / PLMN context;
* PASS / FAIL / INCONCLUSIVE verdicts;
* retry attempts;
* execution timestamps;
* statusInfo messages;
* report mappings;
* internal logs.

Traditional automation can execute tests and generate reports, but engineers still need to manually inspect failures, compare traces, understand recurring patterns, and decide whether retries are useful.

This project adds an AI-assisted observability layer on top of that operational data.

---

## 2. Core Idea

Instead of embedding raw trace files directly, the system first converts telecom traces into normalized operational events.

Pipeline:

```text
TRACE / RESULT files
        ↓
Trace loader
        ↓
Parser / normalization
        ↓
Structured event timeline
        ↓
Chunking
        ↓
Embeddings
        ↓
Vector DB
        ↓
Similarity search
        ↓
AI summary / root-cause analysis / retry advice
        ↓
Campaign health report
```

---

## 3. Main Capabilities

### 3.1 Failure Pattern Detection

The system detects recurring operational patterns such as:

* LTE attach failures;
* IMS registration issues;
* authentication failures;
* paging instability;
* call setup problems;
* detach / release anomalies;
* timeout-heavy traces;
* repeated retry patterns.

Example output:

```text
Failure pattern:
Repeated network registration failure during LTE attach stage.

Evidence:
- authentication-related events detected
- timeout signals detected
- repeated attach/registration sequence
```

---

### 3.2 Similar Incident Retrieval

The system embeds normalized trace chunks and stores them in ChromaDB.

When a new trace is analyzed, the platform can retrieve similar historical chunks.

Example output:

```json
[
  {
    "rank": 1,
    "chunk_id": "trace_310830767.csv::chunk_2",
    "similarity_score": 0.8841,
    "metadata": {
      "signals": "attach,registration,timeout",
      "event_types": "network_registration_event,failure_event",
      "source_file": "trace_310830767.csv"
    }
  }
]
```

---

### 3.3 AI Summary

The AI summary service explains noisy telecom chunks in operational language.

Example output:

```text
1. What happened
The trace indicates instability during the LTE attach / registration workflow.

2. Failure or anomaly indicators
The chunk contains repeated attach, registration, timeout, and failure signals.

3. Likely workflow stage
Network registration / subscriber authentication stage.

4. Similarity observations
Similar historical chunks show timeout-heavy registration failures.

5. Suggested next engineering checks
Inspect SIM provisioning, roaming profile, PLMN configuration, and operator-side registration handling.
```

---

### 3.4 Root-Cause Suggestions

The root-cause service produces an engineering hypothesis, not a final truth.

Example output:

```text
Probable root cause:
Network registration instability during LTE attach sequence.

Evidence from trace:
- repeated attach/registration signals
- timeout indicators
- failure severity events

Similar historical patterns:
Similar chunks were found with registration timeout behavior.

Confidence level:
Medium

What to inspect next:
- HPMN/VPMN roaming configuration
- SIM profile
- IMSI/MSISDN mapping
- PLMN-specific attach behavior

Retry recommendation:
Retry after cooldown if the issue looks transient.
Escalate if the same pattern repeats.
```

---

### 3.5 Retry Intelligence

The retry advisor does not execute retries.
It provides operational recommendations.

Example output:

```json
{
  "retry_decision": "retry_after_cooldown",
  "retry_reason": "Possible transient telecom/network instability.",
  "cooldown_minutes": 30,
  "risk_level": "medium",
  "historical_match_count": 4,
  "average_similarity": 0.9123
}
```

Possible decisions:

```text
retry
retry_after_cooldown
do_not_retry
escalate
```

---

### 3.6 Campaign Health Scoring

The campaign health scorer aggregates chunk-level signals into campaign-level monitoring output.

Example output:

```json
{
  "campaign_health_score": 0.68,
  "campaign_status": "DEGRADED",
  "main_issue_cluster": "Timeout / network instability pattern",
  "recommended_action": "Retry after cooldown and monitor whether the same pattern repeats.",
  "dominant_signals": [
    ["timeout", 12],
    ["registration", 9],
    ["failure", 7]
  ]
}
```

---

## 4. Project Structure

```text
globalroamer_ai_observability/
│
├── bash_files/
│   ├── run_workflow.sh
│   └── cleanup_folders.sh
│
├── globalroamer_ai/
│   ├── lib/
│   │   ├── app_config.py
│   │   ├── setup_logger.py
│   │   ├── exceptions.py
│   │   │
│   │   ├── trace_loader.py
│   │   ├── trace_parser.py
│   │   ├── trace_normalizer.py
│   │   ├── trace_chunker.py
│   │   │
│   │   ├── embedding_service.py
│   │   ├── vector_store.py
│   │   ├── similarity_search.py
│   │   │
│   │   ├── ai_summary_service.py
│   │   ├── root_cause_service.py
│   │   ├── retry_advisor.py
│   │   ├── campaign_health.py
│   │   └── report_writer.py
│   │
│   ├── ingest_main.py
│   ├── analyze_main.py
│   └── report_main.py
│
├── etc/
│   └── globalroamer_ai_config.yml
│
├── var/
│   ├── input/
│   │   ├── traces/
│   │   ├── results/
│   │   └── campaign_metadata/
│   │
│   ├── data/
│   │   ├── normalized_events/
│   │   ├── chunks/
│   │   ├── embeddings/
│   │   └── vector_db/
│   │
│   ├── output/
│   │   ├── ai_summaries/
│   │   ├── root_cause_reports/
│   │   └── campaign_health/
│   │
│   └── log/
│       ├── ingest.log
│       ├── analyze.log
│       ├── report.log
│       └── workflow.log
│
├── .env
├── requirements.txt
├── README.md
└── VERSION
```

---

## 5. Service Parts Explained

### 5.1 `ingest_main.py`

Responsible for:

* loading configuration;
* discovering trace files;
* loading raw trace content;
* parsing trace lines;
* normalizing operational events;
* creating AI-ready chunks;
* saving normalized JSON and chunk JSON.

Input:

```text
var/input/traces/
```

Output:

```text
var/data/normalized_events/
var/data/chunks/
```

---

### 5.2 `analyze_main.py`

Responsible for:

* loading chunks;
* generating embeddings;
* storing chunks in ChromaDB;
* running similarity search;
* saving similarity results.

Input:

```text
var/data/chunks/
```

Output:

```text
var/data/vector_db/
var/output/ai_summaries/similarity_results/
```

---

### 5.3 `report_main.py`

Responsible for:

* loading chunks;
* loading similarity results;
* generating AI summaries;
* generating root-cause reports;
* generating retry recommendations;
* calculating campaign health;
* writing JSON and Markdown reports.

Output:

```text
var/output/ai_summaries/
var/output/root_cause_reports/
var/output/campaign_health/
```

---

## 6. Installation

### 6.1 System Requirements

Recommended development machine:

```text
OS: Linux
CPU: 4 cores+
RAM: 8 GB minimum, 16 GB recommended
Disk: 20 GB+
Python: 3.11+
```

Recommended small production VM:

```text
CPU: 4 vCPU
RAM: 16 GB
Disk: 50–100 GB SSD
OS: Ubuntu / Debian / RHEL
```

For 100+ users or large trace volumes:

```text
CPU: 8–16 vCPU
RAM: 32–64 GB
Disk: 200 GB+ SSD
Separate PostgreSQL / object storage recommended
```

---

### 6.2 Create Project Folder

```bash
mkdir -p /home/<user>/apps/globalroamer_ai_observability
cd /home/<user>/apps/globalroamer_ai_observability
```

---

### 6.3 Create Virtual Environment

```bash
python3.11 -m venv venv
source venv/bin/activate
```

---

### 6.4 Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

---

### 6.5 Create Required Folders

```bash
mkdir -p var/input/traces
mkdir -p var/input/results
mkdir -p var/input/campaign_metadata

mkdir -p var/data/normalized_events
mkdir -p var/data/chunks
mkdir -p var/data/embeddings
mkdir -p var/data/vector_db

mkdir -p var/output/ai_summaries
mkdir -p var/output/root_cause_reports
mkdir -p var/output/campaign_health

mkdir -p var/log
mkdir -p etc
mkdir -p bash_files
```

---

### 6.6 Configure `.env`

Create `.env`:

```env
GLOBALROAMER_AI_ENV=UAT

OPENAI_API_KEY=your_openai_api_key_here

EMBEDDING_MODEL=text-embedding-3-small
LLM_MODEL=gpt-4.1-mini

VECTOR_DB_COLLECTION=globalroamer_traces

CHUNK_SIZE=4000
CHUNK_OVERLAP=400

LOG_LEVEL=INFO
```

---

### 6.7 Configure YAML

Create:

```text
etc/globalroamer_ai_config.yml
```

Example:

```yaml
env: UAT

paths:
  base_dir: /home/<user>/apps/globalroamer_ai_observability

  input_trace_dir: "${base_dir}/var/input/traces"
  input_result_dir: "${base_dir}/var/input/results"
  input_campaign_dir: "${base_dir}/var/input/campaign_metadata"

  normalized_dir: "${base_dir}/var/data/normalized_events"
  chunks_dir: "${base_dir}/var/data/chunks"
  embeddings_dir: "${base_dir}/var/data/embeddings"
  vector_db_dir: "${base_dir}/var/data/vector_db"

  ai_summary_dir: "${base_dir}/var/output/ai_summaries"
  root_cause_dir: "${base_dir}/var/output/root_cause_reports"
  campaign_health_dir: "${base_dir}/var/output/campaign_health"

  log_dir: "${base_dir}/var/log"

ai:
  embedding_model: "text-embedding-3-small"
  llm_model: "gpt-4.1-mini"
  chunk_size: 4000
  chunk_overlap: 400

vector_db:
  provider: "chromadb"
  collection_name: "globalroamer_traces"
  persist_directory: "${base_dir}/var/data/vector_db"

processing:
  supported_trace_extensions:
    - ".csv"
    - ".log"
    - ".txt"

  supported_result_extensions:
    - ".json"
    - ".csv"
    - ".txt"

  save_normalized_json: true
  save_chunks: true

  max_trace_file_size_mb: 200
  max_chunk_count_per_trace: 500

logging:
  level: "INFO"
  rotation_mb: 20
  backup_count: 10

campaign_health:
  degraded_threshold: 0.75
  critical_threshold: 0.50

retry_intelligence:
  min_historical_matches: 3
  low_retry_success_threshold: 0.05
  cooldown_minutes: 30
```

---

## 7. How to Run

### 7.1 Put Input Files

Copy trace files into:

```text
var/input/traces/
```

Example:

```text
var/input/traces/trace_310830767_1.csv
var/input/traces/trace_310830768_1.csv
```

Optional result files:

```text
var/input/results/
```

Optional campaign metadata:

```text
var/input/campaign_metadata/
```

---

### 7.2 Run Ingestion

```bash
python -m globalroamer_ai.ingest_main --config-dir ./etc
```

Expected output:

```text
var/data/normalized_events/trace_310830767_1.csv.json
var/data/chunks/trace_310830767_1.csv_chunks.json
```

---

### 7.3 Run Analysis

```bash
python -m globalroamer_ai.analyze_main --config-dir ./etc --top-k 5
```

Expected output:

```text
var/data/vector_db/
var/output/ai_summaries/similarity_results/
```

---

### 7.4 Generate Reports

```bash
python -m globalroamer_ai.report_main --config-dir ./etc
```

Expected output:

```text
var/output/ai_summaries/ai_summaries.json
var/output/ai_summaries/ai_summaries.md

var/output/root_cause_reports/root_cause_reports.json
var/output/root_cause_reports/root_cause_reports.md

var/output/campaign_health/campaign_health.json
var/output/campaign_health/campaign_health.md

var/output/campaign_health/globalroamer_ai_report.json
var/output/campaign_health/globalroamer_ai_report.md
```

---

### 7.5 Run Full Workflow

```bash
bash bash_files/run_workflow.sh
```

---

## 8. What Happens with 100 Uploaded Trace/Result Files?

If 100 trace files are uploaded:

1. `ingest_main.py` discovers all supported files.
2. Each file is parsed independently.
3. Each file produces:

   * one normalized JSON file;
   * one chunks JSON file.
4. `analyze_main.py` loads all chunks from all files.
5. Embeddings are generated in batches.
6. Chunks are stored in ChromaDB.
7. Similarity search is run per chunk.
8. `report_main.py` generates:

   * AI summaries;
   * root-cause reports;
   * retry recommendations;
   * campaign-level health report.

Example:

```text
100 trace files
≈ 5 chunks per trace
= 500 chunks

500 embeddings
500 similarity searches
500 AI summaries
500 root-cause analyses
500 retry recommendations
1 campaign health report
```

For production, this should be optimized by:

* deduplicating already processed files;
* storing content hashes;
* only embedding new chunks;
* skipping self-similarity results;
* limiting AI summaries to failed/error chunks;
* using async/background workers;
* using batch processing;
* adding job status tracking.

---

## 9. Infrastructure Options

### 9.1 Local Laptop

Good for:

* prototype;
* interview demo;
* small traces;
* 1 user;
* development.

Suggested:

```text
CPU: 4 cores
RAM: 8–16 GB
Disk: 20 GB
Vector DB: local ChromaDB
```

Limitations:

* not good for many users;
* not ideal for large trace history;
* not reliable for scheduled production processing.

---

### 9.2 Small Linux Server

Good for:

* internal tool;
* 1–10 users;
* scheduled batch processing;
* cron-based workflow.

Suggested:

```text
CPU: 4 vCPU
RAM: 16 GB
Disk: 50–100 GB SSD
OS: Ubuntu / Debian / RHEL
Vector DB: ChromaDB local persistent storage
```

---

### 9.3 Production Linux Server

Good for:

* 10–100 users;
* regular trace uploads;
* operational reporting;
* multi-campaign analysis.

Suggested:

```text
CPU: 8–16 vCPU
RAM: 32 GB
Disk: 200 GB SSD
Database: PostgreSQL
Vector DB: Qdrant / pgvector / managed vector DB
Object storage: S3 / MinIO / NFS
Queue: Redis + Celery
```

---

### 9.4 Scaled Production

For 1000 users or large enterprise workloads:

```text
Frontend/API: FastAPI or Django
Workers: Celery / Dramatiq / Kubernetes jobs
Queue: Redis / RabbitMQ
DB: PostgreSQL
Vector DB: Qdrant / Pinecone / pgvector
Storage: S3 / MinIO
Monitoring: Prometheus + Grafana + Loki
Secrets: Vault / CyberArk / cloud secret manager
Deployment: Docker / Kubernetes
```

---

## 10. Cost / Expense Estimates

These are rough estimates and depend heavily on:

* number of trace files;
* average trace size;
* chunk count;
* embedding model;
* LLM model;
* how many summaries are generated;
* how much historical search is performed;
* whether results are cached.

Always verify current provider pricing before production use.

---

### 10.1 Assumptions

Example assumptions:

```text
Average trace file: 100 KB text
Average chunks per trace: 5
Average chunk size: 1,000 tokens
Embedding model: text-embedding-3-small
LLM model: GPT-4.1 mini or similar small model
AI summary/root-cause per failed chunk only
```

---

### 10.2 1 User / Prototype

Usage:

```text
100 trace files / month
500 chunks / month
~500,000 embedding tokens
~100 AI summary/root-cause calls
```

Approximate cost:

```text
Embeddings: very low, usually cents/month
LLM summaries: low, often a few dollars/month depending on output size
Infrastructure: laptop or small VM
```

Recommended infrastructure:

```text
Local laptop or 1 small Linux VM
ChromaDB local
Cron workflow
```

---

### 10.3 100 Users / Internal Team

Usage:

```text
10,000 trace files / month
50,000 chunks / month
~50M embedding tokens
Several thousand AI summary/root-cause calls
```

Approximate cost:

```text
Embeddings: low to moderate
LLM summaries: main cost driver
Infrastructure: small production server or 2–3 services
```

Recommended infrastructure:

```text
8 vCPU / 32 GB RAM Linux VM
PostgreSQL
Qdrant or pgvector
Redis/Celery workers
Object storage for raw files
```

Optimization required:

```text
Only summarize failed/error chunks
Cache AI outputs
Deduplicate traces
Use batch embeddings
Use cheaper model for summaries
Use larger model only for selected root-cause cases
```

---

### 10.4 1000 Users / Enterprise

Usage:

```text
100,000+ trace files / month
500,000+ chunks / month
Hundreds of millions of tokens
High report volume
```

Approximate cost:

```text
Embeddings: still manageable if batched
LLM summaries: significant if every chunk is summarized
Infrastructure: production-grade multi-service deployment
```

Recommended infrastructure:

```text
Kubernetes or multiple Linux workers
PostgreSQL
Qdrant / Pinecone / managed vector DB
S3/MinIO object storage
Redis/RabbitMQ queue
Prometheus/Grafana/Loki monitoring
Rate limits and usage quotas
```

Important:

```text
At this scale, do not run LLM analysis on every chunk.
Use filtering, scoring, caching, and staged analysis.
```

Recommended strategy:

```text
Stage 1: deterministic parser + signal detection
Stage 2: embeddings + similarity
Stage 3: LLM only for important failures
Stage 4: human feedback loop
```

---

## 11. Cost Optimization Strategies

### 11.1 Do Not Send Raw Files Directly to LLM

Bad:

```text
raw 10MB trace → LLM
```

Better:

```text
raw trace → parser → normalized events → relevant chunks → LLM
```

---

### 11.2 Summarize Only Important Chunks

Do not summarize every chunk.

Prioritize:

* chunks with `failure`;
* chunks with `timeout`;
* chunks with `reject`;
* chunks with `authentication`;
* chunks with `critical` or `error` severity.

---

### 11.3 Cache Outputs

Cache by:

```text
file hash
chunk hash
embedding hash
prompt version
model version
```

---

### 11.4 Use Tiered Models

Example:

```text
Embeddings: text-embedding-3-small
Basic summary: small/cheap LLM
Deep root cause: stronger model only when needed
```

---

### 11.5 Use Batch Processing

Batch:

* embeddings;
* reports;
* scheduled jobs;
* cleanup;
* historical backfills.

---

## 12. Tradeoffs

### 12.1 ChromaDB vs Qdrant vs pgvector

#### ChromaDB

Pros:

* simple local development;
* fast prototype;
* no external service needed.

Cons:

* not ideal for large production workloads;
* weaker operational controls.

Best for:

```text
MVP / prototype / laptop demo
```

---

#### Qdrant

Pros:

* production-ready vector DB;
* good filtering;
* scalable;
* Docker-friendly.

Cons:

* separate service to operate.

Best for:

```text
internal production AI observability
```

---

#### pgvector

Pros:

* lives inside PostgreSQL;
* simpler architecture;
* good when metadata matters.

Cons:

* may be less specialized than dedicated vector DBs.

Best for:

```text
small/medium production systems with strong relational metadata
```

---

### 12.2 Deterministic Rules vs LLM

Deterministic rules are better for:

* exact failure detection;
* known telecom patterns;
* repeatable validation;
* compliance-sensitive logic.

LLMs are better for:

* summarization;
* fuzzy pattern explanation;
* similar incident context;
* human-readable operational analysis;
* first-draft root-cause hypotheses.

Best approach:

```text
Deterministic parser + AI explanation layer
```

---

### 12.3 Full Automation vs Human-in-the-Loop

This system should not automatically stop production workflows without control.

Recommended:

```text
AI suggests.
Engineer confirms.
Automation acts only within safe policy.
```

---

## 13. Optimization Concerns

### 13.1 Large Trace Files

Problems:

* memory usage;
* token cost;
* slow parsing;
* noisy chunks.

Solutions:

* streaming parser;
* file size limits;
* chunk by event windows;
* skip low-value lines;
* compress archived traces.

---

### 13.2 Too Many Similarity Searches

Problem:

```text
500 chunks = 500 vector searches
```

Solutions:

* search only failure chunks;
* group by trace;
* search representative chunks;
* cache similarity results.

---

### 13.3 Too Many LLM Calls

Problem:

```text
500 chunks = 500 summaries + 500 root-cause calls
```

Solutions:

* summarize only error/failure chunks;
* aggregate chunks before LLM call;
* generate one report per trace, not per chunk;
* use staged analysis.

---

### 13.4 False Confidence

Problem:

LLM may sound confident even with weak evidence.

Solutions:

* force confidence levels;
* separate evidence from hypothesis;
* cite trace lines;
* require “unknown” when evidence is weak;
* keep engineer approval.

---

## 14. Security and Privacy

Important production concerns:

* do not send sensitive subscriber data unless approved;
* mask MSISDN/IMSI where needed;
* redact credentials;
* avoid storing secrets in code;
* use environment variables or vault;
* restrict raw trace access;
* log only safe metadata;
* apply retention policy.

Recommended future feature:

```text
PII redaction before embedding and LLM calls
```

Possible fields to mask:

```text
MSISDN
IMSI
ICCID
subscriber identifiers
operator-sensitive fields
internal hostnames
credentials
```

---

## 15. Monitoring

The application should expose or log:

* processed trace count;
* failed trace count;
* chunk count;
* embedding count;
* vector DB count;
* AI summary count;
* root-cause report count;
* retry decision distribution;
* campaign health score;
* processing duration;
* API cost estimate;
* error rate.

Current logs:

```text
var/log/ingest.log
var/log/analyze.log
var/log/report.log
var/log/workflow.log
```

Future production monitoring:

```text
Prometheus
Grafana
Loki
ELK
Splunk
NRPE/Nagios checks
```

---

## 16. Example Full Report

Example generated Markdown:

```markdown
# GlobalRoamer AI Observability Report

## Campaign Health

- Health Score: 0.68
- Status: DEGRADED
- Main Issue Cluster: Timeout / network instability pattern
- Recommended Action: Retry after cooldown and monitor whether the same pattern repeats.

## Retry Recommendations

### Chunk: trace_310830767.csv::chunk_2

- Decision: retry_after_cooldown
- Risk Level: medium
- Reason: Possible transient telecom/network instability.
- Cooldown Minutes: 30

## Root-Cause Analysis

Probable root cause:
Network registration instability during LTE attach sequence.

Evidence:
Repeated attach, authentication, timeout, and failure signals.

Confidence:
Medium

What to inspect next:
SIM profile, PLMN configuration, operator-side registration handling.

## AI Summaries

The trace chunk shows instability during the network registration stage with repeated timeout and attach-related signals.
```

---

## 17. Cron Setup

Run workflow every 2 hours:

```bash
crontab -e
```

```cron
0 */2 * * * /home/<user>/apps/globalroamer_ai_observability/bash_files/run_workflow.sh > /dev/null 2>&1
```

Cleanup every night:

```cron
30 3 * * * /home/<user>/apps/globalroamer_ai_observability/bash_files/cleanup_folders.sh > /dev/null 2>&1
```

---

## 18. Possible Enhancements

### 18.1 Web UI

Add FastAPI or Django UI:

* upload traces;
* browse campaigns;
* view AI summaries;
* inspect root-cause reports;
* compare similar incidents.

---

### 18.2 API Service

Expose endpoints:

```text
POST /analyze-trace
GET /campaign-health/{campaign_id}
GET /similar-incidents/{trace_id}
GET /retry-advice/{trace_id}
```

---

### 18.3 Background Workers

Use:

```text
Celery + Redis
```

For:

* async ingestion;
* embedding jobs;
* AI report generation;
* scheduled cleanup.

---

### 18.4 Metadata Database

Add PostgreSQL tables:

```text
traces
chunks
embeddings
similarity_results
ai_summaries
root_cause_reports
retry_recommendations
campaign_health_reports
```

---

### 18.5 PII Redaction

Before embeddings and LLM calls:

```text
+32477653925 → <MSISDN>
206012240120059 → <IMSI>
```

---

### 18.6 Human Feedback Loop

Allow engineers to mark:

```text
root cause correct / incorrect
retry advice useful / not useful
false positive / true issue
```

This feedback can improve future scoring.

---

### 18.7 Advanced AI Agents

Future agent workflow:

```text
Incident Agent
    ↓
Similarity Agent
    ↓
Root Cause Agent
    ↓
Retry Policy Agent
    ↓
Campaign Health Agent
    ↓
Engineer Report
```

---

## 19. Limitations

Current MVP limitations:

* not a replacement for telecom engineers;
* not a deterministic root-cause engine;
* depends on trace quality;
* similarity search quality depends on chunking;
* LLM output must be reviewed;
* cost can grow if every chunk is analyzed;
* ChromaDB is suitable for MVP but not ideal for large enterprise scale.

---

## 20. Positioning

This project is an example of applying AI to real operational engineering systems.

It combines:

* backend/platform engineering;
* telecom workflow orchestration;
* observability;
* trace processing;
* RAG;
* embeddings;
* vector search;
* AI-assisted diagnostics;
* operational reporting.

The main engineering idea:

```text
AI becomes most useful when integrated into real operational workflows,
not when used as an isolated chatbot.
```

---

## 21. Developer Notes

Recommended development loop:

```bash
python -m globalroamer_ai.ingest_main --config-dir ./etc
python -m globalroamer_ai.analyze_main --config-dir ./etc --top-k 5
python -m globalroamer_ai.report_main --config-dir ./etc
```

Check logs:

```bash
tail -f var/log/ingest.log
tail -f var/log/analyze.log
tail -f var/log/report.log
```

Check outputs:

```bash
ls -la var/data/normalized_events/
ls -la var/data/chunks/
ls -la var/output/campaign_health/
```

---

## 22. Final Goal

The long-term vision is to evolve this prototype into an AI-powered telecom observability and workflow intelligence platform that helps engineers:

* understand failures faster;
* reduce useless retries;
* detect recurring operator issues;
* compare incidents semantically;
* improve campaign visibility;
* generate operational reports automatically;
* move from raw trace inspection to AI-assisted diagnostics.

```
```
