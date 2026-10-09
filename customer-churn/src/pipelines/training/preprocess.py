"""SageMaker Processing step: validate the curated dataset and split it.

Input  (/opt/ml/processing/input/data): the curated table, delivered by the
        Athena dataset definition as JSON Lines files (optionally gzipped).
Output (/opt/ml/processing/<name>):
    train/train.csv            features + target, with header
    validation/validation.csv  features + target, with header
    test/test.csv              features + target + id, with header
    baseline/baseline.csv      features only, with header (drift
                               baseline: same shape as live endpoint traffic)
"""
import argparse
import gzip
import json
import logging
import os

import pandas as pd
from sklearn.model_selection import train_test_split

from src.features.schema import (
    FEATURES,
    ID_COLUMN,
    NUMERIC_FEATURES,
    TARGET,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = "/opt/ml/processing"


class DataValidationError(Exception):
    pass


def _read_json_lines(path: str) -> list[dict]:
    with open(path, "rb") as file:
        content = file.read()
    if content[:2] == b"\x1f\x8b":
        content = gzip.decompress(content)
    return [
        json.loads(line)
        for line in content.decode("utf-8").splitlines()
        if line.strip()
    ]


def read_dataset(input_dir: str) -> pd.DataFrame:
    records = []
    for root, _, files in os.walk(input_dir):
        for name in sorted(files):
            path = os.path.join(root, name)
            if name.endswith(".csv"):
                records.extend(pd.read_csv(path).to_dict("records"))
            elif not name.startswith(".") and not name.endswith(".metadata"):
                records.extend(_read_json_lines(path))
    return pd.DataFrame.from_records(records)


def validate(df: pd.DataFrame, min_rows: int) -> pd.DataFrame:
    """Data validation gate: a failure here stops the pipeline before any
    model is trained on bad data."""
    required = [ID_COLUMN, TARGET] + FEATURES
    missing = [column for column in required if column not in df.columns]
    if missing:
        raise DataValidationError(f"Missing columns: {missing}")

    df = df[required].copy()
    df = df.drop_duplicates(subset=[ID_COLUMN], keep="last")
    df = df[df[TARGET].notna()]

    if len(df) < min_rows:
        raise DataValidationError(
            f"Only {len(df)} labeled rows; at least {min_rows} are required")

    df[TARGET] = df[TARGET].astype(int)
    invalid_target = set(df[TARGET].unique()) - {0, 1}
    if invalid_target:
        raise DataValidationError(f"Invalid target values: {invalid_target}")

    for column in NUMERIC_FEATURES:
        df[column] = pd.to_numeric(df[column], errors="coerce")
    if (df["tenure"] < 0).any() or (df["monthly_charges"] < 0).any():
        raise DataValidationError("Negative tenure or monthly_charges found")

    positive_rate = df[TARGET].mean()
    logger.info("Validated %s rows (positive rate %.3f)", len(df),
                positive_rate)
    return df


def split(
    df: pd.DataFrame,
    test_size: float,
    validation_size: float,
    random_state: int,
):
    train_validation, test = train_test_split(
        df,
        test_size=test_size,
        stratify=df[TARGET],
        random_state=random_state,
    )
    relative_validation = validation_size / (1 - test_size)
    train, validation = train_test_split(
        train_validation,
        test_size=relative_validation,
        stratify=train_validation[TARGET],
        random_state=random_state,
    )
    return train, validation, test


def write_outputs(train, validation, test, base_dir: str) -> None:
    outputs = {
        "train": train[FEATURES + [TARGET]],
        "validation": validation[FEATURES + [TARGET]],
        "test": test[[ID_COLUMN] + FEATURES + [TARGET]],
        "baseline": train[FEATURES],
    }
    for name, frame in outputs.items():
        directory = os.path.join(base_dir, name)
        os.makedirs(directory, exist_ok=True)
        frame.to_csv(os.path.join(directory, f"{name}.csv"), index=False)
        logger.info("Wrote %s rows to %s", len(frame), directory)


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input-dir", default=f"{BASE_DIR}/input/data")
    parser.add_argument("--output-dir", default=BASE_DIR)
    parser.add_argument("--test-size", type=float, default=0.15)
    parser.add_argument("--validation-size", type=float, default=0.15)
    parser.add_argument("--min-rows", type=int, default=1000)
    parser.add_argument("--random-state", type=int, default=42)
    return parser.parse_args()


def main():
    args = parse_args()
    df = validate(read_dataset(args.input_dir), args.min_rows)
    train, validation, test = split(
        df,
        args.test_size,
        args.validation_size,
        args.random_state,
    )
    write_outputs(train, validation, test, args.output_dir)


if __name__ == "__main__":
    main()
