"""Data contract shared by every ML step (preprocess, train, inference,
evaluate) and by the batch/online clients.

The column order of FEATURES is the order of a headerless CSV row sent to the
model (endpoint, Batch Transform and the drift monitor). Changing it is a
breaking change for every consumer: bump the model version and redeploy all
of them together.
"""
import re

ID_COLUMN = "customer_id"
TARGET = "churn"

NUMERIC_FEATURES = [
    "senior_citizen",
    "tenure",
    "monthly_charges",
    "total_charges",
]

CATEGORICAL_FEATURES = [
    "gender",
    "partner",
    "dependents",
    "phone_service",
    "multiple_lines",
    "internet_service",
    "online_security",
    "online_backup",
    "device_protection",
    "tech_support",
    "streaming_tv",
    "streaming_movies",
    "contract",
    "paperless_billing",
    "payment_method",
]

FEATURES = NUMERIC_FEATURES + CATEGORICAL_FEATURES


def normalize_category(value):
    """'Month-to-month' → 'month_to_month' (same rule as the Glue job)."""
    if value is None:
        return None
    text = re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower())
    return text.strip("_")
