#!/bin/bash
# CI script: build, tag, and push docker image

set -euo pipefail

IMAGE=nearprotocol/nearup
VERSION=$(echo -n $(cat nearuplib/VERSION))

echo "logging into docker..."
echo "$DOCKER_PASSWORD" | docker login -u "$DOCKER_USERNAME" --password-stdin

echo "building latest version $VERSION..."
docker build . -t $IMAGE:$VERSION
docker tag $IMAGE:$VERSION $IMAGE:latest

echo "pushing $VERSION as latest..."
docker push $IMAGE:$VERSION
docker push $IMAGE:latest

echo "done!"
