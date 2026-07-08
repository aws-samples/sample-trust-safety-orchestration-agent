import logging

from repositories import config_repository

logger = logging.getLogger(__name__)

DEFAULT_AUTONOMOUS_THRESHOLDS = {
    "harassment": {"permanent_ban": 0.90, "temporary_suspension": 0.75},
    "scam": {"permanent_ban": 0.90, "temporary_suspension": 0.75},
    "fake_profile": {"permanent_ban": 0.90, "temporary_suspension": 0.75},
    "explicit_content": {"content_removal": 0.70, "temporary_suspension": 0.80},
    "bot_farm": {"permanent_ban": 0.85},
    "repeat_offender": {"permanent_ban": 0.85},
    "self_harm": {},
    "illegal_activity": {},
    "child_safety": {},
}

SENSITIVE_CATEGORIES = {"self_harm", "illegal_activity", "child_safety"}

ACTION_SEVERITY_ORDER = [
    "warning",
    "content_removal",
    "rate_limit",
    "temporary_suspension",
    "permanent_ban",
]


def get_autonomous_threshold(violation_type: str, action: str) -> float:
    custom = config_repository.get_active_value("autonomous_thresholds")
    if custom and violation_type in custom and action in custom[violation_type]:
        return float(custom[violation_type][action])
    defaults = DEFAULT_AUTONOMOUS_THRESHOLDS.get(violation_type, {})
    return float(defaults.get(action, 1.0))


def should_escalate_to_human(
    violation_type: str,
    confidence_score: float,
    has_sensitive_category: bool = False,
) -> bool:
    if has_sensitive_category or violation_type in SENSITIVE_CATEGORIES:
        return True

    thresholds = DEFAULT_AUTONOMOUS_THRESHOLDS.get(violation_type, {})
    custom = config_repository.get_active_value("autonomous_thresholds")
    if custom and violation_type in custom:
        thresholds = custom[violation_type]

    if not thresholds:
        return True

    min_threshold = min(thresholds.values()) if thresholds else 1.0
    return confidence_score < min_threshold


def get_enforcement_action(
    violation_type: str,
    confidence_score: float,
    is_repeat_offender: bool = False,
) -> str:
    if violation_type in SENSITIVE_CATEGORIES:
        return "escalate"

    if is_repeat_offender:
        threshold = get_autonomous_threshold(violation_type, "permanent_ban")
        if confidence_score >= threshold * 0.9:
            return "permanent_ban"

    thresholds = DEFAULT_AUTONOMOUS_THRESHOLDS.get(violation_type, {})
    custom = config_repository.get_active_value("autonomous_thresholds")
    if custom and violation_type in custom:
        thresholds = custom[violation_type]

    best_action = None
    for action in reversed(ACTION_SEVERITY_ORDER):
        if action in thresholds and confidence_score >= thresholds[action]:
            best_action = action
            break

    if best_action is None:
        for action in ACTION_SEVERITY_ORDER:
            if action in thresholds and confidence_score >= thresholds[action]:
                best_action = action

    return best_action or "escalate"


def route_decision(
    confidence_scores: dict,
    has_sensitive_category: bool = False,
) -> dict:
    if not confidence_scores:
        return {
            "decision": "escalate",
            "action": None,
            "escalation_reason": "no_confidence_scores",
        }

    primary_type, primary_score = max(confidence_scores.items(), key=lambda x: x[1])

    if should_escalate_to_human(primary_type, primary_score, has_sensitive_category):
        reason = "sensitive_category" if (has_sensitive_category or primary_type in SENSITIVE_CATEGORIES) else "below_threshold"
        return {
            "decision": "escalate",
            "action": None,
            "escalation_reason": reason,
            "primary_violation": primary_type,
            "primary_score": primary_score,
        }

    action = get_enforcement_action(primary_type, primary_score)
    if action == "escalate":
        return {
            "decision": "escalate",
            "action": None,
            "escalation_reason": "no_matching_action",
            "primary_violation": primary_type,
            "primary_score": primary_score,
        }

    return {
        "decision": "autonomous",
        "action": action,
        "escalation_reason": None,
        "primary_violation": primary_type,
        "primary_score": primary_score,
    }
