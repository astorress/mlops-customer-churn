import tarfile

import joblib

from src.models.train import MODEL_FILE_NAME
from src.pipelines.training.evaluate import evaluate, load_model


def test_evaluation_report(trained_model, splits):
    report = evaluate(trained_model, splits[2], threshold=0.5)
    metrics = report["binary_classification_metrics"]
    # Path read by the pipeline's CheckAuc condition (PropertyFile).
    assert metrics["auc"]["value"] > 0.7
    matrix = metrics["confusion_matrix"]
    total = sum(matrix[a][b] for a in "01" for b in "01")
    assert total == len(splits[2])


def test_load_model_from_training_job_archive(tmp_path, trained_model):
    joblib.dump(trained_model, tmp_path / MODEL_FILE_NAME)
    with tarfile.open(tmp_path / "model.tar.gz", "w:gz") as tar:
        tar.add(tmp_path / MODEL_FILE_NAME, arcname=MODEL_FILE_NAME)
    (tmp_path / MODEL_FILE_NAME).unlink()
    assert load_model(str(tmp_path)) is not None
