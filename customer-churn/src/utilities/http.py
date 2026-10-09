import json


def json_response(status_code: int, body: dict) -> dict:
    """API Gateway (HTTP API) proxy response."""
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
        },
        "body": json.dumps(body),
    }
