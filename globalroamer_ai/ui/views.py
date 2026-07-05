from __future__ import annotations

import streamlit as st

from pathlib import Path
from typing import Any

from globalroamer_ai.core.app_config import load_yaml_config
from globalroamer_ai.ui.log_reader import LogReader
from globalroamer_ai.ui.pipeline_runner import PipelineRunner, PipelineResult
from globalroamer_ai.ui.result_loader import ResultLoader


def render_dashboard() -> None:
    st.set_page_config(
        page_title="GlobalRoamer AI Observability",
        layout="wide",
    )

    st.title("GlobalRoamer AI Observability Layer")

    state = render_sidebar()

    loader = ResultLoader(state["project_root"])
    log_reader = LogReader(Path(state["project_root"]) / "var" / "log")
    runner = PipelineRunner(state["project_root"])

    tab_control, tab_logs, tab_testcases, tab_reports = st.tabs(
        [
            "Control Center",
            "Live Logs",
            "Testcases",
            "Reports",
        ]
    )

    with tab_control:
        render_control_center(state, runner, loader)

    with tab_logs:
        render_logs(log_reader)

    with tab_testcases:
        render_testcases(loader)

    with tab_reports:
        render_reports(loader)


def render_sidebar() -> dict[str, Any]:
    project_root = Path.cwd()

    st.sidebar.header("Configuration")

    config_dir = st.sidebar.text_input("Config dir", value="etc")
    max_chunks_value = st.sidebar.text_input("Max chunks", value="20")

    skip_ai = st.sidebar.checkbox("Skip AI summaries", value=False)
    skip_embedding = st.sidebar.checkbox("Skip embeddings", value=True)
    skip_similarity = st.sidebar.checkbox("Skip similarity", value=True)

    auto_refresh_logs = st.sidebar.checkbox("Auto refresh logs", value=False)
    log_lines = st.sidebar.slider(
        "Log lines",
        min_value=50,
        max_value=1000,
        value=300,
        step=50,
    )

    try:
        max_chunks = int(max_chunks_value) if max_chunks_value.strip() else None
    except ValueError:
        max_chunks = 20

    cfg = None

    try:
        cfg = load_yaml_config(config_dir)
        st.sidebar.success(f"Environment: {cfg.env}")
    except Exception as exc:
        st.sidebar.error(f"Config load failed: {exc}")

    return {
        "project_root": project_root,
        "config_dir": config_dir,
        "max_chunks": max_chunks,
        "skip_ai": skip_ai,
        "skip_embedding": skip_embedding,
        "skip_similarity": skip_similarity,
        "auto_refresh_logs": auto_refresh_logs,
        "log_lines": log_lines,
        "cfg": cfg,
    }


def render_control_center(
    state: dict[str, Any],
    runner: PipelineRunner,
    loader: ResultLoader,
) -> None:
    st.subheader("Pipeline Control Center")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if st.button("Run Ingest", width="stretch"):
            result = runner.run_ingest(config_dir=state["config_dir"])
            render_pipeline_result(result)

    with col2:
        if st.button("Run Analyze", width="stretch"):
            result = runner.run_analyze(
                config_dir=state["config_dir"],
                skip_embedding=state["skip_embedding"],
                skip_similarity=state["skip_similarity"],
            )
            render_pipeline_result(result)

    with col3:
        if st.button("Run Report", width="stretch"):
            result = runner.run_report(
                config_dir=state["config_dir"],
                max_chunks=state["max_chunks"],
                skip_ai=state["skip_ai"],
            )
            render_pipeline_result(result)

    with col4:
        if st.button("Run Full Pipeline", width="stretch"):
            results = runner.run_full_pipeline(
                config_dir=state["config_dir"],
                max_chunks=state["max_chunks"],
                skip_embedding=state["skip_embedding"],
                skip_similarity=state["skip_similarity"],
                skip_ai=state["skip_ai"],
            )
            for result in results:
                render_pipeline_result(result)

    overview = loader.testcase_overview()
    chunks = loader.load_chunks()
    events = loader.load_events()
    summaries = loader.load_ai_summaries()

    st.divider()

    failures = sum(1 for event in events if is_failure_event(event))
    retries = sum(1 for event in events if is_retry_event(event))
    high_severity = sum(1 for event in events if event.get("severity") == "high")

    metric1, metric2, metric3, metric4, metric5, metric6 = st.columns(6)
    metric1.metric("Testcases", len(overview))
    metric2.metric("Events", len(events))
    metric3.metric("Failures", failures)
    metric4.metric("Retries", retries)
    metric5.metric("High Severity", high_severity)
    metric6.metric("AI Summaries", len(summaries))

    if overview:
        st.subheader("Operational Overview")
        st.dataframe(overview, width="stretch", hide_index=True)


