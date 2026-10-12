# CLAUDE.md — infrastructure

## Repository context

`infrastructure` is one of the two sub-services of this repository (see the root `README.md` and
`CLAUDE.md`):

- **`infrastructure`** (this one) — shared platform every MLOps project reads through SSM. Deploys first.
- `customer-churn` — reference MLOps project; consumes everything this one publishes.

Architecture diagram: root `docs/architecture.drawio` (page "Infrastructure"; `docs/architecture.html` to view it in a browser).

## What it does

Pure Infrastructure-as-Code (no Lambdas, no application code): the data lake, ML artifacts and Athena results buckets,
the shared Athena workgroup, the MLOps notifications SNS topic, and the SageMaker Studio domain inside a VPC
created by the vendored `Library > Cloud Formation > Virtual Private Cloud` stack. Every output is
published to SSM under `/data-science-common-infrastructure/` — see `.claude/rules/integrations.md`.

## Folder structure

```text
infrastructure/
├── serverless/
│   ├── common/      # service common-infrastructure: s3.yml, athena.yml, sns.yml, ssm.yml, cfn-collisions.yml
│   ├── studio/      # service sagemaker-studio: iam.yml, studio.yml, cfn-collisions.yml
│   └── shared/      # email-subscriptions.js (NOTIFICATION_EMAILS → SNS subscriptions)
├── customlib/       # gitignored — cloud-formation/virtual-private-cloud (VPC library distribution, cloned by entrypoint.sh)
├── .docker/         # docker-compose.yml + entrypoint.sh (target img-infrastructure of ../.docker/Dockerfile)
├── .envs/           # config.env (only *.example is committed)
├── package.json     # Serverless plugins, prettier, eslint
└── eslint.config.mjs
```

## Local development

Open this folder in its devcontainer (container `DataScienceInfrastructure`, built from the root `.docker/Dockerfile`,
target `img-infrastructure`). Setup steps: `README.md` → Setup. Checks before considering a change done:
`npm run format`, `npm run lint`, and `serverless print` / `serverless package` inside each touched
`serverless/<stack>/`.

## Environment variables

- `../.envs/aws.env`, `../.envs/sls.env` — shared root credentials (root `README.md` → Glossary).
- `.envs/config.env` — `DEVELOPER` (required), `NOTIFICATION_EMAILS` (required),
  `GIT_CFN_VIRTUAL_PRIVATE_CLOUD_BRANCH_NAME`, `LIBCFNVPC_VPC_CREATE_NAT_GATEWAY`, `LIBCFNVPC_DB_PORT` (VPC library).
  Meanings: `README.md` → Glossary.
- `DEPLOY_APP=data-science` is set by `.docker/docker-compose.yml` (the VPC library names its stack and SSM paths with
  it).

## Deployment

`npm run deploy-common:<stage>`, then `npm run deploy-vpc:<stage>` and `npm run deploy-studio:<stage>` — every stack
is deployed in every stage. Order, the SNS confirmation step and
removal: `README.md` → Deployment / Remove; risks and blast radius: `.claude/rules/deployment.md`. Claude never runs
deploy/remove commands — it gives them to the project owner.

## Environments

- `dev`: bucket names carry `DEVELOPER`; shortest retention (7-day noncurrent versions, 1-day Athena results).
- `test` / `prod`: no developer suffix; longer retention.

Full table: `.claude/rules/environments.md`.

See .claude/rules/ for detailed operational context.
