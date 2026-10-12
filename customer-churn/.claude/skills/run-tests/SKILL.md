---
name: run-tests
description: Runs customer-churn's quality gates — unit tests, format and lint, the pipeline definition render, Serverless packaging and the model image SageMaker-contract check. Use before considering a change done or when asked to verify the project.
---

# Run tests and checks

Run inside the `DataScienceCustomerChurn` devcontainer (or `docker exec DataScienceCustomerChurn sh -c "cd /app/customer-churn && <cmd>"`).
Test layout and mocking: `.claude/rules/testing.md`.

## 1. Unit tests, format, lint

```bash
npm test           # pytest + coverage (htmlcov/)
npm run format
npm run lint       # pylint src tests + eslint serverless container
```

## 2. Pipeline definition render (no AWS)

```bash
node -e "require('./serverless/pipeline/pipeline-definition.js')({resolveVariable: async (k) => k === 'aws:accountId' ? '123456789012' : (k.includes('InstanceTypes') ? ['ml.m5.large'] : 'x')}).then((s) => console.log(JSON.parse(s).Steps.map((x) => x.Name)))"
```

Expected: `[ 'PrepareData', 'Baseline', 'Train', 'Evaluate', 'CheckAuc' ]`.

## 3. Serverless resolution and packaging (needs AWS credentials + deployed dependencies)

From each touched `serverless/<stack>/`: `serverless print --stage dev` and `serverless package --stage dev`. For
`pipeline` before the image exists: `SKIP_IMAGE_CHECK=true serverless print`.

## 4. Image contract (needs Docker)

```bash
npm run image:build-local
python3 -m src.scripts.download_dataset
S=$(mktemp -d); mkdir -p $S/athena $S/ml/input/config $S/ml/input/data
python3 -c "import pandas as pd; from src.features.curation import curate; curate(pd.read_csv('data/local/telco_customer_churn.csv')).to_json('$S/athena/part-0', orient='records', lines=True)"
docker run --rm -v $S/athena:/opt/ml/processing/input/data -v $S/out:/opt/ml/processing/out \
  --entrypoint python3 customer-churn-model:local -m src.pipelines.training.preprocess --min-rows 500 --output-dir /opt/ml/processing/out
cp -r $S/out/train $S/out/validation $S/ml/input/data/ && echo '{"max_iter":"300"}' > $S/ml/input/config/hyperparameters.json
docker run --rm -v $S/ml:/opt/ml customer-churn-model:local train
docker run -d --name churn-serve -p 18080:8080 -v $S/ml/model:/opt/ml/model customer-churn-model:local serve
sleep 5; curl -s localhost:18080/ping -o /dev/null -w "%{http_code}\n"
sed -n 2,3p $S/out/baseline/baseline.csv | curl -s -X POST localhost:18080/invocations -H 'Content-Type: text/csv' --data-binary @-
docker rm -f churn-serve
```

Paths: the devcontainer talks to the host daemon, so `-v` paths must exist on the host — run this block from a host
shell or use a folder under the mounted repository instead of `mktemp`.

Repository note: steps 1, 2 and 4 need nothing deployed; step 3 needs `infrastructure/serverless/common` and the
upstream project stacks (`.claude/rules/deployment.md`).
