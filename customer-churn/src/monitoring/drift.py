"""Data drift with the Population Stability Index (PSI).

Pure Python on purpose: the same code builds the reference profile inside the
training pipeline (model image) and measures drift in the DataDrift Lambda
(no dependencies), so both always agree on bins and categories.

    PSI = Σ (actual% − expected%) · ln(actual% / expected%)
    < 0.1 no significant change · 0.1–0.2 moderate · > 0.2 significant

Numeric features are bucketed with the training quantiles (≈ equal-frequency
bins); categorical features compare category frequencies, with unseen
categories grouped as "__other__". Missing values have their own bucket.
"""
import math
from bisect import bisect_right

NULL = "__null__"
OTHER = "__other__"
EPSILON = 1e-4
DEFAULT_PSI_THRESHOLD = 0.2
DEFAULT_MIN_SAMPLES = 30


def _is_null(value) -> bool:
    if value is None:
        return True
    if isinstance(value, float) and math.isnan(value):
        return True
    return isinstance(value, str) and value.strip() in ("", "\\N", "nan")


def _to_float(value):
    if _is_null(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _quantile_edges(values: list, bins: int) -> list:
    """Interior cut points of ~equal-frequency bins (duplicates removed)."""
    if not values:
        return []
    ordered = sorted(values)
    edges = {
        ordered[min(len(ordered) - 1, (len(ordered) * i) // bins)]
        for i in range(1, bins)
    }
    return sorted(edges)


def _normalize(counts: dict, total: int) -> dict:
    return {
        key: count / total if total else 0.0
        for key, count in counts.items()
    }


def numeric_distribution(values: list, edges: list) -> dict:
    counts = {
        str(index): 0
        for index in range(len(edges) + 1)
    }
    counts[NULL] = 0
    for value in values:
        number = _to_float(value)
        key = NULL if number is None else str(bisect_right(edges, number))
        counts[key] += 1
    return _normalize(counts, len(values))


def categorical_distribution(values: list, known: set | None = None) -> dict:
    counts = {
        key: 0
        for key in known or ()
    }
    for value in values:
        if _is_null(value):
            key = NULL
        else:
            key = str(value).strip()
            if known is not None and key not in known:
                key = OTHER
        counts[key] = counts.get(key, 0) + 1
    return _normalize(counts, len(values))


def psi(expected: dict, actual: dict) -> float:
    total = 0.0
    for key in set(expected) | set(actual):
        e = max(expected.get(key, 0.0), EPSILON)
        a = max(actual.get(key, 0.0), EPSILON)
        total += (a - e) * math.log(a / e)
    return total


def build_profile(rows: list,
                  numeric: list,
                  categorical: list,
                  bins: int = 10) -> dict:
    """Reference profile of the training data (stored with the model)."""
    profile = {
        "method": "psi",
        "samples": len(rows),
        "numeric": {},
        "categorical": {},
    }
    for feature in numeric:
        values = [row.get(feature) for row in rows]
        numbers = [n for n in map(_to_float, values) if n is not None]
        edges = _quantile_edges(numbers, bins)
        profile["numeric"][feature] = {
            "edges": edges,
            "expected": numeric_distribution(values, edges),
        }
    for feature in categorical:
        values = [row.get(feature) for row in rows]
        profile["categorical"][feature] = {
            "expected": categorical_distribution(values),
        }
    return profile


def evaluate(profile: dict, constraints: dict, rows: list) -> dict:
    """Drift report of live rows against the reference profile."""
    threshold = float(constraints.get("psi_threshold", DEFAULT_PSI_THRESHOLD))
    min_samples = int(constraints.get("min_samples", DEFAULT_MIN_SAMPLES))
    report = {
        "samples": len(rows),
        "psi_threshold": threshold,
        "min_samples": min_samples,
        "features": {},
        "drifted_features": [],
        "max_psi": None,
    }
    if len(rows) < min_samples:
        report["status"] = "insufficient_data"
        return report

    for feature, spec in profile["numeric"].items():
        actual = numeric_distribution(
            [row.get(feature) for row in rows],
            spec["edges"],
        )
        report["features"][feature] = psi(spec["expected"], actual)
    for feature, spec in profile["categorical"].items():
        known = set(spec["expected"])
        actual = categorical_distribution(
            [row.get(feature) for row in rows],
            known,
        )
        report["features"][feature] = psi(spec["expected"], actual)

    report["drifted_features"] = sorted(
        feature for feature, value in report["features"].items()
        if value > threshold)
    report["max_psi"] = max(report["features"].values(), default=0.0)
    report["status"] = "drift" if report["drifted_features"] else "ok"
    return report
