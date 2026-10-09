# Architecture — customer-churn

## Place in the monorepo

Consumer of `infrastructure` (buckets, workgroup, topic via SSM `/data-science-common-infrastructure/*`, see
`dependencies.md`). Nobody consumes this project yet (Step 4 **gap**: no confirmed downstream system for the
`/predict` API or the `predictions` table). Authoritative diagram: root `docs/architecture.drawio`, pages "Customer
Churn Training" (layers `data`, `training`, `governance`) and "Customer Churn Inference" (layers `online`, `batch`);
browser export `docs/architecture.html`. Shared resources keep the same numbering and stack labels as the
"Infrastructure" page.

## Stacks

| Stack                 | Service                   | Owns                                                                                                                                                                                                                                                                                                                                                                                |
| --------------------- | ------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `serverless/data`     | `customer-churn-data`     | Glue database `customer_churn`, `RawCrawler`, `CuratedTable` (`customers`), `PredictionsTable` (`predictions`), `CurateJob`, `CuratedDataQualityRuleset`, `IngestionWorkflow` + `IngestionStartTrigger` (EVENT) + `CurateTrigger` (CONDITIONAL) (`glue.yml`); `RawDataArrivedRule` (`events.yml`); 4 Athena named queries (`athena.yml`); `IngestDataset` Lambda; roles (`iam.yml`) |
| `serverless/image`    | `customer-churn-image`    | ECR repository `data-science/customer-churn` (`ecr.yml`)                                                                                                                                                                                                                                                                                                                            |
| `serverless/pipeline` | `customer-churn-pipeline` | `SageMakerExecutionRole`, `ModelPackageGroup` `customer-churn`, `TrainingPipeline` `customer-churn-training` (body from `pipeline-definition.js`), workgroup `customer-churn-pipeline`, EventBridge rules, `OnModelApproved` Lambda, SSM deployment contract                                                                                                                        |
| `serverless/endpoint` | `customer-churn-endpoint` | `ChurnModel`, `ChurnEndpointConfig`, `ChurnEndpoint` (`customer-churn`, one `ml.t2.medium`), `DataDrift` Lambda (hourly), 3 alarms, `Predict` Lambda + public throttled HTTP API (`api.yml`)                                                                                                                                                                                        |
| `serverless/batch`    | `customer-churn-batch`    | `BatchScoring` Lambda (+ schedule), `BatchTransformFailedRule`                                                                                                                                                                                                                                                                                                                      |

## Flows

1. **Ingestion (event-driven)** — `IngestDataset` writes `raw/customer_churn/ingestion_date=YYYY-MM-DD/telco_customer_churn.csv`
   → S3 `Object Created` → `RawDataArrivedRule` → `IngestionWorkflow` (batches events for `eventBatchWindow` = 120 s)
   → `RawCrawler` (table `raw_customer_churn`) → on SUCCEEDED → `CurateJob` (`src/jobs/glue/curate_customers.py`):
   rename/cast/normalize, evaluate the DQDL ruleset (`custom.glue.dataQualityRuleset`; a failing rule fails the job),
   overwrite partition `curated/customer_churn/customers/ingestion_date=…/` (Parquet).
2. **Continuous training** — Glue job SUCCEEDED (`CurationSucceededRule`) or schedule (`ScheduledRetrainingRule`,
   prod only) → `customer-churn-training`:
   `PrepareData` (Athena dataset definition over the latest curated partition → `src/pipelines/training/preprocess.py`:
   validation gate + stratified split) → `Baseline` (`baseline.py` → PSI reference profile `statistics.json` + thresholds `constraints.json`)
   and `Train` (`<image> train`) → `Evaluate` (`evaluate.py` → `evaluation.json`, PropertyFile) → `CheckAuc`
   (`binary_classification_metrics.auc.value` ≥ `MinRocAuc`) → `RegisterModel` (PendingManualApproval, with
   ModelMetrics + DriftCheckBaselines + `ImageTag`) or `FailLowAuc`. Artifacts:
   `s3://<artifacts>/pipelines/customer-churn/executions/<execution-id>/`.
