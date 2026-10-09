# Architecture — infrastructure

## Place in the monorepo

`infrastructure` is the foundation of `data-science`. It owns no application code and calls nothing at run time: every MLOps
project (today only `customer-churn`) **reads** its outputs from SSM at deploy time and writes into its buckets at run
time. The authoritative diagram is the "Infrastructure" page of root `docs/architecture.drawio` (browser export
`docs/architecture.html`; layers `infra-platform` and `infra-studio`); this file has the detail the diagram doesn't.

## Stacks

| Stack                                                        | Service                  | Owns                                                                                                                                                                                                                     |
| ------------------------------------------------------------ | ------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| `serverless/common`                                          | `common-infrastructure`  | `DataLakeBucket`, `ArtifactsBucket`, `AthenaResultsBucket` (`s3.yml`); `AthenaWorkGroup` (`athena.yml`); `NotificationsTopic` + `NotificationsTopicPolicy` (`sns.yml`); 7 SSM parameters (`ssm.yml`)                     |
| `customlib/cloud-formation/virtual-private-cloud/serverless` | `vpc` (vendored library) | VPC `10.0.0.0/16` with public, app and DB subnets in every available AZ (`serverless-vpc-plugin`), `AppSecurityGroup`, an unused `DatabaseSecurityGroup`, no NAT gateways; SSM `/SLS/data-science-cloud-formation-vpc/*` |
| `serverless/studio`                                          | `sagemaker-studio`       | `StudioExecutionRole` (`iam.yml`); `StudioDomain` + `DeveloperUserProfile` (`studio.yml`), in the library VPC's app subnets                                                                                              |

Stack names: `data-science-common-infrastructure`, `data-science-sagemaker-studio` (`${app}-${service}`) and
`data-science-cloud-formation-vpc` (the library's own convention `${DEPLOY_APP}-cloud-formation-vpc`).

## Resource roles

- **`DataLakeBucket`** — zones by prefix, one sub-prefix per project: `raw/<project>/` (as ingested, Hive partitions
  `ingestion_date=`), `curated/<project>/` (Parquet, declared Glue tables), `predictions/<project>/`. Versioned.
  **EventBridge notifications enabled** (`NotificationConfiguration.EventBridgeConfiguration`): projects subscribe to
  `Object Created` with their own EventBridge rules — never add S3 bucket notification configurations here, they
  would collide between projects.
- **`ArtifactsBucket`** — everything ML produces: `code/<project>/` (e.g. Glue scripts), `pipelines/<project>/`
  (per-execution datasets, models, evaluation, baselines), `data-capture/<project>/`, `monitoring/<project>/`,
  `batch/<project>/`, `tmp/<project>/`. Versioned so artifacts referenced by registered models stay reproducible.
- **`AthenaResultsBucket`** — query results of the shared workgroup, expiring.
- **`AthenaWorkGroup`** (`data-science`) — enforced configuration (clients can't override the results location),
  10 GB bytes-scanned cutoff, engine v3, CloudWatch metrics. Projects whose tools set their own result location
  (SageMaker's Athena dataset definition) create their own non-enforced workgroup (e.g.
  `customer-churn-pipeline`).
- **`NotificationsTopic`** — single human channel. Its policy lets `events.amazonaws.com` (EventBridge rules of the
  projects) and `cloudwatch.amazonaws.com` (alarms) publish, restricted to the same account (`aws:SourceAccount`).
  Email subscriptions are built by `serverless/shared/email-subscriptions.js` from `NOTIFICATION_EMAILS`.
- **VPC** — only Studio uses it: the domain mounts each user's home (EFS created by SageMaker) through network
  interfaces in the app subnets. With `AppNetworkAccessType: PublicInternetOnly`, internet/AWS API traffic goes through
  SageMaker's managed network, so the subnets need no NAT. Every other workload of the projects (Glue, Lambdas,
  SageMaker jobs/endpoints) runs on AWS-managed networking and doesn't use this VPC.
- **Studio** — the team's UI (pipelines DAG, registry approvals, endpoints, monitoring). Deployed in every stage;
  no other stack reads its outputs, so the projects keep working (via CLI/scripts) if it's down.
  `StudioExecutionRole` = `AmazonSageMakerFullAccess` + read/write on the three buckets + Athena on the shared
  workgroup + Glue catalog reads.

## Design decisions

- Bucket names for ML use hyphens, not dots (TLS virtual-hosted style and some SageMaker features break with dots);
  only the Serverless deployment bucket keeps the dotted repository convention.
- The VPC is reused from `Library > Cloud Formation > Virtual Private Cloud` (same library as
  `services/data-warehouse`), vendored in `customlib/` — not copied into this repository (`.claude/rules/dependencies.md`).
- Cross-stack contracts go through SSM (`/${app}-${service}/<Name>`), never CloudFormation exports, so stacks can be
  updated or replaced independently (same convention as `services/public-utilities`).
