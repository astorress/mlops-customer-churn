"""Ingestion: downloads the public Telco Customer Churn dataset into the raw
zone of the data lake (raw/<project>/ingestion_date=YYYY-MM-DD/).

The new object triggers (S3 → EventBridge) the Glue workflow, which curates
the data and, on success, starts the SageMaker training pipeline.

Event (all optional):
    ingestion_date   "YYYY-MM-DD" (default: today, UTC)
    sample_fraction  0 < f <= 1, random subset of rows (default: 1)
    simulate_drift   true → shifts prices/contracts to emulate a market change
    seed             random seed (default: 42)
"""
import csv
import io
import json
import os
import random
import urllib.request
from datetime import datetime, timezone

from src.services import s3
from src.utilities.logger import get_logger

logger = get_logger(__name__)

DATASET_URL = os.environ.get("DATASET_URL", "")
DATA_LAKE_BUCKET_NAME = os.environ.get("DATA_LAKE_BUCKET_NAME", "")
RAW_PREFIX = os.environ.get("RAW_PREFIX", "raw/customer_churn")
FILE_NAME = "telco_customer_churn.csv"


def download(url: str) -> str:
    with urllib.request.urlopen(url, timeout=60) as response:  # nosec B310
        return response.read().decode("utf-8")


def apply_drift(rows: list, rng: random.Random) -> list:
    """Emulates a market shift: higher prices and more month-to-month
    contracts. Useful to watch drift monitoring and retraining react."""
    for row in rows:
        charges = float(row["MonthlyCharges"])
        row["MonthlyCharges"] = f"{charges * rng.uniform(1.15, 1.40):.2f}"
        if rng.random() < 0.3:
            row["Contract"] = "Month-to-month"
    return rows


def transform(content: str, sample_fraction: float, simulate_drift: bool,
              seed: int) -> str:
    reader = csv.DictReader(io.StringIO(content))
    rows = list(reader)
    rng = random.Random(seed)
    if sample_fraction < 1:
        rows = rng.sample(rows, max(1, int(len(rows) * sample_fraction)))
    if simulate_drift:
        rows = apply_drift(rows, rng)

    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=reader.fieldnames)
    writer.writeheader()
    writer.writerows(rows)
    return output.getvalue()


def handler(event, context):
    event = event or {}
    ingestion_date = event.get("ingestion_date") or datetime.now(
        timezone.utc).strftime("%Y-%m-%d")
    sample_fraction = float(event.get("sample_fraction", 1))
    simulate_drift = bool(event.get("simulate_drift", False))
    seed = int(event.get("seed", 42))

    body = transform(
        download(DATASET_URL),
        sample_fraction,
        simulate_drift,
        seed,
    )
    key = f"{RAW_PREFIX}/ingestion_date={ingestion_date}/{FILE_NAME}"
    s3.put_object(DATA_LAKE_BUCKET_NAME, key, body.encode("utf-8"), "text/csv")
    result = {
        "bucket": DATA_LAKE_BUCKET_NAME,
        "key": key,
        "rows": body.count("\n") - 1,
        "simulate_drift": simulate_drift,
    }
    logger.info(json.dumps(result))
    return result