def render_pipeline_result(result: PipelineResult) -> None:
    if result.success:
        st.success(f"Finished successfully: {' '.join(result.command)}")
    else:
        st.error(
            f"Failed with return code {result.return_code}: "
            f"{' '.join(result.command)}"
        )

    if result.stdout:
        with st.expander("stdout"):
            st.code(result.stdout)

    if result.stderr:
        with st.expander("stderr"):
            st.code(result.stderr)


def render_logs(log_reader: LogReader) -> None:
    st.subheader("Live Logs")

    logs = log_reader.list_logs()

    if not logs:
        st.warning("No log files found")
        return

    selected_log = st.selectbox("Log file", logs, index=0)
    lines = st.slider(
        "Lines",
        min_value=50,
        max_value=2000,
        value=300,
        step=50,
    )

    if st.button("Refresh logs", width="stretch"):
        st.rerun()

    log_text = log_reader.tail(selected_log, lines=lines)
    st.code(log_text, language="text")


def render_testcases(loader: ResultLoader) -> None:
    st.subheader("Testcase Explorer")

    overview = loader.testcase_overview()

    if not overview:
        st.warning("No testcase data found. Run ingest and analyze first.")
        return

    st.dataframe(overview, width="stretch", hide_index=True)

    testcase_ids = [item["testcase_id"] for item in overview]
    selected_testcase = st.selectbox("Select testcase", testcase_ids)

    events = loader.testcase_events(selected_testcase)
    chunks = loader.testcase_chunks(selected_testcase)
    summaries = loader.testcase_summaries(selected_testcase)

    (
        tab_investigation,
        tab_events,
        tab_chunks,
        tab_summaries,
    ) = st.tabs(
        [
            "Investigation View",
            "Operational Events",
            "Chunks",
            "AI Summaries",
        ]
    )

    with tab_investigation:
        render_investigation_view(
            testcase_id=selected_testcase,
            events=events,
            chunks=chunks,
            summaries=summaries,
        )

    with tab_events:
        render_events(events)

    with tab_chunks:
        render_chunks(chunks)

    with tab_summaries:
        render_summaries(summaries)


def render_investigation_view(
    testcase_id: str,
    events: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
) -> None:
    st.subheader(f"Investigation View: {testcase_id}")

    if not events and not chunks:
        st.warning("No investigation data found for this testcase")
        return

    failed_events = [event for event in events if is_failure_event(event)]
    retry_events = [event for event in events if is_retry_event(event)]
    timeout_events = [
        event
        for event in events
        if event.get("event_name") == "TIMEOUT"
        or event.get("cause") == "TIMEOUT"
        or event.get("event_family") == "timing"
    ]
    high_events = [event for event in events if event.get("severity") == "high"]

    operator = first_value(events, "operator") or first_chunk_value(chunks, "operators")
    country = first_value(events, "country") or first_chunk_value(chunks, "countries")
    main_failure = first_non_empty([event.get("event_name") for event in failed_events])
    main_cause = first_non_empty([event.get("cause") for event in events])
    recommended_action = first_non_empty(
        [event.get("recommendation") for event in events]
    )

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Operator", operator or "unknown")
    col2.metric("Country", country or "unknown")
    col3.metric("Failures", len(failed_events))
    col4.metric("Retry Signals", len(retry_events))
    col5.metric("Timeouts", len(timeout_events))

    st.markdown("### Operational Diagnosis")

    diag1, diag2, diag3 = st.columns(3)

    with diag1:
        st.markdown("#### Problem")
        st.info(build_problem_text(main_failure, main_cause, operator, country, high_events))

    with diag2:
        st.markdown("#### Likely Cause")
        st.warning(build_cause_text(main_cause, failed_events, timeout_events))

    with diag3:
        st.markdown("#### Recommended Action")
        st.success(recommended_action or default_recommendation(events, chunks))

    render_failure_distribution(events)

    st.markdown("### Evidence Timeline")
    render_investigation_timeline(events)

    st.markdown("### AI Investigation Summary")
    render_compact_ai_summary(summaries)

    st.markdown("### Similar / Important Chunks")
    render_important_chunks(chunks)

    st.markdown("### Raw Evidence")
    render_raw_evidence(events)

    st.markdown("### Next Checks")
    render_recommendations(events)


