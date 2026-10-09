# Model image (BYOC): the same image runs every SageMaker workload of the
# project, so the code and library versions are identical everywhere.
#   Processing  → ContainerEntrypoint ["python3", "-m", "src.pipelines.training.<step>"]
#   Training    → `docker run <image> train`
#   Endpoint /
#   Transform   → `docker run <image> serve` (HTTP on :8080, /ping + /invocations)
# Build context: the project folder (customer-churn/). Built and pushed by
# container/build-push.sh; tagged with container/image-version.js.
FROM python:3.13-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONPATH=/opt/program \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

COPY container/requirements.txt /tmp/requirements.txt
RUN pip install -r /tmp/requirements.txt && rm /tmp/requirements.txt

# Only the model packages (no Lambdas/scripts): /opt/program/src/...
WORKDIR /opt/program
COPY src/__init__.py src/__init__.py
COPY src/features/ src/features/
COPY src/models/ src/models/
COPY src/monitoring/ src/monitoring/
COPY src/pipelines/ src/pipelines/
COPY src/serving/ src/serving/
COPY container/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8080
ENTRYPOINT ["entrypoint.sh"]
