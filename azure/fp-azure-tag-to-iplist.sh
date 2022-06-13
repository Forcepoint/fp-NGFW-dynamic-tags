#!/bin/bash

VERSION="1.0"
NAME="fp-azure-tag-to-iplist"

source ./.env

export AZURE_TENANT_ID=$AZURE_TENANT_ID
export AZURE_CLIENT_ID=$AZURE_CLIENT_ID
export AZURE_CLIENT_SECRET=$AZURE_CLIENT_SECRET
export SMC_ADDRESS=$SMC_ADDRESS
export SMC_API_KEY=$SMC_API_KEY
export SMC_TIMEOUT=$SMC_TIMEOUT || 30
export SMC_CLIENT_CERT=$SMC_CLIENT_CERT
export SMC_API_VERSION=$SMC_API_VERSION

docker_start() {
    docker run --rm \
        --env AZURE_TENANT_ID --env AZURE_CLIENT_ID --env AZURE_CLIENT_SECRET \
        --env SMC_ADDRESS --env SMC_API_KEY --env SMC_TIMEOUT --env SMC_API_VERSION \
        $NAME:$VERSION "$@"
}

docker_start_with_cert_volume() {
    CERT_NAME=$(basename "$SMC_CLIENT_CERT")
    CERT_PATH="$SMC_CLIENT_CERT"
    SMC_CLIENT_CERT="/app/$CERT_NAME"

    docker run --rm -v "$CERT_PATH:$SMC_CLIENT_CERT" \
        --env AZURE_TENANT_ID --env AZURE_CLIENT_ID --env AZURE_CLIENT_SECRET \
        --env SMC_ADDRESS --env SMC_API_KEY --env SMC_TIMEOUT --env SMC_API_VERSION --env SMC_CLIENT_CERT \
        $NAME:$VERSION "$@"
}

if [ ! -z "$SMC_CLIENT_CERT" ]; then
    if [ ! -f "$SMC_CLIENT_CERT" ]; then
        echo "Could not find cert file specified: $SMC_CLIENT_CERT"
        exit 1
    fi
    docker_start_with_cert_volume
else
    docker_start
fi
