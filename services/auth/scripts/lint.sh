#!/usr/bin/env bash
set -e
set -x

mypy --package src --package libs
ruff check src libs scripts
ruff format src libs scripts --check
