import json
import logging

from repositories import review_queue_repository, case_repository, evidence_repository
from services import (
    enforcement_engine_service,
    escalation_service,
    feedback_loop_service,
    content_sanitization_service,
    reviewer_wellbeing_service,
    audit_service,
)

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        path = event.get("resource", event.get("path", ""))
        method = event.get("httpMethod", "GET")

        if event.get("action") == "check_stale_cases":
            return _check_stale_cases()

        if method == "GET" and "review-queue" in path:
            return _get_review_queue(event)
        elif method == "POST" and "decision" in path:
            return _submit_decision(event)
        else:
            return _response(404, {"error": "Not found"})
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON body"})
    except ValueError as e:
        return _response(400, {"error": str(e)})
    except Exception as e:
        logger.exception("Review handler error")
        return _response(500, {"error": "Internal server error"})


def _get_reviewer_id(event):
    claims = event.get("requestContext", {}).get("authorizer", {}).get("claims", {})
    return claims.get("sub", "unknown")


def _get_review_queue(event):
    qp = event.get("queryStringParameters") or {}
    priority = qp.get("priority")
    limit = int(qp.get("limit", "20"))

    cases, last_key = review_queue_repository.get_queue(
        priority_filter=priority,
        limit=limit,
    )
    depth = review_queue_repository.get_queue_depth()

    return _response(200, {
        "cases": cases,
        "total_count": sum(depth.values()),
        "queue_depth_by_priority": depth,
    })


def _submit_decision(event):
    case_id = event.get("pathParameters", {}).get("caseId")
    if not case_id:
        return _response(400, {"error": "caseId is required"})

    body = json.loads(event.get("body", "{}"))
    reviewer_id = _get_reviewer_id(event)

    decision = body.get("decision")
    action = body.get("action")
    notes = body.get("notes", "")

    if not decision:
        return _response(400, {"error": "decision is required"})

    case = case_repository.get_case(case_id)
    if not case:
        return _response(404, {"error": f"Case {case_id} not found"})

    if decision in ("approve_action", "custom_action") and action:
        result = enforcement_engine_service.execute_action(
            case_id=case_id,
            user_id=case.get("user_id", ""),
            action=action,
            violation_type=case.get("violation_type", "unknown"),
            confidence_score=float(case.get("confidence_score", 0)),
            is_autonomous=False,
            reviewer_id=reviewer_id,
        )
    elif decision == "dismiss":
        case_repository.update_case_status(case_id, "resolved")
        result = {"case_id": case_id, "action_status": "dismissed"}
    elif decision == "escalate":
        result = escalation_service.escalate_case(
            case_id=case_id,
            user_id=case.get("user_id", ""),
            reason="reviewer_escalation",
        )
    else:
        return _response(400, {"error": f"Invalid decision: {decision}"})

    feedback_loop_service.record_decision_feedback(
        case_id=case_id,
        predicted_violation=case.get("violation_type", "unknown"),
        predicted_confidence=float(case.get("confidence_score", 0)),
        actual_decision=decision,
        reviewer_id=reviewer_id,
    )

    reviewer_wellbeing_service.track_exposure(
        reviewer_id=reviewer_id,
        case_id=case_id,
        content_severity=case.get("content_severity", "medium"),
    )

    audit_service.log_enforcement_action(
        case_id=case_id,
        user_id=case.get("user_id", ""),
        action=action or decision,
        violation_type=case.get("violation_type", "unknown"),
        confidence_score=float(case.get("confidence_score", 0)),
        decision_source="human",
        reasoning=f"Reviewer {reviewer_id}: {decision}. Notes: {notes}",
    )

    return _response(200, result)


def _check_stale_cases():
    alerts = escalation_service.check_queue_age_alerts()
    logger.info(f"Stale queue check: {len(alerts)} alerts")
    return {"alerts": alerts}


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }
