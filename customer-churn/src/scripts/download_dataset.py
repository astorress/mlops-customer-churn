"""Downloads the raw dataset to data/local/ (gitignored) for local work.

    python3 -m src.scripts.download_dataset
"""
import urllib.request

from src.scripts.paths import (
    DATASET_URL,
    LOCAL_DATA_DIR,
    RAW_DATASET_PATH,
)


def main():
    LOCAL_DATA_DIR.mkdir(parents=True, exist_ok=True)
    urllib.request.urlretrieve(DATASET_URL, RAW_DATASET_PATH)  # nosec B310
    print(f"Downloaded {DATASET_URL} → {RAW_DATASET_PATH}")


if __name__ == "__main__":
    main()
