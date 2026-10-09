import random

import pytest

from src.features.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from src.monitoring.drift import (
    NULL,
    OTHER,
    build_profile,
    categorical_distribution,
    evaluate,
    numeric_distribution,
    psi,
)


@pytest.fixture
def rows(curated_df):
    return curated_df.astype(object).where(curated_df.notna(),
                                           None).to_dict("records")


@pytest.fixture
def profile(rows):
    return build_profile(rows, NUMERIC_FEATURES, CATEGORICAL_FEATURES)


def test_psi_is_zero_for_identical_distributions():
    assert psi({
        "a": 0.5,
        "b": 0.5
    }, {
        "a": 0.5,
        "b": 0.5
    }) == pytest.approx(0)


def test_psi_grows_with_the_shift():
    expected = {
        "a": 0.5,
        "b": 0.5
    }
    small = psi(expected, {
        "a": 0.55,
        "b": 0.45
    })
    large = psi(expected, {
        "a": 0.9,
        "b": 0.1
    })
    assert 0 < small < large


def test_numeric_distribution_buckets_and_nulls():
    distribution = numeric_distribution([1, 5, 9, None, "\\N"], [3, 7])
    assert distribution == {
        "0": 0.2,
        "1": 0.2,
        "2": 0.2,
        NULL: 0.4,
    }


def test_categorical_distribution_groups_unseen_values():
    distribution = categorical_distribution(["a", "b", "z"], {"a", "b"})
    assert distribution[OTHER] == pytest.approx(1 / 3)


def test_profile_covers_every_feature(profile, rows):
    assert profile["samples"] == len(rows)
    assert set(profile["numeric"]) == set(NUMERIC_FEATURES)
    assert set(profile["categorical"]) == set(CATEGORICAL_FEATURES)
    assert sum(
        profile["numeric"]["tenure"]["expected"].values()) == (pytest.approx(1))


def test_same_data_has_no_drift(profile, rows):
    report = evaluate(profile, {}, rows)
    assert report["status"] == "ok"
    assert report["max_psi"] < 0.01


def test_shifted_prices_are_detected(profile, rows):
    rng = random.Random(1)
    drifted = [{
        **row,
        "monthly_charges":
            row["monthly_charges"] * rng.uniform(1.4, 1.8),
    } for row in rows]
    report = evaluate(profile, {
        "psi_threshold": 0.2
    }, drifted)
    assert report["status"] == "drift"
    assert "monthly_charges" in report["drifted_features"]


def test_too_few_samples(profile, rows):
    report = evaluate(profile, {
        "min_samples": 100
    }, rows[:10])
    assert report["status"] == "insufficient_data"
    assert report["max_psi"] is None
