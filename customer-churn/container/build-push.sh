#!/bin/bash
# Builds the model image for SageMaker (linux/amd64) and pushes it to the
# project's ECR repository, tagged with container/image-version.js. Skips
# the build when that tag already exists (tags are immutable).
set -euo pipefail

PROJECT_DIR=$(cd "$(dirname "$0")/.." && pwd)
SSM_PREFIX=/data-science-customer-churn-image

TAG=$(node -e "console.log(require('$PROJECT_DIR/container/image-version.js').imageVersion())")
REPOSITORY_URI=$(aws ssm get-parameter --name "$SSM_PREFIX/RepositoryUri" --query Parameter.Value --output text)
REPOSITORY_NAME=${REPOSITORY_URI#*/}
REGISTRY=${REPOSITORY_URI%%/*}
IMAGE=$REPOSITORY_URI:$TAG

if aws ecr describe-images --repository-name "$REPOSITORY_NAME" --image-ids "imageTag=$TAG" > /dev/null 2>&1; then
    echo "Image $IMAGE already pushed. Nothing to do."
    exit 0
fi

aws ecr get-login-password | docker login --username AWS --password-stdin "$REGISTRY"

# SageMaker hosting (CreateModel) only accepts Docker v2 manifests, and a plain
# `docker push` from Docker Desktop's containerd image store uploads OCI ones.
# A dedicated buildx builder exports Docker media types explicitly, without
# provenance/SBOM attestations, for SageMaker's x86 instances.
BUILDER=data-science-builder
if ! docker buildx inspect "$BUILDER" > /dev/null 2>&1; then
    docker buildx create --name "$BUILDER" --driver docker-container > /dev/null
fi
docker buildx build --builder "$BUILDER" --platform linux/amd64 \
    --provenance=false --sbom=false \
    --output "type=image,name=$IMAGE,push=true,oci-mediatypes=false" \
    -f "$PROJECT_DIR/container/Dockerfile" "$PROJECT_DIR"

MEDIA_TYPE=$(aws ecr describe-images --repository-name "$REPOSITORY_NAME" --image-ids "imageTag=$TAG" \
    --query "imageDetails[0].imageManifestMediaType" --output text)
if [ "$MEDIA_TYPE" != "application/vnd.docker.distribution.manifest.v2+json" ]; then
    echo "ERROR: $IMAGE was pushed with manifest $MEDIA_TYPE; SageMaker endpoints need Docker v2." >&2
    exit 1
fi
echo "Pushed $IMAGE ($MEDIA_TYPE)"
