import logging
from decimal import Decimal

from repositories import config_repository

logger = logging.getLogger(__name__)

DEFAULT_WEIGHTS = {
    "message_analysis": {
        "scam_patterns": 0.25,
        "threat_indicators": 0.25,
        "sentiment_hostility": 0.10,
    },
    "image_analysis": {
        "ai_generated": 0.15,
        "reverse_image_match": 0.10,
        "stock_photo_match": 0.10,
    },
    "behavioral": {
        "anomaly_score": 0.20,
        "report_count": 0.15,
    },
    "cross_platform": {
        "blocklist_match": 0.30,
    },
}


def _get_weights() -> dict:
    custom = config_repository.get_active_value("confidence_weights")
    if custom:
        return custom
    return DEFAULT_WEIGHTS


def calculate_confidence_scores(evidence_package: dict) -> dict:
    scores = {}
    weights = _get_weights()

    msg = evidence_package.get("message_analysis", {})
    img = evidence_package.get("image_analysis", {})
    bad_actor = evidence_package.get("bad_actor_matches", [])
    reports = evidence_package.get("previous_reports", [])

    scam_score = _scam_confidence(msg)
    if scam_score > 0:
        scores["scam"] = round(scam_score, 4)

    harassment_score = _harassment_confidence(msg)
    if harassment_score > 0:
        scores["harassment"] = round(harassment_score, 4)

    fake_profile_score = _fake_profile_confidence(img, bad_actor)
    if fake_profile_score > 0:
        scores["fake_profile"] = round(fake_profile_score, 4)

    if msg.get("has_crisis_indicators"):
        scores["self_harm"] = 0.95

    if bad_actor:
        best_match = max((m.get("confidence_score", 0) for m in bad_actor), default=0)
        if best_match > 0:
            scores["repeat_offender"] = round(float(best_match), 4)

    report_boost = min(len(reports) * 0.05, 0.2)
    for vtype in scores:
        scores[vtype] = round(min(scores[vtype] + report_boost, 1.0), 4)

    return scores


def _scam_confidence(msg_analysis: dict) -> float:
    patterns = msg_analysis.get("scam_patterns", [])
    if not patterns:
        return 0.0
    base = min(len(patterns) * 0.2, 0.7)
    sentiment = msg_analysis.get("sentiment_summary", {})
    if sentiment.get("overall") == "hostile":
        base += 0.1
    return min(base, 1.0)


def _harassment_confidence(msg_analysis: dict) -> float:
    threats = msg_analysis.get("threat_indicators", [])
    if not threats:
        sentiment = msg_analysis.get("sentiment_summary", {})
        hostility = float(sentiment.get("hostility_score", 0))
        if hostility > 0.7:
            return hostility * 0.6
        return 0.0
    base = min(len(threats) * 0.25, 0.8)
    return min(base, 1.0)


def _fake_profile_confidence(img_analysis: dict, bad_actor_matches: list) -> float:
    score = 0.0
    ai_prob = float(img_analysis.get("ai_generated_probability", 0))
    if ai_prob > 0.5:
        score += ai_prob * 0.4

    reverse_matches = img_analysis.get("reverse_image_matches", [])
    if reverse_matches:
        score += min(len(reverse_matches) * 0.15, 0.3)

    stock_matches = img_analysis.get("stock_photo_matches", [])
    if stock_matches:
        score += 0.3

    if bad_actor_matches:
        score += 0.3

    return min(score, 1.0)


def get_primary_violation(scores: dict) -> tuple[str, float]:
    if not scores:
        return ("unknown", 0.0)
    primary = max(scores.items(), key=lambda x: x[1])
    return primary
