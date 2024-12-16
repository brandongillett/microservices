#!/usr/bin/env bash
set -e
set -x

mypy src
ruff check src libs scripts
ruff format src libs scripts --check
