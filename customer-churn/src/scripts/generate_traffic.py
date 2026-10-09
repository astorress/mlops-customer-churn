"""Sends sampled customers to the online model to fill the endpoint's data
capture, so the DataDrift monitor has traffic to compare against the baseline.

    python3 -m src.scripts.generate_traffic --api-url https://.../predict
    python3 -m src.scripts.generate_traffic --endpoint-name customer-churn \
        --requests 300 --drift

--drift inflates prices and shortens tenure: the next hourly DataDrift run
should report drift (and the drift alarm should fire).
"""
import argparse
import json
import random
import time
import urllib.request

import pandas as pd

from src.features.curation import curate
from src.features.schema import FEATURES, ID_COLUMN
from src.scripts.paths import RAW_DATASET_PATH
from src.services import sagemaker_runtime


def load_customers(drift: bool, seed: int) -> list:
    df = curate(pd.read_csv(RAW_DATASET_PATH))
    rng = random.Random(seed)
    if drift:
        df["monthly_charges"] = df["monthly_charges"].apply(
            lambda value: round(value * rng.uniform(1.3, 1.8), 2))
        df["tenure"] = (df["tenure"] * 0.3).astype(int)
    df = df.astype(object).where(df.notna(), None)
    return df[[ID_COLUMN] + FEATURES].to_dict("records")


def send_api(url: str, customers: list) -> dict:
    request = urllib.request.Request(
        url,
        data=json.dumps({
            "customers": customers
        }).encode("utf-8"),
        headers={
            "Content-Type": "application/json"
        },
        method="POST",
    )
    with urllib.request.urlopen(request) as response:  # nosec B310
        return json.loads(response.read())


def send_endpoint(endpoint_name: str, customers: list) -> dict:
    rows = "\n".join(",".join("" if row[name] is None else str(row[name])
                              for name in FEATURES)
                     for row in customers)
    body = sagemaker_runtime.invoke_endpoint(
        endpoint_name,
        rows.encode("utf-8"),
        content_type="text/csv",
        accept="application/json",
    )
    return json.loads(body)


def main():
    parser = argparse.ArgumentParser()
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--api-url")
    target.add_argument("--endpoint-name")
    parser.add_argument("--requests", type=int, default=100)
    parser.add_argument("--batch-size", type=int, default=5)
    parser.add_argument("--sleep", type=float, default=0.2)
    parser.add_argument("--drift", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()

    customers = load_customers(args.drift, args.seed)
    rng = random.Random(args.seed)

    for index in range(args.requests):
        batch = rng.sample(customers, args.batch_size)
        if args.api_url:
            result = send_api(args.api_url, batch)
        else:
            result = send_endpoint(args.endpoint_name, batch)
        if index % 10 == 0:
            print(f"[{index}/{args.requests}] {result['predictions'][0]}")
        time.sleep(args.sleep)


if __name__ == "__main__":
    main()
