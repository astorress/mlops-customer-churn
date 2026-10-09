---
name: debug-pipeline-execution
description: Maps customer-churn failures — Glue workflow/job, pipeline steps, registration, approval Lambda, endpoint deploy, monitoring, Predict API, batch scoring, image push — to source files and probable causes. Use when an execution, job, deploy or request of customer-churn fails or behaves unexpectedly.
---

# Debug customer-churn

Find the failing component first: Glue console (workflow run), SageMaker → Pipelines (failed step → logs), CloudWatch
logs of the Lambda, or the deploy output. Read-only AWS commands are fine to run when the owner asks.

## Ingestion / curation

| Symptom                                                           | Cause                                                                                            | Where                                                                                                      |
| ----------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | ---------------------------------------------------------------------------------------------------------- |
| Upload to `raw/` but workflow never starts                        | data lake EventBridge flag off, rule key prefix mismatch, or still inside the 120 s batch window | `../infrastructure/serverless/common/s3.yml`, `serverless/data/events.yml`, `custom.glue.eventBatchWindow` |
| Job fails `Data quality rules failed: …`                          | the DQ gate worked: data broke a rule (e.g. `RowCount > 500` with a small `sample_fraction`)     | `custom.glue.dataQualityRuleset`, job logs                                                                 |
| Job fails reading raw                                             | missing `ingestion_date=` partition folder or header changed                                     | `src/jobs/glue/curate_customers.py`                                                                        |
| Job fails `not authorized to perform: s3:PutObject ... _$folder$` | EMRFS folder markers outside the allowed prefixes                                                | marker ARNs in `GlueRole` (`serverless/data/iam.yml`); redeploy `data`                                     |
| Athena returns 0 rows for curated                                 | partition projection range (`2024-01-01,NOW`) or path not Hive-style                             | `CuratedTable` in `serverless/data/glue.yml`                                                               |

## Pipeline steps

| Step / symptom                                                   | Cause                                                                                                                          | Where                                                                                  |
| ---------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------- |
| Execution never starts after curation                            | `pipeline` not deployed, or `CurationSucceededRule` job name mismatch                                                          | `serverless/pipeline/events.yml`                                                       |
| `CannotPullContainerError`                                       | image tag not pushed, or role lacks ECR pull                                                                                   | `npm run image:push`; `SageMakerExecutionRole` in `pipeline/iam.yml`                   |
| `exec format error`                                              | image built for arm64                                                                                                          | `container/build-push.sh` (`--platform linux/amd64`)                                   |
| `PrepareData`: Athena access/denied or empty input               | workgroup/catalog permissions, or no curated partition yet                                                                     | `pipeline/iam.yml`, `pipeline/athena.yml`                                              |
| `PrepareData`: `Data download failed ... matched no files on s3` | the Athena query returned 0 rows: no curated partition yet (pipeline started before the Glue job succeeded, or the job failed) | check the Glue job run; let `CurationSucceededRule` start the pipeline                 |
| `PrepareData`: `DataValidationError`                             | validation gate (missing columns, < `MinRows`, bad target, negatives)                                                          | `src/pipelines/training/preprocess.py`                                                 |
| `Train` fails                                                    | read `/opt/ml/output/failure` (shown as the job's failure reason)                                                              | `src/models/train.py`                                                                  |
| `Baseline` fails                                                 | no rows in `baseline/baseline.csv` or module missing from the image                                                            | `src/pipelines/training/baseline.py`, `container/Dockerfile` (`src/monitoring` copied) |
| `Evaluate` / `CheckAuc` can't read property                      | `evaluation.json` path or key changed                                                                                          | `evaluate.py`, PropertyFile in `pipeline-definition.js`                                |
| Ends in `FailLowAuc`                                             | model below `MinRocAuc` (expected behavior)                                                                                    | `MIN_ROC_AUC` / pipeline parameter                                                     |
| `RegisterModel` fails                                            | group missing, instance types not allowed, baseline URIs                                                                       | `pipeline/sagemaker.yml`, `custom.registry`                                            |

## Approval → deploy

| Symptom                                                                                              | Cause                                                                                            | Where                                                                                                                                  |
| ---------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------------------------- |
| Approved but SSM still `none`                                                                        | `OnModelApproved` not triggered (group filter) or failed (`MissingBaselineError`)                | `pipeline/functions.yml`, Lambda logs, `src/functions/registry/on_model_approved.py`                                                   |
| `endpoint` deploy: `No approved model yet …` (or CloudFormation `Validation failed with 2 error(s)`) | contract still `none`: no version approved yet                                                   | `npm run models -- --approve <version>`, then redeploy (`serverless/endpoint/approved-model.js`)                                       |
| Endpoint update rolled back                                                                          | 5XX alarm fired during blue/green baking                                                         | `serverless/endpoint/alarms.yml`, endpoint logs (`/aws/sagemaker/Endpoints/customer-churn`)                                            |
| `endpoint` deploy: `Unsupported manifest media type application/vnd.oci.image.manifest.v1+json`      | the model package's image was pushed as OCI (training accepts it, hosting doesn't)               | fixed in `container/build-push.sh`; `image:push` (new tag) → `deploy-pipeline` → retrain → approve the new version → `deploy-endpoint` |
| `/ping` unhealthy, endpoint `Failed`                                                                 | model can't load (library mismatch vs training image) or gunicorn crash                          | `src/serving/serve.py`; `modify-model-image` skill                                                                                     |
| `DataDrift` reports `insufficient_data`                                                              | fewer than `min_samples` (30) captured rows in the previous hour                                 | send more traffic (`generate_traffic`); report in `monitoring/customer-churn/data-drift/`                                              |
| Drift alarm never changes                                                                            | metric only exists after a `DataDrift` run with enough samples; `TreatMissingData: notBreaching` | Lambda logs, `DataScience/CustomerChurn` → `MaxFeatureDrift`                                                                           |

## API / batch / image

| Symptom                                             | Cause                                              | Where                                                                                          |
| --------------------------------------------------- | -------------------------------------------------- | ---------------------------------------------------------------------------------------------- |
| `/predict` 429 Too Many Requests                    | API throttling (10 rps / burst 20)                 | lower the rate (`generate_traffic --sleep`) or raise `custom.api` in `endpoint/serverless.yml` |
| `/predict` 400 `missing [...]`                      | body lacks a feature                               | `src/functions/inference/predict.py`                                                           |
| `BatchScoring` `NoApprovedModelError`               | no approval yet                                    | approve                                                                                        |
| `AthenaQueryError` (UNLOAD)                         | target prefix not empty or workgroup permissions   | `batch_scoring.py`, `batch/iam.yml`                                                            |
| Transform fails with filters/CSV                    | output not CSV per line, or content types mismatch | `src/serving/inference.py` `output_fn`, `transform_request`                                    |
| `image:push`: `Cannot connect to the Docker daemon` | socket not mounted / permissions                   | `.docker/docker-compose.yml`, `.docker/entrypoint.sh`                                          |
| Pipeline deploy: `Image … is not in ECR`            | expected guard                                     | `npm run image:push` (`container/image-version.js`)                                            |
