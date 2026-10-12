# Environments — infrastructure

Assumption (Step 4 not confirmed by the owner — **gap**): each stage is a separate
AWS account, which is why stack names have no stage suffix. Whether each developer has their own dev account is
unknown; bucket names include `DEVELOPER` in `dev` so several developers can coexist in one account.

| Item                                                   | dev                                                            | test                              | prod                              |
| ------------------------------------------------------ | -------------------------------------------------------------- | --------------------------------- | --------------------------------- |
| Bucket prefix                                          | `<ORG>-data-science-dev-<DEVELOPER>`                   | `<ORG>-data-science-test` | `<ORG>-data-science-prod` |
| Deployment bucket                                      | `us-east-1.<ORG>.data-science.dev.<DEVELOPER>.deploys` | `…test.deploys`                   | `…prod.deploys`                   |
| Noncurrent object versions kept (data lake, artifacts) | 7 days                                                         | 30 days                           | 90 days                           |
| Athena results expiration                              | 1 day                                                          | 7 days                            | 30 days                           |
| Athena workgroup                                       | `data-science`                                                 | `data-science`                    | `data-science`                    |
| Notifications topic                                    | `data-science-common-infrastructure-Notifications`             | same                              | same                              |
| VPC (library)                                          | `data-science-cloud-formation-vpc`, `10.0.0.0/16`, no NAT      | same                              | same                              |
| Studio domain                                          | `data-science`, one user profile named `<DEVELOPER>`           | same                              | same                              |

Region: `us-east-1` only (safeguard `allowed-regions` fails the deploy otherwise). Allowed stages: `dev`, `test`,
`prod` (safeguard `allowed-stages`).

Cost: the stacks have no fixed cost beyond S3 storage and SNS (VPC, subnets and security groups are free while
`LIBCFNVPC_VPC_CREATE_NAT_GATEWAY=false`; each NAT gateway would add ~USD 32/month); Studio apps (JupyterLab) bill while running and stop
after 60 idle minutes (`custom.studio.idleTimeoutInMinutes`).
