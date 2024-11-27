#! /usr/bin/env bash
set -e

if [ "$ENVIRONMENT" = "production" ]; then
    echo "Cannot run tests in production"
    exit 1
fi

python app/backend_pre_start.py > /dev/null 2>&1

bash scripts/test.sh "$@"
