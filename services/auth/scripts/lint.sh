#!/usr/bin/env bash
set -e
set -x

mypy app
ruff check app libs scripts
ruff format app libs scripts --check
