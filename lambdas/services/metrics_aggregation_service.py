import logging
from datetime import datetime, timezone, timedelta

from repositories import metrics_repository, case_repository, review_queue_repository

logger = logging.getLogger(__name__)


def get_realtime_metrics() -> dict:
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0).isoformat()

    platform_safety_score = get_platform_safety_score()
    autonomous_rate = get_autonomous_resolution_rate()

    cases_today = metrics_repository.get_metric_values("cases_processed", today_start)
    cases_processed_today = int(sum(float(m.get("value", 0)) for m in cases_today))

    avg_resolution = metrics_repository.get_latest_metric("avg_resolution_time_minutes")
    avg_resolution_time = float(avg_resolution["value"]) if avg_resolution else 0.0

    queue_depths = review_queue_repository.get_queue_depth()
    total_queue_depth = sum(queue_depths.values())

    threat_distribution = get_threat_distribution()

    active_cases_by_stage = {}
    for status in ("detected", "investigating", "decision_pending", "escalated"):
        items, _ = case_repository.get_cases_by_status(status, limit=1)
        active_cases_by_stage[status] = len(items)

    elevated = check_elevated_threat_level()

    return {
        "platform_safety_score": platform_safety_score,
        "cases_processed_today": cases_processed_today,
        "autonomous_resolution_rate": autonomous_rate,
        "avg_resolution_time_minutes": avg_resolution_time,
        "review_queue_depth": total_queue_depth,
        "threat_distribution": threat_distribution,
        "active_cases_by_stage": active_cases_by_stage,
        "elevated_threat_level": elevated,
        "last_updated": now.isoformat(),
    }


def get_platform_safety_score() -> float:
    active_cases, _ = case_repository.get_active_cases(limit=50)
    open_cases_weight = min(len(active_cases) / 50.0, 1.0)

    queue_depths = review_queue_repository.get_queue_depth()
    total_depth = sum(queue_depths.values())
    queue_depth_weight = min(total_depth / 100.0, 1.0)

    error_metric = metrics_repository.get_latest_metric("error_rate")
    error_rate_weight = float(error_metric["value"]) if error_metric else 0.0
    error_rate_weight = min(error_rate_weight, 1.0)

    score = 100 - (open_cases_weight * 20) - (queue_depth_weight * 10) - (error_rate_weight * 30)
    return max(0.0, min(100.0, round(score, 2)))


def get_autonomous_resolution_rate() -> float:
    now = datetime.now(timezone.utc)
    day_ago = (now - timedelta(hours=24)).isoformat()

    autonomous = metrics_repository.get_metric_values("autonomous_resolutions", day_ago)
    total = metrics_repository.get_metric_values("total_resolutions", day_ago)

    autonomous_count = sum(float(m.get("value", 0)) for m in autonomous)
    total_count = sum(float(m.get("value", 0)) for m in total)

    if total_count == 0:
        return 0.0
    return round(autonomous_count / total_count, 4)


def get_threat_distribution() -> dict:
    distribution = {}
    active_cases, _ = case_repository.get_active_cases(limit=50)

    for case in active_cases:
        vtype = case.get("violation_type", "unknown")
        distribution[vtype] = distribution.get(vtype, 0) + 1

    return distribution


def check_elevated_threat_level(baseline_hourly: int = 50) -> bool:
    now = datetime.now(timezone.utc)
    one_hour_ago = (now - timedelta(hours=1)).isoformat()

    recent_anomalies = metrics_repository.get_metric_values("anomaly_detections", one_hour_ago)
    current_volume = sum(float(m.get("value", 0)) for m in recent_anomalies)

    threshold = baseline_hourly * 2.0
    elevated = current_volume > threshold
    if elevated:
        logger.warning(
            "Elevated threat level detected",
            extra={"current_volume": current_volume, "threshold": threshold},
        )
    return elevated


def generate_compliance_report(start_date: str, end_date: str) -> dict:
    resolution_agg = metrics_repository.get_metric_aggregate(
        "resolution_time_minutes", start_date, end_date
    )

    total_resolutions = metrics_repository.get_metric_values("total_resolutions", start_date, end_date)
    total_cases = int(sum(float(m.get("value", 0)) for m in total_resolutions))

    autonomous_resolutions = metrics_repository.get_metric_values(
        "autonomous_resolutions", start_date, end_date
    )
    autonomous_count = int(sum(float(m.get("value", 0)) for m in autonomous_resolutions))
    autonomous_rate = round(autonomous_count / total_cases, 4) if total_cases > 0 else 0.0

    violation_metrics = metrics_repository.get_metric_values("violation_type_count", start_date, end_date)
    violation_breakdown = {}
    for m in violation_metrics:
        dims = m.get("dimensions", {})
        vtype = dims.get("violation_type", "unknown")
        violation_breakdown[vtype] = violation_breakdown.get(vtype, 0) + int(float(m.get("value", 0)))

    appeal_metrics = metrics_repository.get_metric_values("appeal_submitted", start_date, end_date)
    appeal_count = int(sum(float(m.get("value", 0)) for m in appeal_metrics))
    appeal_rate = round(appeal_count / total_cases, 4) if total_cases > 0 else 0.0

    jurisdiction_metrics = metrics_repository.get_metric_values("jurisdiction_cases", start_date, end_date)
    jurisdiction_breakdown = {}
    for m in jurisdiction_metrics:
        dims = m.get("dimensions", {})
        jurisdiction = dims.get("jurisdiction", "unknown")
        jurisdiction_breakdown[jurisdiction] = jurisdiction_breakdown.get(jurisdiction, 0) + int(
            float(m.get("value", 0))
        )

    return {
        "period": {"start": start_date, "end": end_date},
        "total_cases": total_cases,
        "resolution_times": {
            "avg": resolution_agg.get("avg", 0),
            "p50": resolution_agg.get("p50", 0),
            "p90": resolution_agg.get("p90", 0),
            "p99": resolution_agg.get("p99", 0),
        },
        "autonomous_rate": autonomous_rate,
        "violation_breakdown": violation_breakdown,
        "appeal_rates": appeal_rate,
        "jurisdiction_breakdown": jurisdiction_breakdown,
    }
