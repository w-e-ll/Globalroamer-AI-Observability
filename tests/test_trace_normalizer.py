from datetime import datetime

from globalroamer_ai.ingestion.trace_normalizer import TraceNormalizer
from globalroamer_ai.models.operational_models import ParsedEvidence, ParsedTrace, SourceArtifact


def test_trace_normalizer_converts_evidence_to_operational_event():
    source = SourceArtifact(
        testcase_id="123",
        trace_path="trace_123_0.csv",
        result_path=None,
        report_type="operational_trace",
        group="globalroamer",
    )

    evidence = ParsedEvidence(
        evidence_type="failure",
        category="failure_signal",
        value="FAIL",
        confidence=0.8,
        source_line="2026-06-26 04:57:28.413;0;;PRS;TSP_LupErrorVerdict;TSP_LupErrorVerdict = 'FAIL'",
        protocol_layer=None,
        event_code=None,
        metric_name=None,
        severity="medium",
        timestamp=datetime(2026, 6, 26, 4, 57, 28, 413000),
        metadata={"event": "PRS", "type": "TSP_LupErrorVerdict"},
    )

    parsed = ParsedTrace(
        source=source,
        extracted_values={"operator": "mobily", "country": "sa"},
        evidences=[evidence],
        raw_signals=[evidence.source_line],
        parser_errors=[],
    )

    events = TraceNormalizer().normalize(parsed)

    assert len(events) == 1
    event = events[0]

    assert event.testcase_id == "123"
    assert event.event_name == "FAILURE_SIGNAL"
    assert event.event_family == "failure"
    assert event.result == "failed"
    assert event.operator == "mobily"
    assert event.country == "sa"
    assert "failure_signal" in event.tags
