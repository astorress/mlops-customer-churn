"""Model server for SageMaker endpoints and Batch Transform (custom image,
`docker run <image> serve` → gunicorn serve:app on port 8080).

SageMaker's hosting contract:
    GET  /ping         200 when the container is ready (model loaded)
    POST /invocations  Content-Type / Accept headers pick the formats
                       (see inference.py)
"""
import logging
import os
from functools import lru_cache

from flask import (
    Flask,
    Response,
    request,
)

from src.serving.inference import (
    input_fn,
    model_fn,
    output_fn,
    predict_fn,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_DIR = os.environ.get("SM_MODEL_DIR", "/opt/ml/model")

app = Flask(__name__)


@lru_cache(maxsize=1)
def get_model():
    logger.info("Loading model from %s", MODEL_DIR)
    return model_fn(MODEL_DIR)


@app.get("/ping")
def ping():
    try:
        get_model()
    except Exception:
        logger.exception("Model not loadable")
        return Response(status=503)
    return Response(status=200)


@app.post("/invocations")
def invocations():
    content_type = request.content_type or "text/csv"
    accept = request.headers.get("Accept", "application/json")
    if accept in ("*/*", ""):
        accept = "application/json"
    try:
        data = input_fn(request.get_data(), content_type.split(";")[0])
    except ValueError as error:
        return Response(str(error), status=400, mimetype="text/plain")
    body, mimetype = output_fn(predict_fn(data, get_model()), accept)
    return Response(body, status=200, mimetype=mimetype)
