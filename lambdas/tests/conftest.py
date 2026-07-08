import os
import sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

os.environ.setdefault("CASES_TABLE", "tg-cases-test")
os.environ.setdefault("EVIDENCE_TABLE", "tg-evidence-test")
os.environ.setdefault("AUDIT_TABLE", "tg-audit-test")
os.environ.setdefault("CONFIG_TABLE", "tg-config-test")
os.environ.setdefault("BLOCKLIST_TABLE", "tg-blocklist-test")
os.environ.setdefault("REVIEW_QUEUE_TABLE", "tg-review-queue-test")
os.environ.setdefault("METRICS_TABLE", "tg-metrics-test")
os.environ.setdefault("REVIEWER_STATE_TABLE", "tg-reviewer-state-test")
os.environ.setdefault("APPEAL_TABLE", "tg-appeals-test")
os.environ.setdefault("WEBSOCKET_TABLE", "tg-websocket-test")
os.environ.setdefault("ANOMALY_SCORES_TABLE", "tg-anomaly-scores-test")
os.environ.setdefault("EVIDENCE_BUCKET", "tg-evidence-test")
os.environ.setdefault("AUDIT_ARCHIVE_BUCKET", "tg-audit-archive-test")
os.environ.setdefault("CONFIG_BACKUP_BUCKET", "tg-config-backup-test")
os.environ.setdefault("REDIS_HOST", "localhost")
os.environ.setdefault("REDIS_PORT", "6379")
os.environ.setdefault("NOTIFICATION_QUEUE_URL", "https://sqs.us-west-2.amazonaws.com/test/notifications")
os.environ.setdefault("INVESTIGATION_QUEUE_URL", "https://sqs.us-west-2.amazonaws.com/test/investigations")
os.environ.setdefault("INVESTIGATION_STATE_MACHINE_ARN", "arn:aws:states:us-west-2:123456789:stateMachine:test")
os.environ.setdefault("BULK_ACTION_STATE_MACHINE_ARN", "arn:aws:states:us-west-2:123456789:stateMachine:test-bulk")
os.environ.setdefault("PLATFORM_API_URL", "https://api.platform.test/v1")
os.environ.setdefault("PARTNER_NETWORK_INTEL_API_URL", "")
os.environ.setdefault("BEDROCK_MODEL_ID", "anthropic.claude-3-sonnet-20240229-v1:0")
os.environ.setdefault("WEBSOCKET_API_ENDPOINT", "https://ws.test.execute-api.us-west-2.amazonaws.com/prod")
os.environ.setdefault("ENVIRONMENT", "test")
os.environ.setdefault("AWS_DEFAULT_REGION", "us-west-2")


@pytest.fixture
def api_gateway_event():
    def _make(method="GET", path="/", body=None, path_params=None, query_params=None, claims=None):
        event = {
            "httpMethod": method,
            "resource": path,
            "path": path,
            "pathParameters": path_params or {},
            "queryStringParameters": query_params or {},
            "body": None,
            "requestContext": {
                "authorizer": {
                    "claims": claims or {"sub": "test-reviewer-001", "email": "reviewer@test.com"}
                }
            },
        }
        if body is not None:
            import json
            event["body"] = json.dumps(body)
        return event
    return _make


@pytest.fixture
def lambda_context():
    class FakeContext:
        function_name = "test-function"
        memory_limit_in_mb = 256
        invoked_function_arn = "arn:aws:lambda:us-west-2:123456789:function:test"
        aws_request_id = "test-request-id"
    return FakeContext()
