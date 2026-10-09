# Dependencies — customer-churn

## Stacks that must exist first

- `infrastructure/serverless/common` (same account) — SSM parameters listed in `integrations.md`.
- Inside this project: see `deployment.md` → Stack dependencies.

## Model image runtime (the non-obvious one)

- `container/requirements.txt` pins scikit-learn, pandas, numpy, scipy, joblib, flask, gunicorn. Installed by
  **both** the model image (`container/Dockerfile`, `python:3.13-slim-bookworm`) and the devcontainer
  (`../.docker/Dockerfile` stage `img-customerchurn`, `COPY container/requirements.txt` with this folder as build
  context). Keep it the single source of ML versions; never add ML libraries to `img-ml-base`.
- Image tag = `container/image-version.js` hash of `container/Dockerfile`, `container/entrypoint.sh`,
  `container/requirements.txt`, `container/build-push.sh` (it decides the manifest format), `src/__init__.py` and `src/{features,models,pipelines,serving}/**/*.py`. The list must
  match the Dockerfile `COPY`s and `.dockerignore`.
- AWS-managed runtime still used: Glue 5.0 (Spark, Python 3.11) for `src/jobs/glue/`. SageMaker Model Monitor (and its
  analyzer image) is **closed to new customers since 2026-07-30** and isn't used: drift is computed by
  `src/monitoring/drift.py` (pure Python, no dependencies) in the pipeline `Baseline` step and the `DataDrift` Lambda.

## Lambda runtime

Python 3.13, arm64, boto3 from the Lambda runtime (no layers, no bundled dependencies). Lambdas must import only the
standard library, boto3 and `src` modules listed in their `package.patterns`.

## Local tooling

Docker CLI + host socket (`image:push`, `image:build-local`), AWS CLI (`build-push.sh`, `image-version.js`'s ECR
check, npm scripts), Node 24 (resolvers), Python 3.13 with `container/requirements.txt`.
