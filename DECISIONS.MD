# DECISIONS.md

# GlobalRoamer AI Observability Layer
## Architectural Decisions and Tradeoffs

---

# 1. Why Streamlit instead of React/FastAPI frontend?

## Decision
Use Streamlit for the investigation UI and operational dashboard.

## Reasoning
The primary goal of this platform is rapid operational investigation and AI-assisted diagnostics rather than public-facing SaaS delivery.

Streamlit allowed:
- extremely fast iteration
- low frontend complexity
- integrated Python-native analytics
- direct rendering of AI outputs
- minimal deployment overhead

## Tradeoff
Pros:
- very fast prototyping
- small codebase
- excellent for internal tooling
- ideal for AI/data workflows

Cons:
- limited frontend flexibility
- less scalable for large multi-user SaaS
- not ideal for enterprise RBAC/frontend ecosystems

## Future
A future production architecture could separate:
- FastAPI backend
- React frontend
- async workers

---

# 2. Why local ChromaDB instead of managed vector database?

## Decision
Use local ChromaDB for embeddings and similarity search.

## Reasoning
The platform currently operates as:
- local investigation tool
- internal operational AI assistant
- low-scale AI observability platform

Local vector storage simplifies:
- setup
- portability
- offline execution
- demo environments

## Tradeoff
Pros:
- zero infrastructure dependency
- low operational cost
- simple local experimentation

Cons:
- limited scalability
- weaker multi-user concurrency
- limited distributed indexing

## Future
Potential migration targets:
- pgvector
- Qdrant
- Pinecone
- Weaviate

---

# 3. Why batch-oriented processing instead of streaming?

## Decision
Use staged batch execution:
1. ingest
2. analyze
3. report

## Reasoning
Telecom traces are naturally large operational artifacts.
The investigation workflow is analyst-driven rather than real-time user-facing.

Batch processing simplifies:
- reproducibility
- debugging
- report generation
- operational replay

## Tradeoff
Pros:
- deterministic processing
- easier troubleshooting
- simpler orchestration

Cons:
- increased latency
- not real-time

## Future
Streaming/event-driven ingestion could be introduced via:
- Kafka
- Redis Streams
- async workers

---

# 4. Why filesystem-based artifacts instead of database persistence?

## Decision
Store normalized events, chunks, reports, and AI outputs as files.

## Reasoning
Operational investigations benefit from:
- inspectable artifacts
- reproducibility
- portability
- easy debugging

Filesystem storage also reduces operational complexity.

## Tradeoff
Pros:
- transparent debugging
- easy exports
- lightweight architecture

Cons:
- weaker querying capabilities
- limited concurrent access
- manual retention management

## Future
Long-term persistence may move into:
- PostgreSQL
- Elasticsearch/OpenSearch
- object storage

---

# 5. Why modular domain separation?

## Decision
Split the system into:
- ingestion
- ai
- reports
- ui
- core
- models

## Reasoning
The platform evolved from a single operational pipeline into an AI-assisted observability system.

Separation by domain value improves:
- maintainability
- extensibility
- ownership boundaries
- onboarding

## Tradeoff
Pros:
- clear architecture
- easier scaling
- cleaner imports
- better testing

Cons:
- slightly more boilerplate
- additional package boundaries

---

# 6. Why AI-assisted investigation instead of deterministic-only rules?

## Decision
Combine:
- deterministic normalization
- event extraction
- AI summarization
- similarity search
- root-cause heuristics

## Reasoning
Telecom operational traces often contain:
- incomplete failures
- ambiguous signals
- vendor-specific patterns
- noisy diagnostics

AI assistance improves:
- investigation speed
- operator guidance
- operational summarization
- historical correlation

## Tradeoff
Pros:
- better operational context
- faster triage
- richer diagnostics

Cons:
- probabilistic outputs
- hallucination risk
- confidence management required

## Mitigations
- deterministic normalization first
- explicit confidence indicators
- raw evidence visibility
- investigation traceability

---

# 7. Why PowerShell orchestration on Windows?

## Decision
Use PowerShell workflow orchestration for local development/demo.

## Reasoning
The current environment is Windows-native.
Avoiding WSL dependencies simplifies:
- onboarding
- execution
- portability

## Future
Linux shell orchestration and containerized deployment remain possible for production environments.

---

# 8. Why markdown reports?

## Decision
Generate Markdown-based investigation reports.

## Reasoning
Markdown is:
- lightweight
- portable
- Git-friendly
- easy to render in Streamlit

## Future
Additional exports may include:
- HTML
- PDF
- operational ticket integration
- SIEM integrations

---

# Summary

The platform prioritizes:
- operational transparency
- investigation speed
- AI-assisted diagnostics
- modular architecture
- low operational complexity
- reproducible workflows

Current architecture is optimized for:
- internal telecom observability
- AI-assisted troubleshooting
- rapid operational investigations
- demo and prototype scalability

while preserving a migration path toward larger distributed architectures.
