"""Glue ETL job (Spark): raw zone CSV → curated zone Parquet.

    1. Reads the raw CSV files of one ingestion date
       (raw/<project>/ingestion_date=YYYY-MM-DD/*.csv).
    2. Renames to snake_case, casts types, normalizes categories and turns the
       target into 0/1 (pandas mirror: src/features/curation.py — keep in sync).
    3. Evaluates the Glue Data Quality ruleset; a failing rule fails the job,
       so no downstream training runs on bad data.
    4. Overwrites that date's partition in the curated table (Parquet), which
       Athena reads through partition projection.

Job arguments: --RAW_PATH, --CURATED_PATH, --DQ_RULESET, --INGESTION_DATE
(optional; "latest" picks the most recent raw partition).
"""
import sys

from awsglue.context import GlueContext
from awsglue.dynamicframe import DynamicFrame
from awsglue.job import Job
from awsglue.utils import getResolvedOptions
from awsgluedq.transforms import EvaluateDataQuality
from pyspark.context import SparkContext
from pyspark.sql import functions as F

RAW_TO_CURATED = {
    "customerID": "customer_id",
    "gender": "gender",
    "SeniorCitizen": "senior_citizen",
    "Partner": "partner",
    "Dependents": "dependents",
    "tenure": "tenure",
    "PhoneService": "phone_service",
    "MultipleLines": "multiple_lines",
    "InternetService": "internet_service",
    "OnlineSecurity": "online_security",
    "OnlineBackup": "online_backup",
    "DeviceProtection": "device_protection",
    "TechSupport": "tech_support",
    "StreamingTV": "streaming_tv",
    "StreamingMovies": "streaming_movies",
    "Contract": "contract",
    "PaperlessBilling": "paperless_billing",
    "PaymentMethod": "payment_method",
    "MonthlyCharges": "monthly_charges",
    "TotalCharges": "total_charges",
    "Churn": "churn",
}
NON_CATEGORICAL = {
    "customer_id",
    "senior_citizen",
    "tenure",
    "monthly_charges",
    "total_charges",
    "churn",
}

args = getResolvedOptions(
    sys.argv,
    ["JOB_NAME", "RAW_PATH", "CURATED_PATH", "DQ_RULESET", "INGESTION_DATE"],
)
glue_context = GlueContext(SparkContext.getOrCreate())
spark = glue_context.spark_session
spark.conf.set("spark.sql.sources.partitionOverwriteMode", "dynamic")
# Keep `ingestion_date` (from the folder names) as a plain string.
spark.conf.set("spark.sql.sources.partitionColumnTypeInference.enabled",
               "false")
job = Job(glue_context)
job.init(args["JOB_NAME"], args)

# Spark discovers `ingestion_date` from the Hive-style folder names.
raw = spark.read.option("header", "true").csv(args["RAW_PATH"])
ingestion_date = args["INGESTION_DATE"]
if ingestion_date == "latest":
    ingestion_date = raw.agg(F.max("ingestion_date")).first()[0]
raw = raw.filter(F.col("ingestion_date") == F.lit(ingestion_date))
print(f"Curating ingestion_date={ingestion_date}")

curated = raw.select(
    *[F.col(source).alias(target) for source, target in RAW_TO_CURATED.items()])
for column in curated.columns:
    if column not in NON_CATEGORICAL:
        normalized = F.regexp_replace(F.lower(F.trim(F.col(column))),
                                      "[^a-z0-9]+", "_")
        curated = curated.withColumn(
            column, F.regexp_replace(normalized, "^_+|_+$", ""))

curated = (
    curated.withColumn("customer_id", F.trim("customer_id")).withColumn(
        "senior_citizen",
        F.col("senior_citizen").cast("int")).withColumn(
            "tenure",
            F.col("tenure").cast("int")).withColumn(
                "monthly_charges",
                F.col("monthly_charges").cast("double"))
    # Blank TotalCharges = brand-new customers (tenure 0) → null.
    .withColumn(
        "total_charges",
        F.when(F.trim("total_charges") == "",
               None).otherwise(F.col("total_charges").cast("double")),
    ).withColumn(
        "churn",
        (F.lower(F.trim("churn")) == "yes").cast("int"),
    ).dropDuplicates(["customer_id"]).withColumn("ingestion_date",
                                                 F.lit(ingestion_date)))

# Data quality gate (rules defined once in serverless/data/serverless.yml).
dq_results = EvaluateDataQuality.apply(
    frame=DynamicFrame.fromDF(curated, glue_context, "curated"),
    ruleset=args["DQ_RULESET"],
    publishing_options={
        "dataQualityEvaluationContext": "curated_customers",
        "enableDataQualityCloudWatchMetrics": True,
        "enableDataQualityResultsPublishing": True,
    },
).toDF()
dq_results.show(truncate=False)
failed_rules = dq_results.filter(F.col("Outcome") != "Passed").collect()
if failed_rules:
    raise RuntimeError("Data quality rules failed: " +
                       "; ".join(f"{row['Rule']} → {row['FailureReason']}"
                                 for row in failed_rules))

(curated.repartition(1).write.mode("overwrite").partitionBy(
    "ingestion_date").parquet(args["CURATED_PATH"]))
print(f"Wrote {curated.count()} rows to {args['CURATED_PATH']}")

job.commit()
