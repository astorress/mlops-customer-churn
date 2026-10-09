"""Online inference API: POST /predict (HTTP API, public and throttled).

Body: {"customers": [{"customer_id": "..", "tenure": 3, "contract":
"Month-to-month", ...}]} (a single object is also accepted). Categories may
come raw ("Month-to-month") or curated ("month_to_month").

Rows are sent to the endpoint as headerless CSV in FEATURES order — the
format the DataDrift monitor parses in the captured traffic.
"""
import csv
import io
import json
import os

from src.features.schema import (
    CATEGORICAL_FEATURES,
    FEATURES,
    ID_COLUMN,
    normalize_category,
)
from src.services import sagemaker_runtime
from src.utilities.errors import RequestValidationError
from src.utilities.http import json_response
from src.utilities.logger import get_logger

logger = get_logger(__name__)

ENDPOINT_NAME = os.environ.get("ENDPOINT_NAME", "")
MAX_CUSTOMERS = int(os.environ.get("MAX_CUSTOMERS", "100"))


def parse_customers(body: str | None) -> list:
    try:
        payload = json.loads(body or "{}")
    except json.JSONDecodeError as error:
        raise RequestValidationError(f"Invalid JSON: {error}") from error
    if isinstance(payload, dict):
        # {"customers": [...]} or one customer object ({} = no customers).
        customers = payload.get("customers", [payload] if payload else [])
    else:
        customers = payload
    if not customers:
        raise RequestValidationError("No customers in request body")
    if len(customers) > MAX_CUSTOMERS:
        raise RequestValidationError(
            f"At most {MAX_CUSTOMERS} customers per request")
    for index, customer in enumerate(customers):
        missing = [name for name in FEATURES if customer.get(name) is None]
        if missing:
            raise RequestValidationError(
                f"Customer {index} is missing {missing}")
    return customers


def to_csv(customers: list) -> str:
    output = io.StringIO()
    writer = csv.writer(output, lineterminator="\n")
    for customer in customers:
        writer.writerow([
            normalize_category(customer[name])
            if name in CATEGORICAL_FEATURES else customer[name]
            for name in FEATURES
        ])
    return output.getvalue()


def handler(event, context):
    try:
        customers = parse_customers(event.get("body"))
    except RequestValidationError as error:
        return json_response(400, {
            "message": str(error)
        })

    body = sagemaker_runtime.invoke_endpoint(
        ENDPOINT_NAME,
        to_csv(customers).encode("utf-8"),
        content_type="text/csv",
        accept="application/json",
    )
    predictions = json.loads(body)["predictions"]
    for customer, prediction in zip(customers, predictions):
        prediction[ID_COLUMN] = customer.get(ID_COLUMN)
    return json_response(200, {
        "predictions": predictions
    })
