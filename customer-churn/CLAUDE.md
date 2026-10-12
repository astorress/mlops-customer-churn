# CLAUDE.md — customer-churn

## Repository context

`customer-churn` is one of the two sub-services of this repository (see the root `README.md` and
`CLAUDE.md`):

- `infrastructure` — shared buckets, Athena workgroup, notifications topic, Studio and its VPC. Must be deployed first;
  this project reads it through SSM.
- **`customer-churn`** (this one) — reference MLOps project and template for future ones.

Architecture diagram: root `docs/architecture.drawio` (pages "Customer Churn Training" and "Customer Churn Inference"; `docs/architecture.html` to view it in a browser).

## What it does

Predicts customer churn on the public IBM Telco Customer Churn dataset and implements the whole model lifecycle on AWS:
event-driven ingestion → Glue crawler/curation/data quality → Athena → SageMaker Pipeline (validate, baseline, train,
evaluate, quality gate, register) → Model Registry with manual approval → real-time endpoint (blue/green, single `ml.t2.medium`,
data capture, hourly PSI drift Lambda) + public, throttled HTTP API → scheduled Batch Transform scoring → continuous retraining.
Every SageMaker workload runs the project's own Docker image (Python 3.13). Details: `.claude/rules/architecture.md`.

## Folder structure

```text
customer-churn/
├── container/       # model image: Dockerfile, entrypoint.sh (train/serve), requirements.txt, image-version.js, build-push.sh
├── serverless/      # stacks: data, image, pipeline, endpoint, batch (one service each)
├── src/
│   ├── features/  models/  pipelines/training/  serving/   # model packages (baked into the image)
│   ├── jobs/glue/                                          # Glue job script
│   ├── functions/{ingestion,registry,inference}/           # Lambda handlers
│   ├── services/                                           # one module per AWS service the Lambdas use
│   ├── utilities/                                          # shared by all Lambdas
│   └── scripts/                                            # local tooling (python3 -m src.scripts.<name>)
├── tests/           # pytest, mirrors src/
├── .docker/  .envs/  package.json  pyproject.toml  pytest.ini  eslint.config.mjs  .dockerignore
```

What goes where inside `src/`: `.claude/rules/architecture.md` → Code layout.

## Local development

Open this folder in its devcontainer (container `DataScienceCustomerChurn`, root `.docker/Dockerfile` target
`img-customerchurn`, built with this folder as context so it installs `container/requirements.txt`; the host Docker
socket is mounted to build the model image). Setup and local commands: `README.md` → Setup / Local development.
Before considering a change done: `npm run format`, `npm run lint`, `npm test`, and `serverless print` /
`serverless package` in each touched `serverless/<stack>/`. Tests: `.claude/rules/testing.md`.

## Environment variables

- `../.envs/aws.env`, `../.envs/sls.env` — shared root credentials (root `README.md` → Glossary).
- `.envs/config.env` — `DEVELOPER` (required), `MIN_ROC_AUC` (optional), `SKIP_IMAGE_CHECK` (optional). Meanings:
  `README.md` → Glossary.

## Deployment

`npm run deploy-<data|image|pipeline|endpoint|batch>:<stage>` plus `npm run image:push` between `image` and `pipeline`,
in the order of `README.md` → Deployment (a model must be approved before `endpoint`/`batch`); what to redeploy for
each kind of change: `README.md` → Updates. Risks, blast radius and first-run gotchas: `.claude/rules/deployment.md`.
Claude never runs deploy, remove, invoke, `image:push`, pipeline start or approval commands — it hands them to the
project owner.

## Environments

- `dev`: scheduled retraining and batch scoring disabled, 100 % data capture, endpoint max 1 instance.
- `test`: like dev but endpoint max 2 instances.
- `prod`: weekly retraining and daily batch scoring enabled, 20 % data capture, endpoint max 4 instances.

Full table and costs: `.claude/rules/environments.md`.

See .claude/rules/ for detailed operational context.
