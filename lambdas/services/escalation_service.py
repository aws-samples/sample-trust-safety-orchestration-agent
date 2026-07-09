import logging
from datetime import datetime, timezone, timedelta

from repositories import (
    review_queue_repository,
    case_repository,
    audit_repository,
)
from services import precedent_matcher_service

logger = logging.getLogger(__name__)

PRIORITY_WEIGHTS = {
    "self_harm": 100,
    "child_safety": 100,
    "illegal_activity": 95,
    "harassment": 70,
    "scam": 60,
    "fake_profile": 50,
    "explicit_content": 40,
    "bot_farm": 80,
}

ESCALATION_REASONS = {
    "sensitive_category",
    "below_threshold",
    "no_matching_action",
    "no_confidence_scores",
    "system_error",
    "appeal",
    "novel_pattern",
    "bulk_action_low_confidence",
}

REVIEW_TIME_ESTIMATES = {
    "critical": 10,
    "high": 7,
    "medium": 5,
    "low": 3,
}


def calculate_priority(
    violation_type: str,
    confidence_score: float,
    escalation_reason: str,
) -> str:
    if escalation_reason == "sensitive_category":
        return "critical"
    if escalation_reason == "system_error":
        return "high"

    base = PRIORITY_WEIGHTS.get(violation_type, 50)
    score_factor = confidence_score * 30

    total = base + score_factor

    if total >= 90:
        return "critical"
    elif total >= 70:
        return "high"
    elif total >= 40:
        return "medium"
    return "low"


def escalate_case(
    case_id: str,
    user_id: str,
    evidence: dict | None = None,
    confidence: dict | None = None,
    reason: str = "below_threshold",
) -> dict:
    confidence_scores = {}
    if confidence:
        confidence_scores = confidence.get("scores", confidence)
        if "primary_violation" in confidence:
            primary_type = confidence["primary_violation"]
            primary_score = confidence.get("primary_score", 0)
        elif confidence_scores:
            primary_type, primary_score = max(confidence_scores.items(), key=lambda x: x[1])
        else:
            primary_type, primary_score = "unknown", 0.0
    else:
        primary_type, primary_score = "unknown", 0.0

    priority = calculate_priority(primary_type, primary_score, reason)

    precedents = []
    if evidence:
        try:
            precedents = precedent_matcher_service.find_similar_cases(
                evidence, primary_type, limit=5
            )
        except Exception as e:
            logger.warning("Precedent matching failed", extra={"error": str(e)})

    estimated_minutes = REVIEW_TIME_ESTIMATES.get(priority, 5)

    queue_id = review_queue_repository.add_to_queue(
        case_id=case_id,
        priority=priority,
        escalation_reason=reason,
        estimated_review_minutes=estimated_minutes,
        similar_case_ids=[p.get("case_id", "") for p in precedents],
    )

    case_repository.update_case_status(case_id, "escalated")

    audit_repository.write_log(
        event_type="escalation",
        action="escalate_to_human_review",
        case_id=case_id,
        user_id=user_id,
        violation_type=primary_type,
        confidence_score=primary_score,
        reasoning=f"Escalated: {reason}, priority: {priority}",
    )

    logger.info("Case escalated", extra={
        "case_id": case_id,
        "priority": priority,
        "reason": reason,
        "queue_id": queue_id,
    })

    return {
        "queue_id": queue_id,
        "priority": priority,
        "escalation_reason": reason,
        "precedent_count": len(precedents),
        "estimated_review_minutes": estimated_minutes,
    }


def check_queue_age_alerts(stale_hours: int = 4) -> list[dict]:
    threshold = (datetime.now(timezone.utc) - timedelta(hours=stale_hours)).isoformat()
    stale_cases = review_queue_repository.get_stale_cases(threshold)

    alerts = []
    for case in stale_cases:
        alerts.append({
            "queue_id": case["queue_id"],
            "case_id": case.get("case_id"),
            "priority": case.get("priority"),
            "wait_hours": stale_hours,
            "alert_type": "stale_review_case",
        })

    if alerts:
        logger.warning(f"{len(alerts)} stale cases in review queue (>{stale_hours}h)")

    return alerts
