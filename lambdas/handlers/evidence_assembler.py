import json
import logging

from repositories import case_repository
from services import evidence_assembly_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    logger.info("Evidence assembler invoked", extra={"event": json.dumps(event)[:500]})

    case_id = event["case_id"]
    user_id = event["user_id"]
    trigger_source = event.get("trigger_source", "unknown")

    logger.info(
        "Assembling evidence",
        extra={"case_id": case_id, "user_id": user_id, "trigger_source": trigger_source},
    )

    case_repository.update_case_status(case_id, "investigating")

    evidence_package = evidence_assembly_service.assemble_evidence_package(case_id, user_id)

    logger.info(
        "Evidence assembly complete",
        extra={
            "case_id": case_id,
            "unavailable_sources": evidence_package.get("unavailable_sources", []),
        },
    )

    return evidence_package
