#!/usr/bin/env bash
set -e
set -x

coverage run --source=app -m pytest -q
#coverage report --show-missing
coverage html --title "${@-coverage}"
