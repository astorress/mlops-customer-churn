"""SageMaker Training step (custom image, `docker run <image> train`).

SageMaker's training contract (no toolkit involved):
    /opt/ml/input/config/hyperparameters.json  hyperparameters (all strings)
    /opt/ml/input/data/<channel>/              train, validation
    /opt/ml/model/                             saved model → model.tar.gz
    /opt/ml/output/failure                     failure reason shown by the job

Metrics are printed as `<split>:<metric>=<value>` so the training job's
MetricDefinitions capture them (SageMaker Experiments / CloudWatch).
CLI flags override hyperparameters for local runs.
"""
import argparse
import json
import logging
import os
import traceback
from pathlib import Path
from typing import Any

import joblib
import pandas as pd

from src.features.schema import FEATURES, TARGET
from src.models.estimator import DEFAULT_HYPERPARAMETERS, build_pipeline
from src.models.metrics import compute_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODEL_FILE_NAME = "model.joblib"
BASE_DIR = Path(os.environ.get("SAGEMAKER_BASE_DIR", "/opt/ml"))


def load_split(channel_dir: str | Path) -> pd.DataFrame:
    files = sorted(Path(channel_dir).glob("*.csv"))
    return pd.concat([pd.read_csv(path) for path in files], ignore_index=True)


def load_hyperparameters(path: Path, overrides: dict[str, Any]) -> dict:
    """SageMaker passes every hyperparameter as a string: cast each one to
    the type of its default."""
    provided = json.loads(path.read_text()) if path.exists() else {}
    unknown = set(provided) - set(DEFAULT_HYPERPARAMETERS)
    if unknown:
        logger.warning("Ignoring unknown hyperparameters: %s", unknown)
    hyperparameters = {}
    for name, default in DEFAULT_HYPERPARAMETERS.items():
        value = overrides.get(name)
        if value is None:
            value = provided.get(name, default)
        hyperparameters[name] = type(default)(value)
    return hyperparameters


def train(train_df: pd.DataFrame, hyperparameters: dict):
    pipeline = build_pipeline(hyperparameters)
    pipeline.fit(train_df[FEATURES], train_df[TARGET])
    return pipeline


def log_metrics(split_name: str, pipeline, df: pd.DataFrame) -> dict:
    scores = pipeline.predict_proba(df[FEATURES])[:, 1]
    metrics = compute_metrics(df[TARGET].values, scores)
    for name in ("auc", "average_precision", "f1", "precision", "recall"):
        value = metrics["binary_classification_metrics"][name]["value"]
        print(f"{split_name}:{name}={value:.6f}")
    return metrics


def parse_args():
    parser = argparse.ArgumentParser()
    for name, default in DEFAULT_HYPERPARAMETERS.items():
        parser.add_argument(f"--{name}", type=type(default), default=None)
    return parser.parse_args()


def run(overrides: dict[str, Any]) -> None:
    hyperparameters = load_hyperparameters(
        BASE_DIR / "input" / "config" / "hyperparameters.json",
        overrides,
    )
    logger.info("Hyperparameters: %s", hyperparameters)

    data_dir = BASE_DIR / "input" / "data"
    train_df = load_split(data_dir / "train")
    pipeline = train(train_df, hyperparameters)
    log_metrics("train", pipeline, train_df)
    if (data_dir / "validation").exists():
        log_metrics("validation", pipeline, load_split(data_dir / "validation"))

    model_dir = BASE_DIR / "model"
    model_dir.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, model_dir / MODEL_FILE_NAME)
    logger.info("Model saved to %s", model_dir)


def main():
    try:
        run(vars(parse_args()))
    except Exception:
        failure = BASE_DIR / "output" / "failure"
        failure.parent.mkdir(parents=True, exist_ok=True)
        failure.write_text(traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
