# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

- Architecture diagram (`docs/architecture.drawio` / `docs/architecture.html`) with the Infrastructure, Customer Churn Training and Customer Churn Inference pages
- `Infrastructure` module:
  - Shared MLOps platform: data lake, ML artifacts and Athena results buckets, Athena workgroup, notifications topic and SageMaker Studio domain
  - SageMaker Studio VPC created with the `Library > Cloud Formation > Virtual Private Cloud` distribution (vendored in `customlib/`), without NAT gateways; replaces the `STUDIO_VPC_ID`/`STUDIO_SUBNET_IDS` variables
- `Customer Churn` module:
  - Reference MLOps project (IBM Telco Customer Churn dataset): ingestion, Glue cataloging and curation with Glue Data Quality, SageMaker Pipeline (Athena → preprocessing → baseline → training → evaluation → conditional registration), Model Registry with manual approval, real-time endpoint with data capture, blue/green deployment, autoscaling and Model Monitor, batch scoring with Batch Transform and an HTTP API
  - Custom model image (BYOC, Python 3.13) for processing, training and serving, versioned by content hash in an immutable ECR repository; the devcontainer installs the same pinned requirements
  - `src/` layout: model packages (`features`, `models`, `pipelines`, `serving`), Glue `jobs`, Lambdas as `functions` + `services` (one per AWS service) + `utilities`
  - Data drift monitoring with an hourly Lambda (PSI per feature against a reference profile built by the pipeline `Baseline` step) and a CloudWatch alarm, replacing SageMaker Model Monitor, closed to new customers since 2026-07-30
  - Prediction API without authentication (throttled to 10 requests per second) and endpoint on a single `ml.t2.medium` in every stage
  - Model image pushed with Docker v2 manifests (SageMaker hosting rejects OCI)
  - Pending: model quality monitoring (needs ground truth labels merged with captured data)
  - Pending: SageMaker Clarify bias/explainability step
