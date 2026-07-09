import logging


from repositories import config_repository

logger = logging.getLogger(__name__)

TIER_THRESHOLDS = {
    "new": {"enhanced_monitoring": 0.5, "investigation_trigger": 0.7},
    "established": {"enhanced_monitoring": 0.6, "investigation_trigger": 0.8},
    "veteran": {"enhanced_monitoring": 0.7, "investigation_trigger": 0.85},
}


def get_account_tier(account_age_days: int) -> str:
    if account_age_days < 30:
        return "new"
    elif account_age_days < 180:
        return "established"
    return "veteran"


def get_tier_thresholds(account_age_days: int) -> dict:
    tier = get_account_tier(account_age_days)
    custom = config_repository.get_active_value("anomaly_thresholds")
    if custom and tier in custom:
        return custom[tier]
    return TIER_THRESHOLDS[tier]


def calculate_anomaly_score(user_id: str, behavioral_metrics: dict) -> dict:
    score = 0.0
    factors = []

    msg_velocity = behavioral_metrics.get("message_velocity", 0)
    if msg_velocity > 50:
        contrib = min((msg_velocity - 50) / 100, 0.3)
        score += contrib
        factors.append({"factor": "high_message_velocity", "value": msg_velocity, "contribution": contrib})

    response_rate = behavioral_metrics.get("response_rate", 0.5)
    if response_rate < 0.05:
        contrib = 0.2
        score += contrib
        factors.append({"factor": "low_response_rate", "value": response_rate, "contribution": contrib})

    profile_views = behavioral_metrics.get("profile_view_rate", 0)
    if profile_views > 200:
        contrib = min((profile_views - 200) / 500, 0.2)
        score += contrib
        factors.append({"factor": "excessive_profile_views", "value": profile_views, "contribution": contrib})

    match_accept_rate = behavioral_metrics.get("match_accept_rate", 0.5)
    if match_accept_rate > 0.95:
        contrib = 0.15
        score += contrib
        factors.append({"factor": "indiscriminate_matching", "value": match_accept_rate, "contribution": contrib})

    report_count = behavioral_metrics.get("recent_report_count", 0)
    if report_count > 0:
        contrib = min(report_count * 0.1, 0.3)
        score += contrib
        factors.append({"factor": "user_reports", "value": report_count, "contribution": contrib})

    score = min(score, 1.0)

    account_age = behavioral_metrics.get("account_age_days", 90)
    tier = get_account_tier(account_age)
    thresholds = get_tier_thresholds(account_age)

    return {
        "user_id": user_id,
        "anomaly_score": float(round(score, 4)),
        "factors": factors,
        "account_tier": tier,
        "thresholds": thresholds,
        "exceeds_enhanced_monitoring": score >= thresholds["enhanced_monitoring"],
        "exceeds_investigation_trigger": score >= thresholds["investigation_trigger"],
    }


def batch_calculate_scores(user_metrics_list: list[tuple[str, dict]]) -> list[dict]:
    return [calculate_anomaly_score(uid, metrics) for uid, metrics in user_metrics_list]
