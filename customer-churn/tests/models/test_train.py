"""Training logic and SageMaker's training-job contract for the custom image
(`<image> train`): /opt/ml paths, string hyperparameters, failure file."""
import json

import joblib
import pytest

from src.models import train as train_module
from src.models.train import load_hyperparameters


def test_training_learns_signal(trained_model, splits):
    from src.pipelines.training.evaluate import evaluate

    auc = evaluate(trained_model, splits[2],
                   0.5)["binary_classification_metrics"]["auc"]["value"]
    assert auc > 0.7


def test_training_job_contract(tmp_path, monkeypatch, splits):
    train_df, validation_df, _ = splits
    for name, frame in (("train", train_df), ("validation", validation_df)):
        channel = tmp_path / "input" / "data" / name
        channel.mkdir(parents=True)
        frame.to_csv(channel / f"{name}.csv", index=False)
    config = tmp_path / "input" / "config"
    config.mkdir(parents=True)
    # SageMaker always sends strings.
    (config / "hyperparameters.json").write_text(
        json.dumps({
            "max_iter": "40",
            "learning_rate": "0.1",
        }))
    monkeypatch.setattr(train_module, "BASE_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["train.py"])

    train_module.main()

    model = joblib.load(tmp_path / "model" / train_module.MODEL_FILE_NAME)
    assert model.named_steps["classifier"].max_iter == 40


def test_hyperparameters_cast_and_override(tmp_path):
    path = tmp_path / "hyperparameters.json"
    path.write_text(json.dumps({
        "max_depth": "6",
        "learning_rate": "0.2",
    }))
    params = load_hyperparameters(path, {
        "learning_rate": 0.3
    })
    assert params["max_depth"] == 6
    assert params["learning_rate"] == 0.3
    assert params["class_weight"] == "balanced"


def test_training_failure_is_reported(tmp_path, monkeypatch):
    monkeypatch.setattr(train_module, "BASE_DIR", tmp_path)
    monkeypatch.setattr("sys.argv", ["train.py"])
    with pytest.raises(Exception):
        train_module.main()
    assert (tmp_path / "output" / "failure").read_text()
