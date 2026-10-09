"""SageMaker Processing step: score the held-out test split with the trained
model and write evaluation.json.

The report feeds three things:
    * the pipeline ConditionStep (PropertyFile → binary_classification_metrics
      .auc.value) that decides whether the model is registered,
    * the model package ModelMetrics (Model Registry "Model quality" tab),
    * humans reviewing the model before approving it.
"""
import argparse
import json
import logging
import os
import tarfile

import joblib
import pandas as pd

from src.features.schema import FEATURES, TARGET
from src.models.metrics import compute_metrics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = "/opt/ml/processing"
MODEL_FILE_NAME = "model.joblib"


def load_model(model_dir: str):
    archive = os.path.join(model_dir, "model.tar.gz")
    if os.path.exists(archive):
        with tarfile.open(archive) as tar:
            tar.extractall(path=model_dir, filter="data")
    return joblib.load(os.path.join(model_dir, MODEL_FILE_NAME))


def evaluate(model, test_df: pd.DataFrame, threshold: float) -> dict:
    scores = model.predict_proba(test_df[FEATURES])[:, 1]
    return compute_metrics(test_df[TARGET].values, scores, threshold)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model-dir", default=f"{BASE_DIR}/model")
    parser.add_argument("--test-dir", default=f"{BASE_DIR}/test")
    parser.add_argument("--output-dir", default=f"{BASE_DIR}/evaluation")
    parser.add_argument("--threshold", type=float, default=0.5)
    return parser.parse_args()


def main():
    args = parse_args()
    model = load_model(args.model_dir)
    test_df = pd.read_csv(os.path.join(args.test_dir, "test.csv"))
    report = evaluate(model, test_df, args.threshold)
    logger.info("Evaluation report: %s", json.dumps(report))

    os.makedirs(args.output_dir, exist_ok=True)
    with open(
            os.path.join(args.output_dir, "evaluation.json"),
            "w",
            encoding="utf-8",
    ) as file:
        json.dump(report, file, indent=2)


if __name__ == "__main__":
    main()
