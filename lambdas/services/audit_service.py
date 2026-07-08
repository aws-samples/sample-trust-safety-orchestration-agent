import logging
from datetime import datetime, timezone

from repositories import audit_repository

logger = logging.getLogger(__name__)


def log_enforcement_action(
    case_id: str,
    user_id: str,
    action: str,
    violation_type: str,
    confidence_score: float,
    decision_source: str,
    reasoning: str,
    jurisdiction_code: str | None = None,
    response_time_ms: int | None = None,
) -> str:
    return audit_repository.write_log(
        event_type="enforcement",
        action=action,
        case_id=case_id,
        user_id=user_id,
        violation_type=violation_type,
        confidence_score=confidence_score,
        decision_source=decision_source,
        reasoning=reasoning,
        jurisdiction_code=jurisdiction_code,
        response_time_ms=response_time_ms,
    )


def log_config_change(
    admin_id: str,
    config_key: str,
    previous_value,
    new_value,
) -> str:
    return audit_repository.write_log(
        event_type="config_change",
        action="update_config",
        admin_id=admin_id,
        previous_value=previous_value if isinstance(previous_value, dict) else {"value": previous_value},
        new_value=new_value if isinstance(new_value, dict) else {"value": new_value},
        reasoning=f"Config '{config_key}' updated by {admin_id}",
    )


def log_detection_event(
    user_id: str,
    anomaly_type: str,
    score: float,
    threshold: float,
) -> str:
    return audit_repository.write_log(
        event_type="detection",
        action=f"anomaly_{anomaly_type}",
        user_id=user_id,
        confidence_score=score,
        reasoning=f"Anomaly detected: {anomaly_type}, score={score:.4f}, threshold={threshold:.4f}",
    )


def log_intelligence_event(
    action: str,
    user_id: str | None = None,
    reasoning: str = "",
) -> str:
    return audit_repository.write_log(
        event_type="intelligence",
        action=action,
        user_id=user_id,
        reasoning=reasoning,
    )


def log_crisis_event(
    case_id: str,
    user_id: str,
    crisis_type: str,
    resources_sent: bool = False,
) -> str:
    return audit_repository.write_log(
        event_type="crisis",
        action="crisis_detected",
        case_id=case_id,
        user_id=user_id,
        reasoning=f"Crisis: {crisis_type}, resources_sent={resources_sent}",
    )


def export_audit_logs(
    start_date: str,
    end_date: str,
    export_format: str = "json",
) -> str:
    logs = audit_repository.query_by_event_type(
        "enforcement",
        start_time=start_date,
        end_time=end_date,
        limit=10000,
    )

    for event_type in ("detection", "config_change", "escalation", "intelligence", "crisis"):
        more = audit_repository.query_by_event_type(
            event_type,
            start_time=start_date,
            end_time=end_date,
            limit=10000,
        )
        logs.extend(more)

    logs.sort(key=lambda x: x.get("timestamp", ""))

    return audit_repository.export_to_s3(logs, export_format)


def generate_compliance_report(start_date: str, end_date: str) -> dict:
    enforcement_logs = audit_repository.query_by_event_type(
        "enforcement", start_time=start_date, end_time=end_date, limit=50000
    )

    total = len(enforcement_logs)
    autonomous = sum(1 for l in enforcement_logs if l.get("decision_source") == "autonomous")
    human = total - autonomous

    response_times = [l.get("response_time_ms", 0) for l in enforcement_logs if l.get("response_time_ms")]
    response_times.sort()

    def percentile(data, p):
        if not data:
            return 0
        idx = int(len(data) * p)
        return data[min(idx, len(data) - 1)]

    violations = {}
    jurisdictions = {}
    for log in enforcement_logs:
        vt = log.get("violation_type", "unknown")
        violations[vt] = violations.get(vt, 0) + 1
        jc = log.get("jurisdiction_code", "unknown")
        jurisdictions[jc] = jurisdictions.get(jc, 0) + 1

    avg_ms = sum(response_times) / len(response_times) if response_times else 0

    return {
        "period": {"start": start_date, "end": end_date},
        "total_cases": total,
        "resolution_times": {
            "avg_minutes": round(avg_ms / 60000, 1),
            "p50": round(percentile(response_times, 0.5) / 60000, 1),
            "p90": round(percentile(response_times, 0.9) / 60000, 1),
            "p99": round(percentile(response_times, 0.99) / 60000, 1),
        },
        "autonomous_rate": round(autonomous / total, 4) if total else 0,
        "autonomous_count": autonomous,
        "human_count": human,
        "violation_breakdown": violations,
        "jurisdiction_breakdown": jurisdictions,
    }
