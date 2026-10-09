---
name: validate-environment
description: Checks the deployed state of customer-churn in an account — shared layer, each stack's SSM outputs, ECR image tag, approved model contract, endpoint status, latest drift reports, schedules. Use before deploying the next stack, before a demo, or when unsure what is deployed.
---

# Validate the customer-churn environment

Read-only commands. Shared layer first: `../infrastructure/.claude/skills/validate-environment/`.

```bash
aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE \
  --query "StackSummaries[?starts_with(StackName,'data-science-customer-churn')].StackName"
for p in data image pipeline endpoint; do
  aws ssm get-parameters-by-path --path /data-science-customer-churn-$p/ --query "Parameters[].[Name,Value]" --output text
done
TAG=$(node -e "console.log(require('./container/image-version.js').imageVersion())")
aws ecr describe-images --repository-name data-science/customer-churn --image-ids imageTag=$TAG \
  --query "imageDetails[0].imagePushedAt"                      # error = current code not pushed
aws sagemaker list-model-packages --model-package-group-name customer-churn \
  --query "ModelPackageSummaryList[].[ModelPackageVersion,ModelApprovalStatus]" --output text
aws sagemaker describe-endpoint --endpoint-name customer-churn --query "[EndpointStatus,EndpointConfigName]"
aws s3 ls s3://$(aws ssm get-parameter --name /data-science-common-infrastructure/ArtifactsBucketName --query Parameter.Value --output text)/monitoring/customer-churn/data-drift/ --recursive | tail -3   # latest drift reports
aws events describe-rule --name data-science-customer-churn-pipeline-ScheduledRetraining --query State
```

Interpretation:

- `ApprovedModelPackageArn = none` → approve before `endpoint`/`batch` (`README.md` → Model approval).
- `DeployedModelPackageArn` (endpoint SSM) ≠ `ApprovedModelPackageArn` → a newer approved version is not deployed yet.
- Endpoint exists in `dev` outside a session → remind the owner of the hourly cost.
- Expected schedule states per stage: `.claude/rules/environments.md`.