3. **Governance** — registration → `ModelPendingApprovalRule` → SNS. Human approves → EventBridge →
   `OnModelApproved` writes the SSM deployment contract (package ARN + baseline URIs) → SNS with the deploy command.
4. **Online inference** — `serverless/endpoint` resolves the contract at deploy time → Model from the package →
   EndpointConfig (data capture to `data-capture/customer-churn/`) → Endpoint (blue/green, rollback on
   `…-Invocation5XXErrors`). `POST /predict` (HTTP API, public, throttled to 10 rps / burst 20 in `api.yml`) → `Predict` turns JSON into headerless CSV in
   `FEATURES` order → endpoint. Hourly `DataDrift` Lambda (`src/functions/monitoring/data_drift.py`) reads the previous hour of
   captured traffic, computes PSI per feature against the approved model's profile (`src/monitoring/drift.py`), writes
   a report to `monitoring/customer-churn/data-drift/` and publishes `DataScience/CustomerChurn` metrics →
   `…-DataDrift` alarm (`MaxFeatureDrift` > 0.2) → SNS.
5. **Batch inference** — `BatchScoring` (daily, prod only): Athena UNLOAD of active customers (`churn = 0`) of the
   latest partition → `CreateModel` from the approved package → Batch Transform (`InputFilter $[1:]`,
   `JoinSource Input`, `OutputFilter $[0,-1]`) → `predictions/customer_churn/run_date=…/` → `predictions` table.

## Code layout (`src/`, absolute imports `src.*` everywhere)

- Model packages, the only ones copied into the image (`/opt/program/src/...`): `features/` (`schema.py` = data
  contract; `curation.py` = pandas mirror of the Glue job), `monitoring/` (`drift.py`, PSI), `models/` (`estimator.py`, `train.py`, `metrics.py`),
  `pipelines/training/` (pipeline step scripts), `serving/` (`inference.py`, `serve.py`).
- `jobs/glue/` — Glue scripts (synced to `code/customer-churn/glue/` by `serverless-s3-sync` in the data stack).
- Lambdas, `services/public-utilities` convention: handlers in `functions/<group>/` (no `boto3`), one module per AWS
  service in `services/` (module-level `CLIENT` + thin functions), `utilities/` for what every Lambda shares
  (`logger`, `errors`, `http`). Each function's `package.patterns` lists only the files it imports.
- `scripts/` — local tooling, reuses `services`.

## Design decisions

- Pipeline definition as explicit JSON (`serverless/pipeline/pipeline-definition.js`, a Serverless `${file()}`
  resolver), not generated by the SageMaker SDK: no AWS calls or hidden uploads at build time, every step readable.
- One custom image (BYOC) for processing/training/serving instead of the AWS-managed scikit-learn container (stuck on
  Python 3.9/3.10): same pinned runtime as the devcontainer; the pickle always loads where it was trained.
- Preprocessing lives inside the scikit-learn Pipeline → no training/serving skew; clients send raw features.
- Immutable image per content hash + IMMUTABLE ECR tags → every model package is reproducible.
- Approval publishes _what_ to deploy (SSM); deploying stays an explicit, reviewable `sls deploy`.
- Headerless CSV to the endpoint in `FEATURES` order: the drift Lambda parses captured traffic with the same contract.
- Own drift monitoring instead of SageMaker Model Monitor (closed to new customers since 2026-07-30), following AWS's
  recommended replacement pattern (EventBridge + Lambda + CloudWatch + SNS). Pure-Python PSI keeps the Lambda without
  dependencies and shares one implementation with the pipeline; Evidently AI is the richer open-source alternative.
- Raw schema discovered (crawler) vs curated schema declared (IaC): the ML-facing contract is explicit.
