---
name: code-review
description: Rigorous checklist-driven review of customer-churn's container setup (devcontainer AND model image), package dependencies, devcontainer configuration and Serverless packaging. Use when asked to review customer-churn tooling/config or after changing .docker/, container/, .devcontainer.json, package.json, pyproject.toml or serverless/*.yml.
---

# Code review — customer-churn (containers, dependencies, stacks)

Rules: read every file below **completely** before concluding — most bugs only show when comparing two files. Trace
every path end to end. Check parity in both directions. Never skip an item because it looks unchanged. Report
findings without immediate impact too. If something can't be verified statically, say so.

Files: `../.docker/Dockerfile` (stages `img-base`, `img-ml-base`, `img-customerchurn`), `.docker/docker-compose.yml`,
`.docker/entrypoint.sh`, `../.docker/{git,aws}.sh`, `.devcontainer.json`, `container/{Dockerfile,entrypoint.sh,requirements.txt,image-version.js,build-push.sh}`,
`.dockerignore`, `package.json`, `pyproject.toml`, `pytest.ini`, `eslint.config.mjs`, `.prettierignore`,
`serverless/*/serverless.yml` and every file they `${file()}`, `serverless/*/functions.yml`.

Severity: **[BUG]** · **[SILENT FAILURE]** · **[CONFLICT]** · **[WASTE]** · **[RISK]**.

## Checklist

### Devcontainer Dockerfile (`../.docker/Dockerfile`)

- [ ] Single Python: only the `python-base` COPY; grep for `apt-get install ... python3`.
- [ ] `img-ml-base` installs Docker CLI + buildx (for `image:push`), `libsqlite3-0` (pytest-cov), linters, test
      tools; **no ML libraries** (they come from `container/requirements.txt` in `img-customerchurn`).
- [ ] `img-customerchurn` `COPY container/requirements.txt` resolves with the compose `context: ..` (project folder)
      and is allowed by `.dockerignore`.
- [ ] Tools used by scripts exist: `aws`, `jq`, `git`, `node`, `docker`, `tar`, `tput`.
- [ ] No standalone `apt-get update` layer that can go stale ([RISK], shared Dockerfile).
- [ ] `USER $USER` in derived stages resolves to the intended user (ARG scope) — verify with a running container.

### Model image (`container/`)

- [ ] `Dockerfile` `COPY`s ↔ `.dockerignore` allow-list ↔ `IMAGE_PACKAGES` in `image-version.js` (three-way parity).
- [ ] `entrypoint.sh`: `train` → `python3 -m src.models.train`, `serve` → `gunicorn src.serving.serve:app` on
      `${SAGEMAKER_BIND_TO_PORT:-8080}`; `WORKDIR`/`PYTHONPATH=/opt/program` make `src.*` importable.
- [ ] Every module in `ContainerEntrypoint` of `pipeline-definition.js` exists in the image.
- [ ] `requirements.txt` pins exact versions; `flask`/`gunicorn` present for `serve`.
- [ ] `build-push.sh`: `docker buildx` with `--platform linux/amd64`, `--provenance=false --sbom=false`,
      `oci-mediatypes=false` and the post-push manifest check (SageMaker hosting rejects OCI manifests); reads
      `/data-science-customer-churn-image/RepositoryUri`; it's part of the image hash in `image-version.js`.

### devcontainer.json

- [ ] `python.defaultInterpreterPath` / `yapf.interpreter` = `/usr/local/bin/python` (from the python-base COPY).
- [ ] `serverlessIDE.cfnLint.path` = `/usr/local/bin/cfn-lint` (pip); `cfn_lint_serverless.rules` installed.
- [ ] Extensions ↔ tools/settings both ways (pylint, isort, yapf, jupyter ↔ jupyterlab, eslint, prettier,
      markdownlint, docker). `python.analysis.extraPaths` = `["."]` (absolute `src.*` imports).

### package.json / Python config

- [ ] Plugins in every `serverless.yml` ↔ devDependencies (both directions): `serverless-deployment-bucket`,
      `@serverless/safeguards-plugin`, `serverless-s3-sync` (data only).
- [ ] Every script's paths exist (`serverless/<stack>`, `container/build-push.sh`, `src.scripts.*` modules).
- [ ] `lint` covers `src tests` and `serverless container`; `pyproject.toml` isort `known_first_party = ["src"]`;
      `pytest.ini` `pythonpath = .`.

### entrypoint.sh / docker-compose.yml

- [ ] `STEP_COUNT` = number of steps; docker socket step tolerates a missing socket; `aws.sh` runs before `aws`.
- [ ] Compose: `context: ..`, `dockerfile: ../.docker/Dockerfile`, `target: img-customerchurn`; `env_file` root
      `aws.env`, `sls.env` + `../.envs/config.env`; `/var/run/docker.sock` mount; secret
      `gitlab_ssh_private_key` ↔ Dockerfile symlink; `/commandhistory` volume ↔ `HISTFILE`; port 8888 ↔ jupyterlab.

### Stacks / packaging

- [ ] Each `functions.yml` `package.patterns` includes every `src` file the handler imports transitively plus each
      package `__init__.py` (verify by importing the handler from a folder with only those files).
- [ ] Every `${ssm:...}` consumer name matches its producer `ssm.yml` (data, image, pipeline, infrastructure common).
- [ ] Safeguards, `deploymentBucket`, `cfn-collisions.yml` in every stack.
- [ ] IAM: `Resource: '*'` only where required (`ecr:GetAuthorizationToken`, Glue DQ publishing); `iam:PassRole`
      conditioned on `sagemaker.amazonaws.com`.

## Output

Findings by file with severity tags, a severity summary table, and an explicit statement of what was verified
statically vs what needs a running container / AWS account.
