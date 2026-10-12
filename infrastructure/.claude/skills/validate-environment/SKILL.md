---
name: validate-environment
description: Checks that an AWS account/stage is ready for the infrastructure stacks and that the deployed shared platform is healthy (SSM outputs, buckets, EventBridge flag, SNS subscriptions, workgroup). Use before deploying MLOps projects into a new account or when something shared seems broken.
---

# Validate the shared environment

Read-only commands (safe for Claude to run inside the devcontainer when the owner asks).

```bash
aws sts get-caller-identity                                   # right account?
aws ssm get-parameters-by-path --path /data-science-common-infrastructure/ \
  --query "Parameters[].Name"                                 # expect 7 names
LAKE=$(aws ssm get-parameter --name /data-science-common-infrastructure/DataLakeBucketName --query Parameter.Value --output text)
aws s3api get-bucket-notification-configuration --bucket "$LAKE"   # expect "EventBridgeConfiguration": {}
aws s3api get-bucket-versioning --bucket "$LAKE"                   # expect Enabled
aws athena get-work-group --work-group data-science \
  --query "WorkGroup.Configuration.[EnforceWorkGroupConfiguration,BytesScannedCutoffPerQuery]"
TOPIC=$(aws ssm get-parameter --name /data-science-common-infrastructure/NotificationsTopicArn --query Parameter.Value --output text)
aws sns list-subscriptions-by-topic --topic-arn "$TOPIC" \
  --query "Subscriptions[].[Endpoint,SubscriptionArn]"        # PendingConfirmation = not confirmed
```

Studio: `aws ssm get-parameters-by-path --path /SLS/data-science-cloud-formation-vpc/ --query "Parameters[].Name"`
(VPC library outputs, needed by Studio) and
`aws sagemaker list-domains --query "Domains[?DomainName=='data-science'].Status"` → `InService`.

Interpretation: any missing parameter → deploy `serverless/common` (`README.md` → Deployment). Missing EventBridge
configuration → projects' ingestion is silently broken (`.claude/rules/deployment.md` → Blast radius).

Repository note: this validates only the shared layer; each project has its own `validate-environment` skill
(e.g. `../customer-churn/.claude/skills/validate-environment/`).
