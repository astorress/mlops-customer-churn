import json
from unittest.mock import MagicMock

import pytest

from src.features.schema import FEATURES
from src.functions.inference import predict


@pytest.fixture
def customer(curated_df):
    row = curated_df.iloc[0]
    data = {
        name: row[name]
        for name in FEATURES + ["customer_id"]
    }
    data = {
        key: (value.item() if hasattr(value, "item") else value)
        for key, value in data.items()
    }
    data["contract"] = "Month-to-month"  # raw values are accepted too
    return data


def test_builds_csv_and_calls_endpoint(monkeypatch, customer):
    runtime = MagicMock()
    runtime.invoke_endpoint.return_value = json.dumps({
        "predictions": [{
            "churn_probability": 0.8,
            "churn": True,
        }],
    }).encode()
    monkeypatch.setattr(predict, "sagemaker_runtime", runtime)

    result = predict.handler({
        "body": json.dumps({
            "customers": [customer]
        })
    }, None)

    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["predictions"][0]["customer_id"] == customer["customer_id"]
    sent = runtime.invoke_endpoint.call_args.args[1].decode()
    values = sent.strip().split(",")
    assert len(values) == len(FEATURES)
    assert "month_to_month" in values


@pytest.mark.parametrize(
    "body, message",
    [
        ("not json", "Invalid JSON"),
        ("{}", "No customers"),
    ],
)
def test_rejects_invalid_bodies(body, message):
    result = predict.handler({
        "body": body
    }, None)
    assert result["statusCode"] == 400
    assert message in json.loads(result["body"])["message"]


def test_rejects_missing_features(customer):
    customer.pop("tenure")
    result = predict.handler({
        "body": json.dumps(customer)
    }, None)
    assert result["statusCode"] == 400
    assert "tenure" in json.loads(result["body"])["message"]
