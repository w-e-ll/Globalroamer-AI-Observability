from pathlib import Path

from globalroamer_ai.ingestion.trace_parser import TraceParser
from globalroamer_ai.models.operational_models import SourceArtifact


def test_trace_parser_extracts_failure_and_retry_evidences(tmp_path: Path):
    trace_file = tmp_path / "trace_123_0.csv"
    trace_file.write_text(
        "Timestamp;CallId;Ptc;Event;Type;Information\n"
        "2026-06-26 04:57:28.413;0;PTC_A;PRS;TSP_LupErrorVerdict;TSP_LupErrorVerdict = 'FAIL'\n"
        "2026-06-26 04:57:28.413;0;PTC_A;PRS;TSP_SipRetryBehavior;TSP_SipRetryBehavior = 'site'\n"
        "2026-06-26 04:58:00.886;1;PTC_A;TLM;;received QMI NAS_SERVSYS_INFO-IND: RegistrationState NASNotRegistered\n",
        encoding="utf-8",
    )

    source = SourceArtifact(
        testcase_id="123",
        trace_path=str(trace_file),
        result_path=None,
        report_type="operational_trace",
        group="globalroamer",
    )

    parsed = TraceParser().parse(source)

    assert parsed.source.testcase_id == "123"
    assert len(parsed.evidences) >= 3

    categories = {e.category for e in parsed.evidences}
    assert "failure_signal" in categories
    assert "retry_detected" in categories
    assert "nas_not_registered" in categories

    assert parsed.raw_signals
