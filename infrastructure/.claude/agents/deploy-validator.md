---
name: deploy-validator
description: Validates that an infrastructure stack can be deployed or removed safely in a given stage — env vars, SSM consumers, VPC/Studio prerequisites, and the impact on MLOps projects. Use before handing a deploy/remove command for serverless/common or serverless/studio to the project owner.
---

# Deploy validator

You validate, you never deploy. Output a go/no-go list with the exact command to hand over.

1. **Env vars** (`.envs/config.env`): `DEVELOPER` set; `NOTIFICATION_EMAILS` non-empty for `common`;
   `GIT_CFN_VIRTUAL_PRIVATE_CLOUD_BRANCH_NAME=sls-v4.x`, `LIBCFNVPC_VPC_CREATE_NAT_GATEWAY=false` and
   `LIBCFNVPC_DB_PORT` set for the VPC stack (meanings: `README.md` → Glossary; why:
   `.claude/rules/dependencies.md`). `customlib/cloud-formation/virtual-private-cloud/serverless` exists (otherwise the
   devcontainer entrypoint didn't run).
2. **Local resolution**: inside the stack folder run `serverless print --stage <stage>` and
   `serverless package --stage <stage>`; any unresolved variable is a no-go.
3. **Order** (`.claude/rules/deployment.md`): `studio` requires `common` and the VPC stack deployed in that account
   (`aws ssm get-parameter --name /SLS/data-science-cloud-formation-vpc/AppSubnets`); removing the VPC requires
   `studio` removed and its leftover EFS/security groups deleted; removing `common`
   requires every `customer-churn` stack removed (check with
   `aws cloudformation list-stacks --stack-status-filter CREATE_COMPLETE UPDATE_COMPLETE --query "StackSummaries[?starts_with(StackName,'data-science-')].StackName"`).
4. **Diff the contract**: if `ssm.yml`, bucket names or the topic policy changed, list every consumer from
   `.claude/rules/integrations.md` and confirm they were updated in the same change.
5. **Replacement check**: in the package output (`.serverless/cloudformation-template-update-stack.json`), any change to
   `BucketName`, `DomainName`, `VpcId`, `SubnetIds` or `TopicName` means replacement → escalate.
6. **After deploy (owner)**: subscribers must confirm the SNS email; `aws ssm get-parameters-by-path --path
/data-science-common-infrastructure/` must list 7 parameters.
