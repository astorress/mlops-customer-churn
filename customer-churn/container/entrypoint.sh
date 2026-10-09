#!/bin/sh
# SageMaker contract: training runs the image with `train`, endpoints and
# Batch Transform with `serve`. Processing jobs override the entrypoint.
set -e

case "$1" in
  train)
    exec python3 -m src.models.train
    ;;
  serve)
    exec gunicorn src.serving.serve:app \
      --bind "0.0.0.0:${SAGEMAKER_BIND_TO_PORT:-8080}" \
      --workers "${MODEL_SERVER_WORKERS:-2}" \
      --timeout "${MODEL_SERVER_TIMEOUT:-60}" \
      --access-logfile -
    ;;
  *)
    exec "$@"
    ;;
esac
