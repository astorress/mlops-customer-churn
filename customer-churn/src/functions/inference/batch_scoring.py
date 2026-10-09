"""Batch inference: scores every active customer (churn = 0) of the latest
curated partition with the latest *approved* model.

    1. Athena UNLOAD → headerless CSV (customer_id + FEATURES) in the
       artifacts bucket.
    2. CreateModel from the approved model package (Model Registry).
    3. Batch Transform job: drops customer_id before the model
       (InputFilter), joins the probability back (JoinSource/OutputFilter) and
       writes predictions to the data lake, queryable in Athena through the
       `predictions` table.

Event (optional): {"ingestion_date": "YYYY-MM-DD"} to score a given partition.
"""
import json
import os
from datetime import datetime, timezone

from src.features.schema import (
    FEATURES,
    ID_COLUMN,
    TARGET,
)
from src.services import (
    athena,
    sagemaker,
    ssm,
)
from src.utilities.errors import NoApprovedModelError
from src.utilities.logger import get_logger

logger = get_logger(__name__)

ATHENA_WORKGROUP = os.environ.get("ATHENA_WORKGROUP", "")
GLUE_DATABASE = os.environ.get("GLUE_DATABASE", "")
CURATED_TABLE = os.environ.get("CURATED_TABLE", "")
ARTIFACTS_BUCKET_NAME = os.environ.get("ARTIFACTS_BUCKET_NAME", "")
BATCH_INPUT_PREFIX = os.environ.get("BATCH_INPUT_PREFIX", "")
DATA_LAKE_BUCKET_NAME = os.environ.get("DATA_LAKE_BUCKET_NAME", "")
PREDICTIONS_PREFIX = os.environ.get("PREDICTIONS_PREFIX", "")
MODEL_PACKAGE_ARN_PARAMETER = os.environ.get(
    "APPROVED_MODEL_PACKAGE_ARN_PARAMETER", "")
SAGEMAKER_ROLE_ARN = os.environ.get("SAGEMAKER_ROLE_ARN", "")
RESOURCE_PREFIX = os.environ.get("RESOURCE_PREFIX", "customer-churn")
TRANSFORM_INSTANCE_TYPE = os.environ.get("TRANSFORM_INSTANCE_TYPE",
                                         "ml.m5.large")


def build_unload_query(output_uri: str,
                       ingestion_date: str | None = None) -> str:
    table = f'"{GLUE_DATABASE}"."{CURATED_TABLE}"'
    partition = (f"'{ingestion_date}'" if ingestion_date else
                 f"(SELECT max(ingestion_date) FROM {table})")
    columns = ", ".join([ID_COLUMN] + FEATURES)
    return (f"UNLOAD (SELECT {columns} FROM {table} "
            f"WHERE ingestion_date = {partition} AND {TARGET} = 0) "
            f"TO '{output_uri}' "
            "WITH (format = 'TEXTFILE', field_delimiter = ',')")


def get_approved_model_package() -> str:
    arn = ssm.get_parameter(MODEL_PACKAGE_ARN_PARAMETER)
    if not arn.startswith("arn:"):
        raise NoApprovedModelError(
            "No approved model yet: approve a model package in the registry")
    return arn


def transform_request(job_name: str, model_name: str, input_uri: str,
                      output_uri: str, model_package_arn: str) -> dict:
    return {
        "TransformJobName": job_name,
        "ModelName": model_name,
        "BatchStrategy": "MultiRecord",
        "MaxPayloadInMB": 6,
        "TransformInput": {
            "DataSource": {
                "S3DataSource": {
                    "S3DataType": "S3Prefix",
                    "S3Uri": input_uri,
                },
            },
            "ContentType": "text/csv",
            # Athena UNLOAD writes gzipped text files.
            "CompressionType": "Gzip",
            "SplitType": "Line",
        },
        "TransformOutput": {
            "S3OutputPath": output_uri,
            "Accept": "text/csv",
            "AssembleWith": "Line",
        },
        "TransformResources": {
            "InstanceType": TRANSFORM_INSTANCE_TYPE,
            "InstanceCount": 1,
        },
        "DataProcessing": {
            # Drop customer_id before the model, then keep id + probability.
            "InputFilter": "$[1:]",
            "JoinSource": "Input",
            "OutputFilter": "$[0,-1]",
        },
        "Tags": [{
            "Key": "ModelPackageArn",
            "Value": model_package_arn,
        }],
    }


def handler(event, context):
    event = event or {}
    now = datetime.now(timezone.utc)
    run_id = now.strftime("%Y%m%d-%H%M%S")
    input_uri = f"s3://{ARTIFACTS_BUCKET_NAME}/{BATCH_INPUT_PREFIX}/{run_id}/"
    output_uri = (f"s3://{DATA_LAKE_BUCKET_NAME}/{PREDICTIONS_PREFIX}/"
                  f"run_date={now.strftime('%Y-%m-%d')}/")
    model_package_arn = get_approved_model_package()

    athena.run_query(
        build_unload_query(input_uri, event.get("ingestion_date")),
        ATHENA_WORKGROUP,
    )

    model_name = f"{RESOURCE_PREFIX}-batch-{run_id}"
    sagemaker.create_model_from_package(
        model_name,
        SAGEMAKER_ROLE_ARN,
        model_package_arn,
    )
    job_name = f"{RESOURCE_PREFIX}-{run_id}"
    sagemaker.create_transform_job(**transform_request(
        job_name,
        model_name,
        input_uri,
        output_uri,
        model_package_arn,
    ))
    result = {
        "transform_job_name": job_name,
        "model_package_arn": model_package_arn,
        "input": input_uri,
        "output": output_uri,
    }
    logger.info(json.dumps(result))
    return result
