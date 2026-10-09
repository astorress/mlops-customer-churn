import json

from src.features.schema import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from src.pipelines.training import baseline as baseline_module
from src.pipelines.training.preprocess import (
    split,
    validate,
    write_outputs,
)


def test_baseline_step_contract(tmp_path, monkeypatch, curated_df):
    train, validation, test = split(validate(curated_df, min_rows=100), 0.2,
                                    0.2, 42)
    write_outputs(train, validation, test, str(tmp_path / "data"))
    output = tmp_path / "output"
    monkeypatch.setattr("sys.argv", [
        "baseline.py",
        "--input-dir",
        str(tmp_path / "data" / "baseline"),
        "--output-dir",
        str(output),
        "--psi-threshold",
        "0.25",
    ])

    baseline_module.main()

    profile = json.loads((output / "statistics.json").read_text())
    constraints = json.loads((output / "constraints.json").read_text())
    assert profile["method"] == "psi"
    assert profile["samples"] == len(train)
    assert set(profile["numeric"]) == set(NUMERIC_FEATURES)
    assert set(profile["categorical"]) == set(CATEGORICAL_FEATURES)
    assert constraints["psi_threshold"] == 0.25
