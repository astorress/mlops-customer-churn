"""Local paths and the public dataset URL used by the local scripts."""
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parents[2]
LOCAL_DATA_DIR = PROJECT_DIR / "data" / "local"
LOCAL_MODELS_DIR = PROJECT_DIR / "models" / "local"
RAW_DATASET_PATH = LOCAL_DATA_DIR / "telco_customer_churn.csv"
DATASET_URL = (
    "https://raw.githubusercontent.com/IBM/telco-customer-churn-on-icp4d/"
    "master/data/Telco-Customer-Churn.csv")
