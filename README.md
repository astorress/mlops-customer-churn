# README

- [README](#readme)
  - [Summary](#summary)
  - [Setup](#setup)
    - [Development container](#development-container)
    - [Environment variables](#environment-variables)
    - [Deployment](#deployment)
    - [Remove](#remove)
  - [Glossary](#glossary)
    - [AWS environment variables: `.envs/aws.env`](#aws-environment-variables-envsawsenv)
    - [Serverless Framework environment variables: `.envs/sls.env`](#serverless-framework-environment-variables-envsslsenv)

---

## Summary

`Data Science` repository contains MLOps projects. Each sub-project is deployed independently:

- `infrastructure`: shared resources every MLOps project uses (data lake, ML artifacts and Athena results buckets, Athena workgroup, notifications topic, a VPC and a SageMaker Studio domain).
- `customer-churn`: reference MLOps project that predicts customer churn with the public IBM Telco Customer Churn dataset.

These resources are created as `Infrastructure as Code` and deployed using `Serverless Framework`.

---

## Setup

### Development container

This steps are tailored to work with Visual Studio Code, but you are free to chose a different IDE and make necessary adjustments to the setup.

1. Install `ms-vscode-remote.remote-containers` extension. If you don't know how to do that follow this steps: <https://code.visualstudio.com/docs/editor/extension-gallery#_install-an-extension>
2. Open the folder of the sub-project you'll work on in Visual Studio Code. The extension will detect a container configuration and will ask you if you want to reopen the project in the container. Accept.

This root folder has its own container only to browse the whole repository.

### Environment variables

At `.envs` folder, you'll need to create env files with the variables described in the [Glossary](#glossary). You can start from the `*.example` files.

Each sub-project needs its own env files too. They are described in each sub-project's README.

### Deployment

Each sub-project is deployed from its own development container. You can deploy `Cloud Formation Stacks` using `Serverless Framework` syntax: <https://www.serverless.com/framework/docs/providers/aws/cli-reference/deploy/>

The deployment order is the same for `dev`, `test` and `prod` — replace `<stage>` in every command below with the target stage (e.g. `npm run deploy-common:test`):

1. `infrastructure` (see [its README](infrastructure/README.md)):
   1. Deploy `serverless/common` stack: `npm run deploy-common:<stage>`
   2. Confirm the notifications subscription email
   3. Deploy `customlib/cloud-formation/virtual-private-cloud/serverless` stack: `npm run deploy-vpc:<stage>`
   4. Deploy `serverless/studio` stack: `npm run deploy-studio:<stage>`
2. `customer-churn` (see [its README](customer-churn/README.md)):
   1. Deploy `serverless/data` stack: `npm run deploy-data:<stage>`
   2. Deploy `serverless/image` stack: `npm run deploy-image:<stage>`
   3. Build and push the model image: `npm run image:push`
   4. Deploy `serverless/pipeline` stack: `npm run deploy-pipeline:<stage>`
   5. Load the dataset (starts curation and the first training): `npm run ingest`
   6. Wait until the training pipeline execution succeeds: `npm run pipeline:executions`
   7. Approve the model version: `npm run models -- --approve <version>`
   8. Deploy `serverless/endpoint` stack: `npm run deploy-endpoint:<stage>`
   9. Deploy `serverless/batch` stack: `npm run deploy-batch:<stage>`

Every MLOps project depends on `infrastructure > serverless/common`; MLOps projects don't depend on each other.

### Remove

Remove sub-projects in the inverse order: first every MLOps project (inverse order of its own stacks), then `infrastructure`. Each README's `Remove` section has the details.

---

## Glossary

### AWS environment variables: `.envs/aws.env`

- `AWS_ACCESS_KEY_ID`: _Access Key_ used to deploy Cloud Formation stack to AWS cloud. The owner of the _Access Key_ need to have sufficient IAM permissions to perform the deployment process.
- `AWS_SECRET_ACCESS_KEY`: _Secret Access Key_ that matches the _Access Key_
- `AWS_DEFAULT_REGION`: Region where you intend to deploy the stack. Stacks only allow `us-east-1`
- `AWS_DEFAULT_OUTPUT`: Default response format for AWS CLI commands
- `AWS_ORGANIZATION_ID`: ID of the AWS Organization that will be able to communicate with the account where this service is deployed.

### Serverless Framework environment variables: `.envs/sls.env`

- `SERVERLESS_ACCESS_KEY`: Serverless _Secret API Key_. Needed to deploy stack information to Serverless cloud.
- `ORG`: Short organization name (lowercase, no spaces). Used as prefix of every bucket name, so it must make them globally unique. E.g. `myorg`
