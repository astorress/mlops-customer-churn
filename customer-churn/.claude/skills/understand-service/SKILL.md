---
name: understand-service
description: Explains customer-churn to someone new — what it predicts, its five stacks, how each MLOps concept maps to a real file, how it fits in the repository and what it does NOT own. Use when onboarding, when someone wants to learn MLOps with this project, or before a first change.
---

# Understand customer-churn

Answer in the language the person writes in. Point at real files. Facts live in `.claude/rules/` — cite them.

## 1. What it is

Reference MLOps project: predicts churn on the public IBM Telco Customer Churn dataset (7,043 customers, ~26 %
churn) with a scikit-learn Pipeline (imputation + one-hot + `HistGradientBoostingClassifier`, test ROC AUC ≈ 0.85),
and runs its whole lifecycle on AWS as IaC. It is also the template for the next MLOps projects.

## 2. Place in the repository

Needs `infrastructure` (buckets, Athena workgroup, notifications topic via SSM). Nobody consumes it yet. See
`.claude/rules/architecture.md` → Place in the repository, and open root `docs/architecture.html` (pages "Customer Churn
Training" / "Customer Churn Inference") to walk the numbered steps.

## 3. The five stacks and the flows

Walk `.claude/rules/architecture.md` → Stacks and Flows (ingestion → training → governance → online → batch).

## 4. Concept → file map

| MLOps concept                     | Where                                                                                                                        |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| Data lake zones                   | `../infrastructure/serverless/common/s3.yml` (`raw/` → `curated/` → `predictions/`)                                          |
| Ingestion                         | `src/functions/ingestion/ingest_dataset.py` (Hive partition `ingestion_date=`, simulated drift)                              |
| Event-driven orchestration        | `serverless/data/events.yml`, `glue.yml` (S3 → EventBridge → Glue Workflow EVENT trigger)                                    |
| Schema discovery vs data contract | `RawCrawler` vs `CuratedTable` in `serverless/data/glue.yml`; `src/features/schema.py`                                       |
| ETL                               | `src/jobs/glue/curate_customers.py`                                                                                          |
| Data quality                      | DQDL in `serverless/data/serverless.yml` (`custom.glue.dataQualityRuleset`)                                                  |
| Partition projection              | `CuratedTable` / `PredictionsTable` parameters                                                                               |
| Exploratory SQL                   | `serverless/data/athena.yml` named queries                                                                                   |
| Training pipeline as code         | `serverless/pipeline/pipeline-definition.js`                                                                                 |
| Reading training data from Athena | step `PrepareData` (`AthenaDatasetDefinition`)                                                                               |
| ML data validation                | `src/pipelines/training/preprocess.py`                                                                                       |
| Training/serving skew             | `src/models/estimator.py` (preprocessing inside the model), `src/serving/`                                                   |
| Experiment tracking               | `PipelineExperimentConfig` + `MetricDefinitions` in the pipeline definition                                                  |
| Offline evaluation                | `src/pipelines/training/evaluate.py`, `src/models/metrics.py`                                                                |
| Quality gate                      | step `CheckAuc` / `FailLowAuc`                                                                                               |
| Data baseline                     | step `Baseline` (`src/pipelines/training/baseline.py`, PSI reference profile)                                                |
| Model Registry                    | `serverless/pipeline/sagemaker.yml` (`ModelPackageGroup`)                                                                    |
| Containers (BYOC)                 | `container/` (`train` / `serve` contracts), `serverless/image/`                                                              |
| Reproducibility                   | `container/image-version.js` + IMMUTABLE ECR tags                                                                            |
| Human approval                    | `src/scripts/approve_model.py` / Studio                                                                                      |
| Deployment contract               | `serverless/pipeline/ssm.yml`, `src/functions/registry/on_model_approved.py`                                                 |
| Model CD                          | `serverless/endpoint/` resolves the approved model from SSM                                                                  |
| Safe deployment                   | `ChurnEndpoint` blue/green + auto-rollback (`serverless/endpoint/sagemaker.yml`)                                             |
| Inference API                     | `src/functions/inference/predict.py` (public HTTP API, throttled)                                                            |
| Data capture & drift monitoring   | `ChurnEndpointConfig`, `src/monitoring/drift.py`, `src/functions/monitoring/data_drift.py`, `serverless/endpoint/alarms.yml` |
| Batch inference                   | `src/functions/inference/batch_scoring.py`                                                                                   |
| Continuous training               | `serverless/pipeline/events.yml`                                                                                             |
| Alerting                          | EventBridge rules → SNS (pipeline, registry, transform)                                                                      |
| CI/CD                             | `../.gitlab-ci.yml`                                                                                                          |

## 5. Why it's built this way

`.claude/rules/architecture.md` → Design decisions.

## 6. What it does NOT own

The shared buckets, the `data-science` workgroup and the notifications topic (`infrastructure`); the dataset itself
(IBM's GitHub); any consumer of `/predict` or `predictions`. Pending (root `changelog.md`): model quality monitoring,
Clarify, hyperparameter tuning, MLflow, Feature Store, cross-account promotion.

## 7. Next step

To see it working end to end, use the `run-end-to-end-demo` skill.
