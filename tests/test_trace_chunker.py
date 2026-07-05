from globalroamer_ai.ingestion.trace_chunker import chunk_normalized_trace


def test_chunk_normalized_trace_builds_chunks_from_events():
    normalized_trace = {
        "testcase_id": "123",
        "trace_id": "123",
        "source_file": "trace_123_0.csv",
        "normalized_events": [
            {
                "testcase_id": "123",
                "event_id": "123-0001",
                "timestamp": "2026-06-26 04:57:28.413000",
                "event_family": "failure",
                "event_name": "FAILURE_SIGNAL",
                "severity": "medium",
                "result": "failed",
                "operator": "mobily",
                "country": "sa",
                "network_domain": "unknown",
                "workflow_stage": "trace_analysis",
                "cause": None,
                "retry_recommended": False,
                "recommendation": None,
                "normalized_message": "FAILURE_SIGNAL detected",
                "tags": ["failure", "failure_signal", "medium"],
                "metadata": {"evidence_value": "FAIL"},
                "raw_message": "raw line",
            }
        ],
    }

    chunks = chunk_normalized_trace(normalized_trace, chunk_size=2000, chunk_overlap=200)

    assert len(chunks) == 1

    chunk = chunks[0]
    assert chunk["testcase_id"] == "123"
    assert chunk["event_count"] == 1
    assert "FAILURE_SIGNAL" in chunk["event_names"]
    assert chunk["has_failure"] is True
    assert "FAILURE_SIGNAL" in chunk["text"]
