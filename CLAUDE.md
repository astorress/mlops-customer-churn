# CLAUDE.md — data-science (monorepo root)

## How to work in this repository

**Claude never runs deploys (`serverless deploy`/`sls deploy`, `npm run deploy-*`), `serverless remove`,
`serverless invoke` against AWS, `aws sagemaker start-pipeline-execution`/`update-model-package`, `git push`, or
any other command that changes deployed AWS state or remote git state.** Give the actual command (or its
diagnosis) and let the project owner run it. SageMaker jobs and endpoints cost money while they run.

**Before considering any change done, run (all local):** each sub-service's `npm run format` and `npm run lint`,
`npm test` where it exists, then — from within the affected stack's own `serverless/<stack>/` folder —
`serverless print` (resolves every `${ssm:...}`/`${env:...}`/`${self:...}`/`${file(...)}` variable) and
`serverless package` (builds the artifact locally, no deploy).

## What this monorepo is

`data-science` holds **MLOps projects**. Each project is an independently deployed sub-service
that owns the full lifecycle of one model on AWS (S3 data lake zones, Glue catalog/jobs/data quality, Athena,
SageMaker Pipelines, Model Registry, endpoints/Batch Transform, data drift monitoring, EventBridge), all
Infrastructure-as-Code with Serverless Framework v4 — same conventions as `services/public-utilities`.

Sub-services, each with its own `CLAUDE.md`:

- [`infrastructure/`](infrastructure/CLAUDE.md) — shared platform (data lake / artifacts / Athena results buckets,
  Athena workgroup, notifications SNS topic, VPC and SageMaker Studio domain). Deploy first; every project reads
  its outputs via `${ssm:/data-science-common-infrastructure/...}`.
- [`customer-churn/`](customer-churn/CLAUDE.md) — reference project (IBM Telco Customer Churn) that implements
  every MLOps flow; the template for new projects.

Each sub-service carries its own Claude context: `CLAUDE.md` (index) + `.claude/rules/` (facts: architecture,
environments, deployment, integrations, …) + `.claude/agents/` + `.claude/skills/`, generated with
`.claude/commands/project-context-builder.md`. `README.md` files are human-facing operational guides (repository
standard: Summary / Setup / Contribution guidelines / Glossary) and own the procedures; `.claude/` files cite them and
never the other way around.

Architecture: `docs/architecture.drawio` (authoritative; one page per sub-service flow — "Infrastructure", "Customer
Churn Training", "Customer Churn Inference"; `docs/architecture.html` is its browser export), maintained with
`.claude/commands/architecture-diagram.md`. `docs/mlops-architecture.md` is a lighter Mermaid overview.

## Shared Docker / devcontainer architecture

Same pattern as `public-utilities`: one shared multi-stage `.docker/Dockerfile`. `img-base` (Node 24, Python
3.13, AWS CLI, Serverless Framework v4, `cfn-lint`, Claude Code) → `img-ml-base` (Docker CLI, libsqlite3, boto3,
jupyterlab, pytest/moto, pylint/yapf/isort; no ML libraries) → one target per ML project (`img-customerchurn`),
built with the project folder as context so it installs the project's `container/requirements.txt` — the same
pinned runtime as the project's SageMaker model image (BYOC). ML project devcontainers mount the host
`/var/run/docker.sock` to build/push that image.
`img-root`/`img-infrastructure` extend `img-base` directly.

- The root `.devcontainer.json` (service `data_science`, target `img-root`) is only for browsing the monorepo.
- Each sub-service has its own `.devcontainer.json` + `.docker/docker-compose.yml` + `.docker/entrypoint.sh`
  (configures git via `../.docker/git.sh`, runs `npm install`, AWS credentials via `../.docker/aws.sh`).
  `entrypoint.sh` only runs from VS Code's `postCreateCommand`; `docker compose up` just runs `sleep infinity`.
- Container names: `DataScience`, `DataScienceInfrastructure`, `DataScienceCustomerChurn`. Run commands with
  `docker exec <container> sh -c "cd /app/<sub-service> && <command>"`.
- **Serverless plugins are never installed globally**: each sub-service declares
  `serverless-deployment-bucket`, `@serverless/safeguards-plugin` (and `serverless-s3-sync` where needed) in its
  own `package.json`.
- Shared root `.envs/` (`aws.env`, `sls.env`, loaded by every sub-service's compose file) and per-sub-service
  `.envs/config.env`. Only `*.example` files are committed.

## Stack conventions (all sub-services)

- `stackName: ${self:custom.app}-${self:service}`; one AWS account per stage (dev/test/prod); `DEVELOPER` only
  appears in bucket names.
- Safeguards: framework version, `us-east-1` only, stages `dev|test|prod`, no wildcard IAM (warning), function
  names `${servicePrefix}-${FUNCTION}`.
- Cross-stack values travel through SSM parameters named `/${app}-${service}/<Name>`, never CloudFormation
  exports (except `cfn-collisions.yml`, which only renames the deployment bucket output).
- ML-facing bucket names use hyphens (no dots).

## Python layout (all projects)

Everything under `<project>/src/`, imported absolutely (`src.*`): model packages (`features/`, `models/`,
`pipelines/<pipeline>/`, `serving/`) baked into the model image; `jobs/` (Glue); Lambdas as
`functions/<group>/<handler>.py`, one `services/<aws_service>.py` per AWS service they call, `utilities/` for what
every Lambda shares; `scripts/` for local tooling. `tests/` mirrors `src/`.

## Commit convention

Conventional Commits, one bullet per line: `* <type>: <description>` (imperative, no trailing period), one bullet
per distinct change, no body. **Never add Claude co-authorship to commits in this repository.**