def render_failure_distribution(events: list[dict[str, Any]]) -> None:
    if not events:
        return

    families = count_values(events, "event_family")
    names = count_values(events, "event_name")
    severities = count_values(events, "severity")
    causes = count_values(events, "cause")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### Event Families")
        st.dataframe(to_rows(families), width="stretch", hide_index=True)

    with col2:
        st.markdown("#### Event Names")
        st.dataframe(to_rows(names), width="stretch", hide_index=True)

    with col3:
        st.markdown("#### Severities")
        st.dataframe(to_rows(severities), width="stretch", hide_index=True)

    with col4:
        st.markdown("#### Causes")
        st.dataframe(to_rows(causes), width="stretch", hide_index=True)


def render_investigation_timeline(events: list[dict[str, Any]]) -> None:
    if not events:
        st.warning("No event timeline available")
        return

    timeline_rows = []

    for event in events:
        timeline_rows.append(
            {
                "timestamp": event.get("timestamp"),
                "event_name": event.get("event_name"),
                "family": event.get("event_family"),
                "severity": event.get("severity"),
                "cause": event.get("cause"),
                "retry": event.get("retry_recommended"),
                "message": short_text(event.get("normalized_message"), 180),
            }
        )

    st.dataframe(timeline_rows, width="stretch", hide_index=True)


def render_compact_ai_summary(summaries: list[dict[str, Any]]) -> None:
    if not summaries:
        st.warning("No AI summaries available. Run report with AI enabled.")
        return

    selected = st.selectbox(
        "Select AI summary",
        [summary.get("chunk_id", f"summary_{index}") for index, summary in enumerate(summaries)],
    )

    for summary in summaries:
        if summary.get("chunk_id") == selected:
            st.markdown(summary.get("summary", ""))
            with st.expander("AI summary JSON"):
                st.json(summary)
            return


def render_important_chunks(chunks: list[dict[str, Any]]) -> None:
    important_chunks = [
        chunk
        for chunk in chunks
        if chunk.get("has_failure")
        or chunk.get("has_high_severity")
        or chunk.get("has_retry_recommended")
    ]

    if not important_chunks:
        st.warning("No important chunks detected")
        return

    chunk_rows = []

    for chunk in important_chunks:
        chunk_rows.append(
            {
                "chunk_id": chunk.get("chunk_id"),
                "event_count": chunk.get("event_count"),
                "events": ", ".join(chunk.get("event_names", [])),
                "families": ", ".join(chunk.get("event_families", [])),
                "causes": ", ".join(chunk.get("causes", [])),
                "failure": chunk.get("has_failure"),
                "high": chunk.get("has_high_severity"),
                "retry": chunk.get("has_retry_recommended"),
            }
        )

    st.dataframe(chunk_rows, width="stretch", hide_index=True)

    selected_chunk = st.selectbox(
        "Inspect chunk",
        [chunk.get("chunk_id") for chunk in important_chunks],
    )

    for chunk in important_chunks:
        if chunk.get("chunk_id") == selected_chunk:
            st.code(chunk.get("text", ""), language="text")
            with st.expander("Chunk JSON"):
                st.json(chunk)
            break


