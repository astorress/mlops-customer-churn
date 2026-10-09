---
name: code-review
description: Rigorous checklist-driven review of the infrastructure sub-service's container setup, package dependencies, devcontainer and Serverless stacks. Use when asked to review infrastructure's tooling/config, after changing .docker/, .devcontainer.json, package.json or serverless/*.yml.
---

# Code review — infrastructure (container, dependencies, stacks)

Rules: read every file below **completely** before concluding; many bugs only show when comparing two files. Trace
every path end to end. Check parity in both directions. Never skip an item because it looks unchanged. Report
findings even without immediate impact. If something can't be verified statically, say so.

Files: `../.docker/Dockerfile` (stages `img-base`, `img-infrastructure`), `.docker/docker-compose.yml`,
`.docker/entrypoint.sh`, `../.docker/git.sh`, `../.docker/aws.sh`, `.devcontainer.json`, `package.json`,
`eslint.config.mjs`, `.prettierignore`, `serverless/*/serverless.yml` and every file they `${file()}`.

Severity tags: **[BUG]** broken at runtime · **[SILENT FAILURE]** wrong result, no error · **[CONFLICT]** two installs
of the same thing · **[WASTE]** unnecessary layer/package · **[RISK]** correct today, fragile.

## Checklist

### Dockerfile

- [ ] Python comes only from the `python-base` multi-stage COPY; grep for any `apt-get install ... python3` (would
      shadow `/usr/local/bin/python3`).
- [ ] Every tool used by `entrypoint.sh`, `git.sh`, `aws.sh` and npm scripts is installed in `img-base`
      (`git`, `jq`, `aws`, `tput`/ncurses, `sudo`, `node`/`npm`, `serverless`).
- [ ] No standalone `apt-get update` layer that can go stale relative to later `apt-get install` layers (note: the
      shared Dockerfile has one — report it as [RISK] once, it affects every target).
- [ ] AWS CLI install handles `amd64` and `arm64`.
- [ ] `ARG USER` is visible in `img-infrastructure` (`USER $USER`): ARGs don't cross stages unless re-declared —
      verify the effective user (`docker run --rm <image> whoami`) and say if it needs a running container.

### devcontainer.json

- [ ] `serverlessIDE.cfnLint.path` = `/usr/local/bin/cfn-lint` matches `pip3 install cfn-lint` (pip → `/usr/local/bin`).
- [ ] `cfn_lint_serverless.rules` ↔ `pip3 install cfn-lint-serverless`.
- [ ] Every extension has its tool/setting and every setting its extension (eslint ↔ `eslint` devDependency,
      prettier ↔ `prettier`, markdownlint ↔ `.markdownlint.json`).

### package.json

- [ ] `deploy-vpc:*` scripts point to `customlib/cloud-formation/virtual-private-cloud/serverless` (that stack uses the
      library's own bundled plugins, not this `package.json`).
- [ ] Every plugin listed in any `serverless/*/serverless.yml` (`serverless-deployment-bucket`,
      `@serverless/safeguards-plugin`) is a devDependency, and every devDependency is used (both directions).
- [ ] Every `deploy-*` script `cd`s into a folder that exists (`serverless/common`, `serverless/studio`).
- [ ] `format`/`lint` globs cover `serverless/**/*.{yml,js}` including `serverless/shared/`.

### entrypoint.sh

- [ ] Works from any CWD (`EXEC_PATH`/`HOME_PATH` from `readlink -f "$0"`); `npm install` runs in the project folder.
- [ ] `STEP_COUNT` equals the number of `STEP` echoes.
- [ ] The customlib block clones `library/cloud-formation/virtual-private-cloud`, checks out
      `$GIT_CFN_VIRTUAL_PRIVATE_CLOUD_BRANCH_NAME`, calls `sh dist.sh`, and returns to `$EXEC_PATH` before `npm install`.
- [ ] `git.sh` (GitLab SSH command) runs before the clone; compose mounts the `gitlab_ssh_private_key` secret.
- [ ] `aws.sh` runs before the first `aws` call (`list-account-aliases`).

### docker-compose.yml

- [ ] `env_file`: `../../.envs/aws.env`, `../../.envs/sls.env`, `../.envs/config.env`.
- [ ] Secret `gitlab_ssh_private_key` ↔ Dockerfile symlink `/run/secrets/gitlab_ssh_private_key`.
- [ ] Volume `/commandhistory` ↔ Dockerfile `HISTFILE=/commandhistory/.bash_history`.
- [ ] `target: img-infrastructure` exists in the Dockerfile; `dockerfile` path is relative to `context`.

### Stacks

- [ ] Each stack: `frameworkVersion`, safeguards (regions, stages, IAM wildcards), `deploymentBucket` naming,
      `cfn-collisions.yml` included.
- [ ] Every `${ssm:...}` in `studio` is produced by `common/ssm.yml` or by the VPC library
      (`/SLS/${env:DEPLOY_APP}-cloud-formation-vpc/{VPC,AppSubnets}`); `DEPLOY_APP` is set in `docker-compose.yml`.
- [ ] `.envs/config.env.example` lists every `LIBCFNVPC_*` value `.claude/rules/dependencies.md` requires.
- [ ] Every SSM parameter in `common/ssm.yml` is documented in `.claude/rules/integrations.md` (and vice versa).
- [ ] IAM: `Resource: '*'` only where the API requires it.

## Output

Findings grouped by file with severity tags, then a summary table (severity → count) and an explicit statement of
which items were verified statically and which need a running container.
