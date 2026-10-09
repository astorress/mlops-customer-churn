# Integrations — infrastructure

At deploy time this sub-service only reaches GitLab (the devcontainer clones the VPC library over SSH). All integrations are **inbound**: other sub-services read its SSM parameters at deploy
time (Serverless `${ssm:...}`, IAM of the deployer) and use its resources at run time (IAM of their own roles).

## SSM contract (`serverless/common/ssm.yml`, prefix `/data-science-common-infrastructure/`)

| Parameter                | Value                     | Consumed by                                                               |
| ------------------------ | ------------------------- | ------------------------------------------------------------------------- |
| `DataLakeBucketName`     | data lake bucket name     | `customer-churn` data, batch                                              |
| `DataLakeBucketArn`      | data lake bucket ARN      | `customer-churn` data, pipeline, batch; `sagemaker-studio`                |
| `ArtifactsBucketName`    | artifacts bucket name     | `customer-churn` data, pipeline, endpoint, batch                          |
| `ArtifactsBucketArn`     | artifacts bucket ARN      | `customer-churn` data, pipeline, batch; `sagemaker-studio`                |
| `AthenaResultsBucketArn` | Athena results bucket ARN | `customer-churn` batch; `sagemaker-studio`                                |
| `AthenaWorkGroupName`    | `data-science`            | `customer-churn` data (named queries), batch (UNLOAD); `sagemaker-studio` |
| `NotificationsTopicArn`  | SNS topic ARN             | `customer-churn` pipeline, endpoint, batch                                |

If `common` is missing or a parameter is renamed, consumers fail at `serverless print`/`deploy` time with an
unresolved `${ssm:...}` variable.

## VPC library outputs (consumed inside this sub-service)

`serverless-vpc-plugin` publishes `/SLS/data-science-cloud-formation-vpc/{VPC,AppSecurityGroup,PublicSubnets,AppSubnets,DBSubnets}`
and the library adds `DatabaseSecurityGroup`. `serverless/studio` reads `VPC` and `AppSubnets` (StringList, resolved as
a list by Serverless). No MLOps project reads them today.

## Run-time integrations

| Resource                                   | Direction       | Who                                                 | Auth                               | If unavailable                                   |
| ------------------------------------------ | --------------- | --------------------------------------------------- | ---------------------------------- | ------------------------------------------------ |
| `DataLakeBucket` → EventBridge default bus | outbound events | S3 `Object Created`                                 | AWS service                        | projects' event-driven ingestion stops silently  |
| `DataLakeBucket`, `ArtifactsBucket`        | inbound S3      | projects' Lambda, Glue and SageMaker roles          | IAM (consumer roles)               | ingestion, training, serving and monitoring fail |
| `AthenaWorkGroup`                          | inbound         | `customer-churn` BatchScoring, users, Studio        | IAM                                | batch scoring UNLOAD fails                       |
| `NotificationsTopic`                       | inbound         | EventBridge rules and CloudWatch alarms of projects | topic policy (`aws:SourceAccount`) | notifications lost; nothing else fails           |
| `NotificationsTopic` → email               | outbound        | subscribers in `NOTIFICATION_EMAILS`                | email confirmation                 | humans miss approvals/failures                   |
