#!/usr/bin/env bash
set -e
set -x

mypy --package src --package libs --package tests
ruff check src tests libs scripts
ruff format src tests libs scripts --check
