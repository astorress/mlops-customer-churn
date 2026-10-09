import json

from src.features.schema import TARGET
from src.serving.inference import (
    input_fn,
    output_fn,
    predict_fn,
)


def _rows(splits, count):
    return splits[2].drop(columns=["customer_id", TARGET]).head(count)


def test_csv_and_json_inputs_match(trained_model, splits):
    rows = _rows(splits, 3)
    csv_scores = predict_fn(
        input_fn(rows.to_csv(header=False, index=False), "text/csv"),
        trained_model,
    )
    json_body = json.dumps({
        "instances": rows.to_dict("records")
    })
    json_scores = predict_fn(
        input_fn(json_body, "application/json"),
        trained_model,
    )
    assert list(csv_scores.round(6)) == list(json_scores.round(6))


def test_output_formats(trained_model, splits):
    scores = predict_fn(
        input_fn(
            _rows(splits, 3).to_csv(header=False, index=False), "text/csv"),
        trained_model,
    )
    body, content_type = output_fn(scores, "application/json")
    assert content_type == "application/json"
    assert 0 <= json.loads(body)["predictions"][0]["churn_probability"] <= 1

    body, content_type = output_fn(scores, "text/csv; charset=utf-8")
    assert content_type == "text/csv"
    assert len(body.splitlines()) == 3


def test_missing_total_charges(trained_model, splits):
    row = _rows(splits, 1).copy()
    row["total_charges"] = None
    body = row.to_csv(header=False, index=False)
    assert len(predict_fn(input_fn(body, "text/csv"), trained_model)) == 1
