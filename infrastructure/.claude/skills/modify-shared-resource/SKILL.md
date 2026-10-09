---
name: modify-shared-resource
description: Safe procedure to change a shared resource or SSM parameter of the infrastructure sub-service (buckets, lifecycle, Athena workgroup, notifications topic/policy, SSM outputs) without breaking the MLOps projects that consume it. Use before editing anything in serverless/common.
---

# Modify a shared resource

`serverless/common` is consumed by every MLOps project (`.claude/rules/integrations.md`). Follow this order.

1. **Classify the change**
   - _Additive_ (new SSM parameter, new lifecycle rule, new subscription): safe, go to step 3.
   - _Behavioral_ (retention, workgroup limits, topic policy, EventBridge flag): check `.claude/rules/deployment.md`
     → Blast radius for silent failures.
   - _Breaking_ (rename/delete a parameter, rename a bucket, change `TopicName`): requires consumer changes and a
     migration plan — escalate to the owner before writing code.
2. **Find consumers**: `grep -rn "<ParameterName>\|<bucket prefix>" ../customer-churn/serverless ../customer-churn/src`
   and list each file that must change.
3. **Edit** the resource (`s3.yml`, `athena.yml`, `sns.yml`) and, if a value must be shared, add a parameter to
   `ssm.yml` with the `/${self:custom.servicePrefix}/<Name>` convention. Never use CloudFormation exports.
4. **Update docs** that own the fact: `.claude/rules/integrations.md` (new/changed parameter),
   `.claude/rules/environments.md` (per-stage values), `README.md` → Glossary (new env vars).
5. **Validate locally**: `npm run format && npm run lint`, then in `serverless/common`:
   `serverless print --stage dev` and `serverless package --stage dev`. Inspect
   `.serverless/cloudformation-template-update-stack.json` for unintended replacements (`BucketName`, `TopicName`).
6. **Hand over** the commands in order: `npm run deploy-common:<stage>` first, then the consumer stacks' deploy
   commands (consumer `README.md` → Deployment). Claude never runs them.
7. **Changelog**: use the `update-changelog` skill.
