import base64
import json
import logging
import os
from datetime import datetime, timezone

import boto3

from repositories import base, case_repository, audit_repository, metrics_repository
from services import anomaly_detection_service

logger = logging.getLogger(__name__)

INVESTIGATION_STATE_MACHINE_ARN = os.environ.get("INVESTIGATION_STATE_MACHINE_ARN", "")
ANOMALY_SCORES_TABLE = os.environ.get("ANOMALY_SCORES_TABLE", "")


def lambda_handler(event, context):
    logger.info("Behavioral processor invoked", extra={"record_count": len(event.get("Records", []))})

    batch_item_failures = []

    for record in event.get("Records", []):
        try:
            _process_record(record)
        except Exception as e:
            logger.error(
                "Failed to process behavioral record",
                extra={"error": str(e), "kinesis_sequence": record.get("kinesis", {}).get("sequenceNumber")},
            )
            batch_item_failures.append({
                "itemIdentifier": record["kinesis"]["sequenceNumber"],
            })

    metrics_repository.increment_counter("anomaly_detections")

    return {"batchItemFailures": batch_item_failures}


def _process_record(record):
    raw_data = base64.b64decode(record["kinesis"]["data"])
    behavioral_event = json.loads(raw_data)

    user_id = behavioral_event["user_id"]
    metrics = behavioral_event["behavioral_metrics"]

    anomaly_result = anomaly_detection_service.calculate_anomaly_score(user_id, metrics)

    _update_anomaly_scores(user_id, anomaly_result)

    if anomaly_result["exceeds_investigation_trigger"]:
        case = case_repository.create_case(
            user_id=user_id,
            trigger_source="anomaly_detection",
            violation_type="behavioral_anomaly",
        )

        _start_investigation(case["case_id"], user_id)

        audit_repository.write_log(
            event_type="anomaly_detection",
            action="investigation_triggered",
            case_id=case["case_id"],
            user_id=user_id,
            confidence_score=anomaly_result["anomaly_score"],
            reasoning=f"Anomaly score {anomaly_result['anomaly_score']} exceeded investigation trigger threshold",
        )

        logger.info(
            "Investigation triggered",
            extra={
                "user_id": user_id,
                "case_id": case["case_id"],
                "anomaly_score": anomaly_result["anomaly_score"],
            },
        )

    elif anomaly_result["exceeds_enhanced_monitoring"]:
        audit_repository.write_log(
            event_type="anomaly_detection",
            action="enhanced_monitoring",
            user_id=user_id,
            confidence_score=anomaly_result["anomaly_score"],
            reasoning=f"Anomaly score {anomaly_result['anomaly_score']} exceeded enhanced monitoring threshold",
        )

        logger.info(
            "Enhanced monitoring triggered",
            extra={
                "user_id": user_id,
                "anomaly_score": anomaly_result["anomaly_score"],
            },
        )


def _update_anomaly_scores(user_id, anomaly_result):
    table = base.get_dynamodb_resource().Table(ANOMALY_SCORES_TABLE)
    table.put_item(Item={
        "user_id": user_id,
        "anomaly_score": json.loads(json.dumps(anomaly_result["anomaly_score"]), parse_float=lambda x: x),
        "account_tier": anomaly_result["account_tier"],
        "factors": anomaly_result["factors"],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    })


def _start_investigation(case_id, user_id):
    if not INVESTIGATION_STATE_MACHINE_ARN:
        logger.warning("Investigation state machine ARN not configured")
        return

    sfn = boto3.client("stepfunctions")
    sfn.start_execution(
        stateMachineArn=INVESTIGATION_STATE_MACHINE_ARN,
        name=f"investigation-{case_id}",
        input=json.dumps({
            "case_id": case_id,
            "user_id": user_id,
            "trigger_source": "anomaly_detection",
        }),
    )

    logger.info(
        "Step Functions execution started",
        extra={"case_id": case_id, "state_machine": INVESTIGATION_STATE_MACHINE_ARN},
    )
