import os

import numpy as np
import pandas as pd
import pytest

# The services create their boto3 clients at import time.
os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")
os.environ.setdefault("AWS_ACCESS_KEY_ID", "testing")
os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "testing")

CATEGORIES = {
    "gender": ["Female", "Male"],
    "Partner": ["Yes", "No"],
    "Dependents": ["Yes", "No"],
    "PhoneService": ["Yes", "No"],
    "MultipleLines": ["Yes", "No", "No phone service"],
    "InternetService": ["DSL", "Fiber optic", "No"],
    "OnlineSecurity": ["Yes", "No", "No internet service"],
    "OnlineBackup": ["Yes", "No", "No internet service"],
    "DeviceProtection": ["Yes", "No", "No internet service"],
    "TechSupport": ["Yes", "No", "No internet service"],
    "StreamingTV": ["Yes", "No", "No internet service"],
    "StreamingMovies": ["Yes", "No", "No internet service"],
    "Contract": ["Month-to-month", "One year", "Two year"],
    "PaperlessBilling": ["Yes", "No"],
    "PaymentMethod": [
        "Electronic check",
        "Mailed check",
        "Bank transfer (automatic)",
        "Credit card (automatic)",
    ],
}


def make_raw(rows: int = 1500, seed: int = 0) -> pd.DataFrame:
    """Synthetic data with the raw IBM Telco schema and a learnable signal
    (short tenure + month-to-month + high charges → churn)."""
    rng = np.random.default_rng(seed)
    data = {
        "customerID": [f"{i:04d}-TEST" for i in range(rows)],
        "SeniorCitizen": rng.integers(0, 2, rows),
        "tenure": rng.integers(0, 72, rows),
        "MonthlyCharges": rng.uniform(18, 120, rows).round(2),
    }
    for column, values in CATEGORIES.items():
        data[column] = rng.choice(values, rows)
    df = pd.DataFrame(data)
    total = (df["tenure"] * df["MonthlyCharges"]).round(2).astype(str)
    df["TotalCharges"] = total.where(df["tenure"] > 0, " ")
    logit = (-1.0 - 0.05 * df["tenure"] + 0.02 * df["MonthlyCharges"] + 1.2 *
             (df["Contract"] == "Month-to-month"))
    churn = rng.random(rows) < 1 / (1 + np.exp(-logit))
    df["Churn"] = np.where(churn, "Yes", "No")
    return df


@pytest.fixture
def raw_df() -> pd.DataFrame:
    return make_raw()


@pytest.fixture
def curated_df(raw_df) -> pd.DataFrame:
    from src.features.curation import curate

    return curate(raw_df)


@pytest.fixture
def splits(curated_df):
    from src.pipelines.training.preprocess import split, validate

    return split(validate(curated_df, min_rows=100), 0.2, 0.2, 42)


@pytest.fixture
def trained_model(splits):
    from src.models.train import train

    return train(splits[0], {
        "max_iter": 50
    })
