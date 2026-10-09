"""Runs the whole training flow on your machine, without AWS:
raw CSV → curation (pandas mirror of Glue) → validation/split (preprocess)
→ training → evaluation. Same code the SageMaker Pipeline runs.

    python3 -m src.scripts.download_dataset
    python3 -m src.scripts.train_local --max_iter 200
"""
import argparse
import json
import shutil

import joblib
import pandas as pd

from src.features.curation import curate
from src.models.estimator import DEFAULT_HYPERPARAMETERS
from src.models.train import (
    MODEL_FILE_NAME,
    log_metrics,
    train,
)
from src.pipelines.training.evaluate import evaluate
from src.pipelines.training.preprocess import (
    split,
    validate,
    write_outputs,
)
from src.scripts.paths import (
    LOCAL_DATA_DIR,
    LOCAL_MODELS_DIR,
    RAW_DATASET_PATH,
)


def parse_args():
    parser = argparse.ArgumentParser()
    for name, default in DEFAULT_HYPERPARAMETERS.items():
        parser.add_argument(f"--{name}", type=type(default), default=default)
    parser.add_argument("--threshold", type=float, default=0.5)
    return parser.parse_args()


def main():
    args = parse_args()
    hyperparameters = {
        name: getattr(args, name)
        for name in DEFAULT_HYPERPARAMETERS
    }
    curated = curate(pd.read_csv(RAW_DATASET_PATH))
    df = validate(curated, min_rows=1000)
    train_df, validation_df, test_df = split(df, 0.15, 0.15, 42)

    splits_dir = LOCAL_DATA_DIR / "splits"
    shutil.rmtree(splits_dir, ignore_errors=True)
    write_outputs(train_df, validation_df, test_df, splits_dir)

    model = train(train_df, hyperparameters)
    log_metrics("validation", model, validation_df)
    report = evaluate(model, test_df, args.threshold)

    LOCAL_MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(model, LOCAL_MODELS_DIR / MODEL_FILE_NAME)
    with open(
            LOCAL_MODELS_DIR / "evaluation.json",
            "w",
            encoding="utf-8",
    ) as file:
        json.dump(report, file, indent=2)
    print(json.dumps(report["binary_classification_metrics"], indent=2))


if __name__ == "__main__":
    main()
