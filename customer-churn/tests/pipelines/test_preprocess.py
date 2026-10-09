import gzip
import json
import os

import pandas as pd
import pytest

from src.features.schema import (
    FEATURES,
    ID_COLUMN,
    TARGET,
)
from src.pipelines.training.preprocess import (
    DataValidationError,
    read_dataset,
    split,
    validate,
    write_outputs,
)


def test_read_dataset_json_lines_plain_and_gzip(tmp_path, curated_df):
    records = curated_df.head(10).to_dict("records")
    lines = "\n".join(json.dumps(record) for record in records)
    (tmp_path / "part-0").write_text(lines[:len(lines) // 2].rsplit("\n", 1)[0])
    half = len(lines[:len(lines) // 2].rsplit("\n", 1)[0].splitlines())
    rest = "\n".join(json.dumps(record) for record in records[half:])
    (tmp_path / "part-1.gz").write_bytes(gzip.compress(rest.encode()))
    df = read_dataset(str(tmp_path))
    assert len(df) == 10


def test_validate_rejects_missing_columns(curated_df):
    with pytest.raises(DataValidationError, match="Missing columns"):
        validate(curated_df.drop(columns=["tenure"]), min_rows=10)


def test_validate_rejects_too_few_rows(curated_df):
    with pytest.raises(DataValidationError, match="at least"):
        validate(curated_df.head(50), min_rows=100)


def test_validate_drops_duplicates(curated_df):
    duplicated = pd.concat([curated_df, curated_df.head(20)])
    assert len(validate(duplicated, min_rows=10)) == len(curated_df)


def test_split_and_outputs(tmp_path, curated_df):
    df = validate(curated_df, min_rows=100)
    train, validation, test = split(df, 0.15, 0.15, 42)
    assert len(train) + len(validation) + len(test) == len(df)
    assert abs(len(test) / len(df) - 0.15) < 0.01

    write_outputs(train, validation, test, str(tmp_path))
    baseline = pd.read_csv(tmp_path / "baseline" / "baseline.csv")
    assert list(baseline.columns) == FEATURES
    test_out = pd.read_csv(tmp_path / "test" / "test.csv")
    assert list(test_out.columns) == [ID_COLUMN] + FEATURES + [TARGET]
    assert os.path.exists(tmp_path / "train" / "train.csv")
