# Integrations — customer-churn

## Internal (this repository)

| Integration                                                                                                                                                                          | Direction              | Protocol / auth                                    | If unavailable                     |
| ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ | ---------------------- | -------------------------------------------------- | ---------------------------------- |
| `infrastructure` SSM `/data-science-common-infrastructure/*` (buckets, workgroup, topic)                                                                                             | inbound at deploy time | `${ssm:...}`, deployer IAM                         | every stack fails to resolve       |
| Data lake bucket (`raw/customer_churn/`, `curated/customer_churn/customers/`, `predictions/customer_churn/`)                                                                         | read/write             | S3, project roles                                  | ingestion/curation/batch fail      |
| Artifacts bucket (`code/customer-churn/`, `pipelines/customer-churn/`, `data-capture/customer-churn/`, `monitoring/customer-churn/`, `batch/customer-churn/`, `tmp/customer-churn/`) | read/write             | S3, project roles                                  | pipeline, monitor, batch fail      |
| Shared workgroup `data-science`                                                                                                                                                      | outbound               | Athena, `BatchScoringRole`                         | batch UNLOAD fails                 |
| Notifications topic                                                                                                                                                                  | outbound               | EventBridge targets / alarm actions (topic policy) | humans miss failures and approvals |

## AWS services (all in-account)

| Caller → callee                                             | Code / config                                                                                                  | Notes                                                |
| ----------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------- |
| S3 → EventBridge → Glue workflow                            | `data/events.yml`, role `IngestionEventsRole` (`glue:NotifyEvent`)                                             | requires data lake EventBridge flag (infrastructure) |
| Glue crawler/job → S3, Data Quality, CloudWatch             | `data/glue.yml`, role `GlueRole`                                                                               | DQ results in Glue console                           |
| Glue job SUCCEEDED → SageMaker pipeline                     | `pipeline/events.yml` `CurationSucceededRule`, `PipelineEventsRole`                                            | parameter `TriggeredBy=new-data`                     |
| SageMaker pipeline → Athena / Glue catalog / S3 / ECR       | `pipeline-definition.js`, `SageMakerExecutionRole`                                                             | Athena via workgroup `customer-churn-pipeline`       |
| Model Registry → EventBridge → `OnModelApproved` → SSM, SNS | `pipeline/functions.yml`, `src/functions/registry/on_model_approved.py`, `src/services/{sagemaker,ssm,sns}.py` | only `Approved` status                               |
| `Predict` → SageMaker runtime                               | `src/functions/inference/predict.py`, `src/services/sagemaker_runtime.py`                                      | `ContentType text/csv`, `Accept application/json`    |
| `BatchScoring` → SSM, Athena, SageMaker                     | `src/functions/inference/batch_scoring.py`, `src/services/{ssm,athena,sagemaker}.py`                           | UNLOAD output is gzip TEXTFILE                       |
| Endpoint / transform / jobs → ECR image                     | `SageMakerExecutionRole` (ECR pull statement)                                                                  | image tag from the model package                     |

## External

| Integration                                                          | Direction         | Auth                                                     | If unavailable                                          |
| -------------------------------------------------------------------- | ----------------- | -------------------------------------------------------- | ------------------------------------------------------- |
| IBM dataset on GitHub (`custom.dataset.url`, `src/scripts/paths.py`) | outbound HTTPS    | none                                                     | `IngestDataset` and `local:download` fail; nothing else |
| `POST /predict` (HTTP API)                                           | inbound           | none — public, throttled (`serverless/endpoint/api.yml`) | no consumer today (Step 4 gap)                          |
| `predictions` Athena table                                           | inbound (queries) | IAM                                                      | no consumer today (Step 4 gap)                          |

## Contracts other parties rely on

- `/predict` body/response shape: `src/functions/inference/predict.py` docstring.
- Model input: headerless CSV in `src/features/schema.py` `FEATURES` order, or JSON `{"instances": [...]}`; output
  JSON `{"predictions": [{"churn_probability", "churn"}]}` or one probability per line (`text/csv`).
- SSM deployment contract names (`serverless/pipeline/ssm.yml`) read by `endpoint` and `batch`.
