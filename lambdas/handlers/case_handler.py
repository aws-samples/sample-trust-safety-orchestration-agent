import json
import logging

from repositories import case_repository, evidence_repository
from services import content_sanitization_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        path = event.get("resource", event.get("path", ""))

        if "evidence" in path:
            return _get_case_evidence(event)
        elif "active" in path:
            return _get_active_cases(event)
        else:
            return _response(404, {"error": "Not found"})
    except Exception:
        logger.exception("Case handler error")
        return _response(500, {"error": "Internal server error"})


def _get_case_evidence(event):
    case_id = event.get("pathParameters", {}).get("caseId")
    if not case_id:
        return _response(400, {"error": "caseId is required"})

    case = case_repository.get_case(case_id)
    if not case:
        return _response(404, {"error": f"Case {case_id} not found"})

    evidence = evidence_repository.get_evidence_package(case_id)
    metadata = evidence_repository.get_evidence_metadata(case_id)

    qp = event.get("queryStringParameters") or {}
    visibility = qp.get("content_visibility", "labels_only")
    if evidence:
        evidence = content_sanitization_service.sanitize_evidence_package(evidence, visibility)

    return _response(200, {
        "case_id": case_id,
        "status": case.get("status"),
        "evidence_package": evidence,
        "evidence_metadata": metadata,
        "created_at": case.get("created_at"),
        "updated_at": case.get("updated_at"),
    })


def _get_active_cases(event):
    qp = event.get("queryStringParameters") or {}
    limit = int(qp.get("limit", "50"))

    cases, last_key = case_repository.get_active_cases(limit=limit)

    return _response(200, {
        "cases": cases,
        "count": len(cases),
    })


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }
