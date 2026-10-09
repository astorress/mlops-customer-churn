"""Inference handlers used by serve.py (real-time endpoint and Batch
Transform).

Request content types:
    text/csv          headerless rows in src.features.schema.FEATURES order
                      (what the DataDrift monitor parses in captured traffic)
    application/json  {"instances": [{"tenure": 3, ...}, ...]}
Response accept types:
    application/json  {"predictions": [{"churn_probability": .., "churn": ..}]}
    text/csv          one probability per line (Batch Transform join)
"""
import io
import json
import os

import joblib
import pandas as pd

from src.features.schema import FEATURES, NUMERIC_FEATURES

MODEL_FILE_NAME = "model.joblib"
THRESHOLD = float(os.environ.get("CHURN_THRESHOLD", "0.5"))


def model_fn(model_dir):
    return joblib.load(os.path.join(model_dir, MODEL_FILE_NAME))


def input_fn(request_body, request_content_type):
    if isinstance(request_body, bytes):
        request_body = request_body.decode("utf-8")

    if request_content_type == "text/csv":
        df = pd.read_csv(
            io.StringIO(request_body),
            header=None,
            names=FEATURES,
            skipinitialspace=True,
        )
    elif request_content_type == "application/json":
        payload = json.loads(request_body)
        instances = payload.get("instances", payload) if isinstance(
            payload, dict) else payload
        if isinstance(instances, dict):
            instances = [instances]
        df = pd.DataFrame.from_records(instances)
        missing = [name for name in FEATURES if name not in df.columns]
        if missing:
            raise ValueError(f"Missing features: {missing}")
        df = df[FEATURES]
    else:
        raise ValueError(f"Unsupported content type: {request_content_type}")

    for column in NUMERIC_FEATURES:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    return df


def predict_fn(input_data, model):
    return model.predict_proba(input_data)[:, 1]


def output_fn(prediction, accept):
    if accept.split(";")[0].strip() == "text/csv":
        body = "\n".join(f"{value:.6f}" for value in prediction)
        return body, "text/csv"
    predictions = [{
        "churn_probability": round(float(value), 6),
        "churn": bool(value >= THRESHOLD),
    } for value in prediction]
    return json.dumps({
        "predictions": predictions
    }), "application/json"
