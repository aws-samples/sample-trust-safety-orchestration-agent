import json
import logging

from services import audit_service

logger = logging.getLogger(__name__)


def lambda_handler(event, context):
    try:
        path = event.get("path", "") or event.get("resource", "")

        if "/audit/export" in path:
            return _handle_export(event)
        elif "/reports/compliance" in path:
            return _handle_compliance_report(event)
        else:
            return _response(404, {"error": f"Unknown path: {path}"})

    except ValueError as e:
        return _response(400, {"error": str(e)})
    except Exception:
        logger.exception("Handler error")
        return _response(500, {"error": "Internal server error"})


def _handle_export(event):
    params = event.get("queryStringParameters") or {}

    start_date = params.get("start_date")
    end_date = params.get("end_date")
    export_format = params.get("format", "json")

    if not start_date:
        raise ValueError("start_date query parameter is required")
    if not end_date:
        raise ValueError("end_date query parameter is required")

    presigned_url = audit_service.export_audit_logs(
        start_date=start_date,
        end_date=end_date,
        export_format=export_format,
    )

    return _response(200, {"download_url": presigned_url})


def _handle_compliance_report(event):
    params = event.get("queryStringParameters") or {}

    start_date = params.get("start_date")
    end_date = params.get("end_date")

    if not start_date:
        raise ValueError("start_date query parameter is required")
    if not end_date:
        raise ValueError("end_date query parameter is required")

    report = audit_service.generate_compliance_report(
        start_date=start_date,
        end_date=end_date,
    )

    return _response(200, report)


def _response(status_code, body):
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
        "body": json.dumps(body, default=str),
    }
