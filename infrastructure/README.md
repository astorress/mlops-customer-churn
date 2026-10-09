# README

- [README](#readme)
  - [Summary](#summary)
  - [Setup](#setup)
    - [Development container](#development-container)
    - [Environment variables](#environment-variables)
    - [Dependencies](#dependencies)
    - [Deployment](#deployment)
    - [Notifications subscription](#notifications-subscription)
    - [Remove](#remove)
  - [Contribution guidelines](#contribution-guidelines)
    - [Code review](#code-review)
    - [Other guidelines](#other-guidelines)
  - [Glossary](#glossary)
    - [Service environment variables: `.envs/config.env`](#service-environment-variables-envsconfigenv)
    - [Serverless Framework deployment variables](#serverless-framework-deployment-variables)

---

## Summary

`Data Science > Infrastructure` project contains the resources shared by every MLOps project of the repository: data lake, ML artifacts and Athena results buckets, the Athena workgroup, the notifications topic, and the SageMaker Studio domain with its VPC.

These resources are created as `Infrastructure as Code` and deployed using `Serverless Framework`.

---

## Setup

### Development container

This steps are tailored to work with Visual Studio Code, but you are free to chose a different IDE and make necessary adjustments to the setup.

1. Install `ms-vscode-remote.remote-containers` extension. If you don't know how to do that follow this steps: <https://code.visualstudio.com/docs/editor/extension-gallery#_install-an-extension>
2. Open this project's folder in Visual Studio Code. The extension will detect a container configuration and will ask you if you want to reopen the project in the container. Accept.

### Environment variables

At `.envs` folder, you'll need to create env files with the variables described in the [Glossary](#glossary). You can start from `.envs/config.env.example`.

### Dependencies

This project must be deployed before any MLOps project.

Cloud Formation packages (cloned into `customlib/` when the development container is created):

- `Library > Cloud Formation > Virtual Private Cloud` repository distribution. Creates the VPC used by the SageMaker Studio domain.

### Deployment

You can deploy `Cloud Formation Stacks` using `Serverless Framework` syntax: <https://www.serverless.com/framework/docs/providers/aws/cli-reference/deploy/>

Deployment order:

1. Deploy `serverless/common` stack: `npm run deploy-common:<stage>`
2. Confirm the [notifications subscription](#notifications-subscription)
3. Deploy `customlib/cloud-formation/virtual-private-cloud/serverless` stack: `npm run deploy-vpc:<stage>`
4. Deploy `serverless/studio` stack: `npm run deploy-studio:<stage>`

To open SageMaker Studio: AWS Console → `SageMaker AI` → `Domains` → `data-science` → your user profile → `Launch` → `Studio`.

### Notifications subscription

Every email in `NOTIFICATION_EMAILS` receives an `AWS Notification - Subscription Confirmation` email after the first deployment of `serverless/common`. Each recipient must click the confirmation link, otherwise no MLOps notification reaches them.

### Remove

You must use `Serverless Framework` remove command as primary option: <https://www.serverless.com/framework/docs/providers/aws/cli-reference/remove/>

If `remove` command fails for whatever reason, you'll need to investigate the reason using `AWS Console` at your browser, solve the issue and then re-attempt the `remove` command. Buckets must be empty before they can be removed.

Recommended remove order is inverse to deployment order, and only after every MLOps project has been removed.

When `serverless/studio` is removed, SageMaker may keep resources it created outside Cloud Formation (the users' home EFS file system, its mount targets and security groups). Delete them from `AWS Console` before removing the VPC stack, otherwise the VPC can't be deleted.

---

## Contribution guidelines

### Code review

- Use known standards where situation allows it.
- Use known solutions for known problems.

### Other guidelines

- Investigate known and proven solutions before manufacturing your own.
- Check if our cloud provider offers a service you could use to solve the problem: evaluate ease of use, costs, maturity and reviews.
- If you need to use a library make sure it's mature, has continuos releases, it's stable.
- If a solution starts to get too messy, it's probably not the right solution.

---

## Glossary

### Service environment variables: `.envs/config.env`

- `DEVELOPER`: Same username as you corporate email without domain part. It's used to guarantee some unique resource names at deploy
- `NOTIFICATION_EMAILS`: Comma-separated emails subscribed to the MLOps notifications topic (pipeline failures, models pending approval, approved models, endpoint and drift alarms). E.g. `alice@example.com,bob@example.com`
- `GIT_CFN_VIRTUAL_PRIVATE_CLOUD_REPOSITORY`: Git URL of the _Library > Cloud Formation > Virtual Private Cloud_ repository, cloned into `customlib/` by the development container.
- `GIT_CFN_VIRTUAL_PRIVATE_CLOUD_BRANCH_NAME`: Git branch name to pull from _Library > Cloud Formation > Virtual Private Cloud_ repository.
- `LIBCFNVPC_VPC_CREATE_NAT_GATEWAY`: Amount of NAT Gateways of the VPC. Use `false`: SageMaker Studio runs in public internet mode and doesn't need them. The library default creates one
- `LIBCFNVPC_DB_PORT`: The library always includes database security group rules that need a port, even when no database exists. Use `5432`; it only creates an unused security group

There are other variables that can be configured for the VPC library. They are described in the README file of the dependency:

- `Library > Cloud Formation > Virtual Private Cloud` repository (URL set in `GIT_CFN_VIRTUAL_PRIVATE_CLOUD_REPOSITORY`)

### Serverless Framework deployment variables

- `stage`: Means the deployment stage. Values can be `dev`, `test` or `prod`
- Other deployment options can be set through CLI command. More info in the [Serverless Framework deploy CLI reference](https://www.serverless.com/framework/docs/providers/aws/cli-reference/deploy/)
