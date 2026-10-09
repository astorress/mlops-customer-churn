# Testing — customer-churn

`npm test` (= `python3 -m pytest`, config `pytest.ini`: `pythonpath = .`, coverage of `src` to `htmlcov/`). No AWS,
no network, no Docker needed. Runs in the devcontainer (same `container/requirements.txt` as the model image).

## Layout (mirrors `src/`)

| Folder             | Covers                                                                                                                                                 |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `tests/features/`  | curation (pandas mirror of Glue), `normalize_category`                                                                                                 |
| `tests/pipelines/` | `preprocess` (Athena JSON Lines plain + gzip, validation gate, split, outputs) and `evaluate` (report path used by `CheckAuc`, `model.tar.gz` loading) |
| `tests/models/`    | training signal and the BYOC training contract (`/opt/ml/input/...` emulated with `tmp_path`, string hyperparameters, `/opt/ml/output/failure`)        |
| `tests/serving/`   | `inference` formats and `serve` (`/ping`, `/invocations` CSV/JSON, 400s) via Flask test client                                                         |
| `tests/functions/` | each Lambda handler with its `services` modules replaced by `MagicMock` (`monkeypatch.setattr(<handler module>, "<service>", mock)`)                   |
| `tests/services/`  | `athena.run_query` success/failure with a mocked `CLIENT`                                                                                              |

## Fixtures (`tests/conftest.py`)

- Sets dummy `AWS_DEFAULT_REGION`/keys **before** imports: `services` create boto3 clients at import time.
- `raw_df` — 1,500 synthetic rows with the raw IBM schema and a learnable signal; `curated_df`, `splits`
  (70/15/15-style split via `preprocess`), `trained_model` (50 iterations).

## Not covered by unit tests

- `src/jobs/glue/curate_customers.py` (needs a Glue/Spark runtime) — keep it in sync with `features/curation.py`.
- `src/scripts/*` (local CLIs).
- Real AWS behavior: pipeline definition validity, IAM, image manifest acceptance. Validate with `serverless package`
  and the image contract run in the `run-tests` skill.
