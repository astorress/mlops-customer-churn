# Environments — customer-churn

Assumption (Step 4 not confirmed — **gap**): one AWS account per stage; the shared
buckets come from `infrastructure` in the same account (names: `../infrastructure/.claude/rules/environments.md`).
Region `us-east-1`; stages `dev|test|prod` (safeguards).

| Item                                      | dev                                 | test     | prod    | Where                                                                        |
| ----------------------------------------- | ----------------------------------- | -------- | ------- | ---------------------------------------------------------------------------- |
| Scheduled retraining (Mondays 06:00 UTC)  | disabled                            | disabled | enabled | `pipeline/serverless.yml` → `custom.pipeline.retrainingScheduleState`        |
| Scheduled batch scoring (daily 07:00 UTC) | disabled                            | disabled | enabled | `batch/serverless.yml` → `custom.batch.scheduleEnabled`                      |
| Endpoint instance type                    | `ml.t2.medium` × 1 (no autoscaling) | same     | same    | `endpoint/serverless.yml` → `custom.endpoint.instanceType` / `instanceCount` |
| Data capture sampling                     | 100 %                               | 100 %    | 20 %    | `custom.endpoint.dataCapturePercentage`                                      |
| Lambda log retention                      | 1 day                               | 3 days   | 7 days  | `custom.lambda.logRetentionInDays` (every stack)                             |
| ECR images kept                           | 20                                  | 50       | 200     | `image/serverless.yml` → `custom.ecr.maxImages`                              |
| Registration threshold                    | `MIN_ROC_AUC` (default 0.80)        | same     | same    | `.envs/config.env`                                                           |

Same names in every stage (one account each): pipeline `customer-churn-training`, model package group and endpoint
`customer-churn`, Glue database `customer_churn`, ECR `data-science/customer-churn`.

## Costs (us-east-1, approximate — verify current prices)

| Resource                                  | Bills                       | Order of magnitude           |
| ----------------------------------------- | --------------------------- | ---------------------------- |
| Endpoint `ml.t2.medium`                   | 24/7 while the stack exists | ~USD 0.056/h (~USD 41/month) |
| `DataDrift` Lambda                        | hourly, a few seconds       | cents per month              |
| Pipeline execution (4 jobs `ml.m5.large`) | per run                     | < USD 0.10                   |
| Glue job (2 × G.1X, 1-min minimum)        | per run                     | ~USD 0.05                    |
| Batch Transform                           | per run                     | < USD 0.05                   |
| ECR                                       | storage per image (~400 MB) | ~USD 0.04/month per image    |

`dev` practice sessions should end with removing `serverless/endpoint` (`README.md` → Remove).
