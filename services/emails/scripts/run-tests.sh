#! /usr/bin/env bash
set -e

# Check if the environment is local or staging
if [ "$ENVIRONMENT" = "local" ] || [ "$ENVIRONMENT" = "staging" ]; then
    python src/prestart.py > /dev/null 2>&1

    coverage run -m pytest tests/
    # coverage report --show-missing
    coverage html --title "${@-coverage}"
else
    echo "Error: This script is only for local/staging environments."
    exit 1
fi
