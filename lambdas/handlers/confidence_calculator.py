import json
import logging

from services import confidence_calculator_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    logger.info("Confidence calculator invoked", extra={"event": json.dumps(event)[:500]})

    case_id = event["case_id"]
    evidence = event["evidence"]

    scores = confidence_calculator_service.calculate_confidence_scores(evidence)

    primary_type, primary_score = confidence_calculator_service.get_primary_violation(scores)

    logger.info(
        "Confidence scores calculated",
        extra={
            "case_id": case_id,
            "primary_violation": primary_type,
            "primary_score": primary_score,
            "all_scores": scores,
        },
    )

    return {
        "scores": scores,
        "primary_violation": primary_type,
        "primary_score": primary_score,
    }