def render_raw_evidence(events: list[dict[str, Any]]) -> None:
    raw_lines = []

    for event in events:
        raw_message = event.get("raw_message") or event.get("raw") or event.get("source_line")
        if raw_message:
            raw_lines.append(str(raw_message))

    if not raw_lines:
        st.warning("No raw evidence lines available")
        return

    selected_mode = st.radio(
        "Raw evidence mode",
        ["Important only", "All"],
        horizontal=True,
    )

    if selected_mode == "Important only":
        important_lines = [
            line
            for line in raw_lines
            if any(
                token.lower() in line.lower()
                for token in [
                    "fail",
                    "failed",
                    "failure",
                    "reject",
                    "timeout",
                    "retry",
                    "notregistered",
                    "detached",
                    "plmn",
                    "locationupdate",
                ]
            )
        ]
        raw_lines = important_lines or raw_lines[:50]

    st.code("\n".join(raw_lines[:200]), language="text")


def render_recommendations(events: list[dict[str, Any]]) -> None:
    recommendations = collect_recommendations(events)

    if recommendations:
        for recommendation in recommendations:
            st.write(f"- {recommendation}")
        return

    st.write("- Check RES/Error fields.")
    st.write("- Check MM Location Update request/reject sequence.")
    st.write("- Check NAS registration and attach state.")
    st.write("- Compare with similar historical incidents.")
    st.write("- Validate HPLMN/VPLMN roaming configuration.")
    st.write("- Check retry count, timeout thresholds and escalation policy.")


def render_events(events: list[dict[str, Any]]) -> None:
    if not events:
        st.warning("No events found for this testcase")
        return

    st.metric("Events", len(events))

    timeline = []

    for event in events:
        timeline.append(
            {
                "timestamp": event.get("timestamp"),
                "event_name": event.get("event_name"),
                "family": event.get("event_family"),
                "severity": event.get("severity"),
                "result": event.get("result"),
                "cause": event.get("cause"),
                "retry": event.get("retry_recommended"),
                "recommendation": event.get("recommendation"),
            }
        )

    st.dataframe(timeline, width="stretch", hide_index=True)

    with st.expander("Raw event JSON"):
        st.json(events)


def render_chunks(chunks: list[dict[str, Any]]) -> None:
    if not chunks:
        st.warning("No chunks found for this testcase")
        return

    st.metric("Chunks", len(chunks))

    chunk_rows = []

    for chunk in chunks:
        chunk_rows.append(
            {
                "chunk_id": chunk.get("chunk_id"),
                "event_count": chunk.get("event_count"),
                "families": ", ".join(chunk.get("event_families", [])),
                "events": ", ".join(chunk.get("event_names", [])),
                "causes": ", ".join(chunk.get("causes", [])),
                "has_failure": chunk.get("has_failure"),
                "has_high_severity": chunk.get("has_high_severity"),
                "has_retry_recommended": chunk.get("has_retry_recommended"),
            }
        )

    st.dataframe(chunk_rows, width="stretch", hide_index=True)

    selected_chunk = st.selectbox(
        "Select chunk",
        [chunk.get("chunk_id") for chunk in chunks],
    )

    for chunk in chunks:
        if chunk.get("chunk_id") == selected_chunk:
            st.subheader(selected_chunk)
            st.code(chunk.get("text", ""), language="text")
            with st.expander("Chunk JSON"):
                st.json(chunk)
            break


def render_summaries(summaries: list[dict[str, Any]]) -> None:
    if not summaries:
        st.warning("No AI summaries found for this testcase")
        return

    st.metric("AI Summaries", len(summaries))

    selected_summary = st.selectbox(
        "Select summary",
        [summary.get("chunk_id") for summary in summaries],
    )

    for summary in summaries:
        if summary.get("chunk_id") == selected_summary:
            st.markdown(summary.get("summary", ""))
            with st.expander("Summary JSON"):
                st.json(summary)
            break


