"""SageMaker hosting contract of the custom image (`<image> serve`)."""
import json

import joblib
import pytest

from src.features.schema import FEATURES, TARGET
from src.models.train import MODEL_FILE_NAME
from src.serving import serve


@pytest.fixture
def client(tmp_path, monkeypatch, trained_model):
    joblib.dump(trained_model, tmp_path / MODEL_FILE_NAME)
    monkeypatch.setattr(serve, "MODEL_DIR", str(tmp_path))
    serve.get_model.cache_clear()
    yield serve.app.test_client()
    serve.get_model.cache_clear()


def test_ping(client):
    assert client.get("/ping").status_code == 200


def test_ping_without_model(tmp_path, monkeypatch):
    monkeypatch.setattr(serve, "MODEL_DIR", str(tmp_path / "missing"))
    serve.get_model.cache_clear()
    assert serve.app.test_client().get("/ping").status_code == 503
    serve.get_model.cache_clear()


def test_invocations_csv_to_json(client, splits):
    rows = splits[2].drop(columns=["customer_id", TARGET]).head(3)
    response = client.post(
        "/invocations",
        data=rows.to_csv(header=False, index=False),
        content_type="text/csv",
        headers={
            "Accept": "application/json"
        },
    )
    assert response.status_code == 200
    assert len(response.get_json()["predictions"]) == 3


def test_invocations_csv_to_csv_for_batch_transform(client, splits):
    rows = splits[2][FEATURES].head(4)
    response = client.post(
        "/invocations",
        data=rows.to_csv(header=False, index=False),
        content_type="text/csv",
        headers={
            "Accept": "text/csv"
        },
    )
    assert response.mimetype == "text/csv"
    assert len(response.get_data(as_text=True).splitlines()) == 4


def test_invocations_rejects_bad_payload(client):
    response = client.post(
        "/invocations",
        data=json.dumps({
            "instances": [{
                "tenure": 1
            }]
        }),
        content_type="application/json",
    )
    assert response.status_code == 400
