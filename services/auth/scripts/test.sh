#!/usr/bin/env bash
set -e
set -x

coverage run --source=src -m pytest -q
#coverage report --show-missing
coverage html --title "${@-coverage}"
