from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


@dataclass
class SourceArtifact:
    testcase_id: str
    trace_path: str | None = None
    result_path: str | None = None
    report_path: str | None = None
    template_path: str | None = None
    campaign_name: str | None = None
    template_name: str | None = None
    report_type: str | None = None
    group: str | None = None
    test_user: str | None = None
    index: int | None = None
    time_change: str = "0"
    created_at: datetime | None = None


@dataclass
class ParsedEvidence:
    evidence_type: str
    category: str
    value: str | int | float | None
    confidence: float
    source_line: str
    protocol_layer: str | None = None
    event_code: str | None = None
    metric_name: str | None = None
    severity: str | None = None
    timestamp: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ParsedTrace:
    source: SourceArtifact
    extracted_values: dict[str, Any]
    evidences: list[ParsedEvidence] = field(default_factory=list)
    raw_signals: list[str] = field(default_factory=list)
    parser_errors: list[str] = field(default_factory=list)


@dataclass
class ParsedResultLog:
    source: SourceArtifact
    base_url: str | None = None
    http_statuses: list[int] = field(default_factory=list)
    request_count: int = 0
    response_count: int = 0
    evidences: list[ParsedEvidence] = field(default_factory=list)
    parser_errors: list[str] = field(default_factory=list)


@dataclass
class ParsedExcelReport:
    source: SourceArtifact
    testcase_name: str | None = None
    final_result: str | None = None
    kpis: dict[str, Any] = field(default_factory=dict)
    evidences: list[ParsedEvidence] = field(default_factory=list)
    parser_errors: list[str] = field(default_factory=list)


@dataclass
class OperationalEvent:
    testcase_id: str
    event_id: str
    timestamp: datetime | None
    event_family: str
    protocol_layer: str
    event_name: str
    severity: str
    raw_message: str
    normalized_message: str
    direction: str | None = None
    workflow_stage: str | None = None
    network_domain: str | None = None
    operator: str | None = None
    country: str | None = None
    result: str | None = None
    cause: str | None = None
    source_trace: str | None = None
    extracted_values: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    evidences: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class RetryPattern:
    testcase_id: str
    retry_count: int
    retry_reason: str | None = None
    transient_probability: float | None = None
    escalation_required: bool = False
    evidence: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class IncidentSignature:
    signature_id: str
    testcase_id: str
    title: str
    category: str
    symptoms: list[str]
    probable_causes: list[str]
    known_fix_patterns: list[str] = field(default_factory=list)
    confidence: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class SimilarIncident:
    testcase_id: str
    similarity_score: float
    matching_patterns: list[str]
    known_resolution: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class CampaignHealth:
    campaign_name: str | None
    total_tests: int
    passed: int
    failed: int
    unstable: int
    dominant_failures: list[str]
    recurring_patterns: list[str]
    affected_operators: list[str]
    affected_countries: list[str]
    health_score: float
    status: str
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class NormalizedCase:
    testcase_id: str
    source: SourceArtifact
    trace: ParsedTrace | None = None
    result_log: ParsedResultLog | None = None
    excel_report: ParsedExcelReport | None = None
    events: list[OperationalEvent] = field(default_factory=list)
    retry_patterns: list[RetryPattern] = field(default_factory=list)
    incident_signatures: list[IncidentSignature] = field(default_factory=list)
    similar_incidents: list[SimilarIncident] = field(default_factory=list)
    campaign_health: CampaignHealth | None = None
    final_rca: str | None = None
    ai_summary: str | None = None
    escalation_required: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
