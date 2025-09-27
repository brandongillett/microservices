#!/usr/bin/env bash
set -e
set -x

mypy src
ruff check libs src
ruff format libs src --check
