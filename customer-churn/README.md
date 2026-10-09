# README

- [README](#readme)
  - [Summary](#summary)
  - [Setup](#setup)
    - [Development container](#development-container)
    - [Environment variables](#environment-variables)
    - [Dependencies](#dependencies)
    - [Deployment](#deployment)
    - [Updates](#updates)
    - [Model approval](#model-approval)
    - [Operation](#operation)
    - [Local development](#local-development)
    - [Remove](#remove)
  - [Contribution guidelines](#contribution-guidelines)
    - [Code review](#code-review)
    - [Other guidelines](#other-guidelines)
  - [Glossary](#glossary)
    - [Service environment variables: `.envs/config.env`](#service-environment-variables-envsconfigenv)
    - [Serverless Framework deployment variables](#serverless-framework-deployment-variables)

---

## Summary

`Data Science > Customer Churn` project is the reference MLOps project of the repository. It predicts which customers will churn using the public [IBM Telco Customer Churn](https://github.com/IBM/telco-customer-churn-on-icp4d) dataset, and implements the full model lifecycle on AWS: event-driven ingestion, Glue cataloging, curation and data quality, Athena, a SageMaker training pipeline, Model Registry with manual approval, a real-time endpoint with monitoring, an HTTP prediction API and batch scoring.

Every SageMaker workload (processing, training and serving) runs the project's own Docker image, published to ECR.

These resources are created as `Infrastructure as Code` and deployed using `Serverless Framework`.

---

## Setup

### Development container

This steps are tailored to work with Visual Studio Code, but you are free to chose a different IDE and make necessary adjustments to the setup.

1. Install `ms-vscode-remote.remote-containers` extension. If you don't know how to do that follow this steps: <https://code.visualstudio.com/docs/editor/extension-gallery#_install-an-extension>
2. Make sure Docker is running on your machine: the container uses the host Docker daemon to build the model image.
3. Open this project's folder in Visual Studio Code. The extension will detect a container configuration and will ask you if you want to reopen the project in the container. Accept.

### Environment variables

At `.envs` folder, you'll need to create env files with the variables described in the [Glossary](#glossary). You can start from `.envs/config.env.example`.

### Dependencies

You need these `Cloud Formation Stacks` deployed:

- `Data Science > Infrastructure > common` stack (buckets, Athena workgroup, notifications topic)

### Deployment

You can deploy `Cloud Formation Stacks` using `Serverless Framework` syntax: <https://www.serverless.com/framework/docs/providers/aws/cli-reference/deploy/>

The deployment order is the same for `dev`, `test` and `prod` — replace `<stage>` in every command below with the target stage (e.g. `npm run deploy-data:test`). AWS credentials in `../.envs/aws.env` must belong to that stage's account.

1. Deploy `serverless/data` stack: `npm run deploy-data:<stage>`
2. Deploy `serverless/image` stack: `npm run deploy-image:<stage>`
3. Build and push the model image to ECR: `npm run image:push`. Docker must be running on your machine. If an image with the same tag already exists, nothing is built
4. Deploy `serverless/pipeline` stack: `npm run deploy-pipeline:<stage>`. It fails if the image of step 3 is not in ECR
5. Load the dataset into the data lake: `npm run ingest`. This starts the data curation and, when it succeeds, a training pipeline execution
6. Wait until the training pipeline execution succeeds: `npm run pipeline:executions`. When it finishes, the notifications topic sends an email with the new model version waiting for approval
7. Approve the model version (see [Model approval](#model-approval))
8. Deploy `serverless/endpoint` stack: `npm run deploy-endpoint:<stage>`
9. Deploy `serverless/batch` stack: `npm run deploy-batch:<stage>`

### Updates

| Change                                                                                           | Steps                                                                                                                |
| ------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------------- |
| Code of the model (`src/features`, `src/models`, `src/pipelines`, `src/serving`) or `container/` | Step 3 (`npm run image:push`), then step 4 (`npm run deploy-pipeline:<stage>`). The next training uses the new image |
| A new model version was approved                                                                 | Step 8 (`npm run deploy-endpoint:<stage>`) releases it in the endpoint. Batch scoring uses it on its next run        |
| Glue job (`src/jobs/glue`) or data stack configuration                                           | Step 1 (`npm run deploy-data:<stage>`)                                                                               |
| Lambdas or configuration of a stack                                                              | Deploy only that stack                                                                                               |

### Model approval

Every trained model that passes the quality threshold (`MIN_ROC_AUC`) is registered in the `customer-churn` model package group as `PendingManualApproval`, and an email is sent to the notifications topic.

```bash
npm run models                                   # list versions, status and test ROC AUC
npm run models -- --approve <version>            # approve
npm run models -- --reject <version> --description "<reason>"
```

Models can also be approved from SageMaker Studio → `Models` → `customer-churn`.

### Operation

| Task                                                               | Command                                                             |
| ------------------------------------------------------------------ | ------------------------------------------------------------------- |
| Load the dataset into the data lake (starts curation and training) | `npm run ingest`                                                    |
| Load the dataset with simulated drift                              | `npm run ingest:drift`                                              |
| Start a training pipeline execution manually                       | `npm run pipeline:start`                                            |
| List the last pipeline executions                                  | `npm run pipeline:executions`                                       |
| Run batch scoring now                                              | `npm run batch:run`                                                 |
| Send traffic to the prediction API                                 | `python3 -m src.scripts.generate_traffic --api-url <url> [--drift]` |

The prediction API URL is stored in the SSM parameter `/data-science-customer-churn-endpoint/PredictUrl`. The API has no authentication and accepts up to 10 requests per second (bursts of 20); extra requests get `429 Too Many Requests`. Example:

```bash
URL=$(aws ssm get-parameter --name /data-science-customer-churn-endpoint/PredictUrl --query Parameter.Value --output text)
curl -s -X POST "$URL" -H 'Content-Type: application/json' -d '{
  "customers": [{
    "customer_id": "0001-TEST", "gender": "Female", "senior_citizen": 0, "partner": "Yes", "dependents": "No",
    "tenure": 2, "phone_service": "Yes", "multiple_lines": "No", "internet_service": "Fiber optic",
    "online_security": "No", "online_backup": "No", "device_protection": "No", "tech_support": "No",
    "streaming_tv": "Yes", "streaming_movies": "Yes", "contract": "Month-to-month", "paperless_billing": "Yes",
    "payment_method": "Electronic check", "monthly_charges": 95.7, "total_charges": 191.4
  }]
}'
```

### Local development

```bash
npm run local:download      # downloads the dataset to data/local/
npm run local:train         # trains and evaluates the model locally, without AWS
npm run image:build-local   # builds the model image locally
npm test
npm run format
npm run lint
```

### Remove

You must use `Serverless Framework` remove command as primary option: <https://www.serverless.com/framework/docs/providers/aws/cli-reference/remove/>

If `remove` command fails for whatever reason, you'll need to investigate the reason using `AWS Console` at your browser, solve the issue and then re-attempt the `remove` command.

You can, alternatively, delete the `AWS Cloud Formation` stack manually using `AWS Console` at your browser. But it's recommended to do it using the `remove` command from Serverless Framework.

Recommended remove order is inverse to deployment order. The `serverless/endpoint` stack has an hourly cost while it exists: remove it when it's not in use.

The ECR repository is retained when `serverless/image` is removed (registered models depend on its images); delete it manually if it's no longer needed.

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
- `MIN_ROC_AUC` _(Optional)_: Minimum test ROC AUC a trained model needs to be registered. Default value is `0.80`
- `SKIP_IMAGE_CHECK` _(Optional)_: `true` skips the check that the model image exists in ECR when resolving `serverless/pipeline` (e.g. to run `serverless print` before the image is pushed). Default value is `false`

### Serverless Framework deployment variables

- `stage`: Means the deployment stage. Values can be `dev`, `test` or `prod`
- Other deployment options can be set through CLI command. More info in the [Serverless Framework deploy CLI reference](https://www.serverless.com/framework/docs/providers/aws/cli-reference/deploy/)
