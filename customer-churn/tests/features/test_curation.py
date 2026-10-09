from src.features.curation import curate
from src.features.schema import (
    FEATURES,
    ID_COLUMN,
    TARGET,
    normalize_category,
)


def test_normalize_category():
    assert normalize_category("Month-to-month") == "month_to_month"
    assert normalize_category(" Bank transfer (automatic) ") == (
        "bank_transfer_automatic")
    assert normalize_category(None) is None


def test_curate_schema_and_types(raw_df):
    df = curate(raw_df)
    assert set([ID_COLUMN, TARGET] + FEATURES) == set(df.columns)
    assert set(df[TARGET].unique()) <= {0, 1}
    assert df["contract"].isin(["month_to_month", "one_year", "two_year"]).all()


def test_blank_total_charges_become_null(raw_df):
    df = curate(raw_df)
    assert df.loc[df["tenure"] == 0, "total_charges"].isna().all()
    assert df.loc[df["tenure"] > 0, "total_charges"].notna().all()
