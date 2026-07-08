import json
import logging

from repositories import case_repository, audit_repository, metrics_repository
from services import intelligence_service, enforcement_engine_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    logger.info("Profile processor invoked", extra={"event": json.dumps(event)[:500]})

    detail = event.get("detail", {})
    user_id = detail["user_id"]
    device_fingerprint = detail["device_fingerprint"]
    behavioral_signature = detail.get("behavioral_signature")

    match = intelligence_service.check_blocklist_match(device_fingerprint, behavioral_signature)

    if match and match.get("confidence", 0) >= 0.95:
        logger.info(
            "High-confidence blocklist match, executing permanent ban",
            extra={"user_id": user_id, "confidence": match["confidence"]},
        )

        enforcement_engine_service.execute_action(
            case_id=f"BLOCKLIST-{user_id}",
            user_id=user_id,
            action="permanent_ban",
            violation_type=match.get("ban_reason", "blocklist_match"),
            confidence_score=match["confidence"],
            is_autonomous=True,
        )

        audit_repository.write_log(
            event_type="profile_screening",
            action="blocklist_permanent_ban",
            user_id=user_id,
            confidence_score=match["confidence"],
            reasoning=f"Blocklist match (confidence={match['confidence']:.2f}): {match.get('match_type')}, source={match.get('source_platform')}",
        )

    elif match and match.get("confidence", 0) >= 0.80:
        logger.info(
            "Medium-confidence blocklist match, creating case for investigation",
            extra={"user_id": user_id, "confidence": match["confidence"]},
        )

        case = case_repository.create_case(
            user_id=user_id,
            trigger_source="cross_platform_match",
            violation_type=match.get("ban_reason", "blocklist_match"),
        )

        case_repository.update_case_status(case["case_id"], "enhanced_monitoring")

        audit_repository.write_log(
            event_type="profile_screening",
            action="enhanced_monitoring",
            case_id=case["case_id"],
            user_id=user_id,
            confidence_score=match["confidence"],
            reasoning=f"Blocklist match (confidence={match['confidence']:.2f}): {match.get('match_type')}, source={match.get('source_platform')}",
        )

    else:
        logger.info("No blocklist match for new profile", extra={"user_id": user_id})
        metrics_repository.record_metric("profile_creations", 1)

    return None