def render_reports(loader: ResultLoader) -> None:
    st.subheader("Generated Reports")

    markdown_reports = loader.load_markdown_reports()
    campaign_health = loader.load_campaign_health()
    root_cause = loader.load_root_cause_report()

    if markdown_reports:
        selected_report = st.selectbox("Markdown report", list(markdown_reports.keys()))
        st.markdown(markdown_reports[selected_report])
    else:
        st.warning("No markdown reports found")

    col1, col2 = st.columns(2)

    with col1:
        with st.expander("Campaign Health JSON"):
            st.json(campaign_health)

    with col2:
        with st.expander("Root Cause JSON"):
            st.json(root_cause)


def is_failure_event(event: dict[str, Any]) -> bool:
    return (
        event.get("result") == "failed"
        or event.get("event_family") == "failure"
        or "fail" in str(event.get("event_name", "")).lower()
        or "reject" in str(event.get("event_name", "")).lower()
    )


def is_retry_event(event: dict[str, Any]) -> bool:
    return (
        bool(event.get("retry_recommended"))
        or event.get("event_family") == "retry"
        or "retry" in str(event.get("event_name", "")).lower()
        or "retry" in str(event.get("cause", "")).lower()
    )


def first_value(items: list[dict[str, Any]], key: str) -> Any:
    for item in items:
        value = item.get(key)
        if value not in [None, "", [], {}]:
            return value
    return None


def first_chunk_value(chunks: list[dict[str, Any]], key: str) -> Any:
    for chunk in chunks:
        values = chunk.get(key)

        if isinstance(values, list) and values:
            return values[0]

        if values:
            return values

    return None


def first_non_empty(values: list[Any]) -> Any:
    for value in values:
        if value not in [None, "", [], {}]:
            return value
    return None


def build_problem_text(
    main_failure: Any,
    main_cause: Any,
    operator: Any,
    country: Any,
    high_events: list[dict[str, Any]],
) -> str:
    severity = "high" if high_events else "medium"

    return (
        f"Detected {severity} operational issue for "
        f"operator={operator or 'unknown'}, country={country or 'unknown'}. "
        f"Main failure={main_failure or 'unknown'}. "
        f"Cause={main_cause or 'not extracted yet'}."
    )


def build_cause_text(
    main_cause: Any,
    failed_events: list[dict[str, Any]],
    timeout_events: list[dict[str, Any]],
) -> str:
    if main_cause:
        return f"Main detected cause: {main_cause}"

    if timeout_events:
        return "Timeout pattern detected. Check network stability, transport delay, radio conditions and retry policy."

    if failed_events:
        return "Failure signals detected, but exact cause is not extracted yet. Inspect raw trace around failed events."

    return "No clear failure cause detected yet."


def default_recommendation(
    events: list[dict[str, Any]],
    chunks: list[dict[str, Any]],
) -> str:
    has_retry = any(is_retry_event(event) for event in events)
    has_timeout = any(
        event.get("event_name") == "TIMEOUT" or event.get("cause") == "TIMEOUT"
        for event in events
    )
    has_failure = any(is_failure_event(event) for event in events)

    if has_timeout:
        return "Check timeout thresholds, network stability, signaling delay and retry behavior."

    if has_retry:
        return "Compare retry count with historical successful retries before escalation."

    if has_failure:
        return "Inspect failed trace lines and compare with similar incidents."

    if chunks:
        return "Review important chunks and similar historical patterns."

    return "No immediate action detected."


def collect_recommendations(events: list[dict[str, Any]]) -> list[str]:
    recommendations = []

    for event in events:
        recommendation = event.get("recommendation")

        if recommendation and recommendation not in recommendations:
            recommendations.append(recommendation)

    return recommendations[:10]


def count_values(items: list[dict[str, Any]], key: str) -> dict[str, int]:
    result: dict[str, int] = {}

    for item in items:
        value = item.get(key)

        if value in [None, "", [], {}]:
            continue

        value = str(value)
        result[value] = result.get(value, 0) + 1

    return dict(sorted(result.items(), key=lambda pair: pair[1], reverse=True))


def to_rows(counts: dict[str, int]) -> list[dict[str, Any]]:
    return [{"value": key, "count": value} for key, value in counts.items()]


def short_text(value: Any, limit: int = 160) -> str:
    text = "" if value is None else str(value)

    if len(text) <= limit:
        return text

    return text[:limit] + "..."
