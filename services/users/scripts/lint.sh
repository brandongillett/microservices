#!/usr/bin/env bash
set -e
set -x

mypy app
ruff check libs app
ruff format libs app --check
