# Deployment — infrastructure

Procedure (order, SNS confirmation, removal): `README.md` → Deployment / Notifications subscription / Remove. This file
covers what the README doesn't: technology, blast radius and gotchas.

## Technology

Serverless Framework v4 (`frameworkVersion: ^4.43.0`), plugins `serverless-deployment-bucket` and
`@serverless/safeguards-plugin` declared in `package.json` (never global). Resolvers:
`${file(../shared/email-subscriptions.js)}` (common), `${ssm:/data-science-common-infrastructure/...}` (studio reads
common's outputs).

## Order relative to other sub-services

1. `serverless/common` — before any MLOps project (all of them resolve its SSM parameters at deploy time; a missing
   parameter fails their `serverless print`).
2. `customlib/cloud-formation/virtual-private-cloud/serverless` — Studio's network.
3. `serverless/studio` — after `common` (bucket ARNs, workgroup) and the VPC stack
   (`/SLS/data-science-cloud-formation-vpc/{VPC,AppSubnets}`).

Removal: only after every project stack is removed (`customer-churn` keeps data, artifacts and model images that
depend on these buckets).

## Blast radius

- **Renaming or deleting an SSM parameter** in `serverless/common/ssm.yml` breaks the next deploy of every project.
  Change producer and consumers together (`customer-churn/serverless/*/serverless.yml` and its `iam.yml` files).
- **Changing a bucket name** (`custom.bucketPrefix`, `custom.s3.*BucketName`) replaces the bucket: CloudFormation
  fails if the old bucket is not empty, and every project's IAM policies, Glue table locations and data become stale.
- **Disabling `EventBridgeEnabled`** on the data lake silently stops event-driven ingestion in every project (no error
  anywhere; the Glue workflows just never start).
- **Narrowing `NotificationsTopicPolicy`** silently drops pipeline/registry/alarm notifications.
- **`EnforceWorkGroupConfiguration: false`** on the shared workgroup removes the guard against full scans and lets
  clients write results anywhere.

- **Replacing the VPC stack or changing its subnets** forces replacing the Studio domain, which deletes the users'
  home volume.

## First-run gotchas

- `NOTIFICATION_EMAILS` empty → `email-subscriptions.js` throws during variable resolution (deploy aborts before
  CloudFormation).
- New email subscriptions stay `PendingConfirmation` until each recipient confirms.
- VPC library (details in `.claude/rules/dependencies.md`):
  - `LIBCFNVPC_DB_PORT` must be set even without a database (`database/proxy.yml` is always included and references
    `${env:LIBCFNVPC_DB_PORT}`); it creates an unused `DatabaseSecurityGroup`.
  - Without `LIBCFNVPC_VPC_CREATE_NAT_GATEWAY=false` the library creates one NAT gateway (hourly cost).
  - `zones: auto-discover` puts subnets in every available AZ of `us-east-1`. Not verified whether every AZ supports
    Studio: if the domain creation fails on a subnet, that's the first suspect.
  - CIDR is hard-coded to `10.0.0.0/16`, the same as `services/data-warehouse`'s VPC; peering them later would need a
    library change.
  - `customlib/` only exists after the devcontainer's `entrypoint.sh` ran (needs the GitLab SSH key secret).
- Removing `studio` can leave SageMaker-created EFS/mount targets/security groups that block the VPC removal
  (`README.md` → Remove).
