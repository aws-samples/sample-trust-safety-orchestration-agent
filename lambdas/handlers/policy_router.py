import json
import logging

from services import policy_engine_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    logger.info("Policy router invoked", extra={"event": json.dumps(event)[:500]})

    case_id = event["case_id"]
    confidence = event["confidence"]
    evidence = event["evidence"]

    scores = confidence.get("scores", {})

    has_sensitive = bool(
        evidence.get("sensitive_category") or evidence.get("crisis_detected")
    )

    routing = policy_engine_service.route_decision(scores, has_sensitive)

    logger.info(
        "Policy routing complete",
        extra={
            "case_id": case_id,
            "decision": routing.get("decision"),
            "action": routing.get("action"),
            "escalation_reason": routing.get("escalation_reason"),
        },
    )

    return routing
