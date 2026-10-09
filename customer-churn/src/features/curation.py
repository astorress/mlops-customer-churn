"""pandas mirror of the Glue curation job (src/jobs/glue/curate_customers.py),
used only for local experimentation (src.scripts.train_local) and tests.
Keep both in sync: the Glue job is the source of truth in AWS."""
import pandas as pd

from src.features.schema import normalize_category

RAW_TO_CURATED = {
    "customerID": "customer_id",
    "gender": "gender",
    "SeniorCitizen": "senior_citizen",
    "Partner": "partner",
    "Dependents": "dependents",
    "tenure": "tenure",
    "PhoneService": "phone_service",
    "MultipleLines": "multiple_lines",
    "InternetService": "internet_service",
    "OnlineSecurity": "online_security",
    "OnlineBackup": "online_backup",
    "DeviceProtection": "device_protection",
    "TechSupport": "tech_support",
    "StreamingTV": "streaming_tv",
    "StreamingMovies": "streaming_movies",
    "Contract": "contract",
    "PaperlessBilling": "paperless_billing",
    "PaymentMethod": "payment_method",
    "MonthlyCharges": "monthly_charges",
    "TotalCharges": "total_charges",
    "Churn": "churn",
}


def curate(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw.rename(columns=RAW_TO_CURATED)[list(RAW_TO_CURATED.values())]
    df = df.copy()
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    df["senior_citizen"] = pd.to_numeric(df["senior_citizen"]).astype(int)
    df["tenure"] = pd.to_numeric(df["tenure"]).astype(int)
    df["monthly_charges"] = pd.to_numeric(df["monthly_charges"])
    # Blank TotalCharges = brand-new customers (tenure 0) → null.
    df["total_charges"] = pd.to_numeric(df["total_charges"], errors="coerce")
    df["churn"] = (
        df["churn"].astype(str).str.strip().str.lower() == "yes").astype(int)
    for column in df.columns:
        if (pd.api.types.is_string_dtype(df[column]) and
                column != "customer_id"):
            df[column] = df[column].map(lambda value: value if pd.isna(value)
                                        else normalize_category(value))
    return df
