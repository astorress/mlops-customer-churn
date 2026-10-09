import io
from unittest.mock import MagicMock

import pandas as pd

from src.functions.ingestion import ingest_dataset


def test_transform_sample_and_drift(raw_df):
    content = raw_df.to_csv(index=False)
    sampled = ingest_dataset.transform(content, 0.1, False, 1)
    assert len(sampled.strip().splitlines()) == 1 + 150

    drifted = pd.read_csv(
        io.StringIO(ingest_dataset.transform(content, 1, True, 1)))
    assert drifted["MonthlyCharges"].mean() > raw_df["MonthlyCharges"].mean()


def test_handler_writes_raw_partition(monkeypatch, raw_df):
    s3 = MagicMock()
    monkeypatch.setattr(ingest_dataset, "s3", s3)
    monkeypatch.setattr(ingest_dataset, "download",
                        lambda url: raw_df.to_csv(index=False))
    monkeypatch.setattr(ingest_dataset, "DATA_LAKE_BUCKET_NAME", "lake")

    result = ingest_dataset.handler({
        "ingestion_date": "2026-01-02"
    }, None)

    bucket, key = s3.put_object.call_args.args[:2]
    assert bucket == "lake"
    assert "/ingestion_date=2026-01-02/" in key
    assert result["rows"] == len(raw_df)
