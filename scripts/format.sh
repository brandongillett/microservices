#!/usr/bin/env bash

set -e

#Libs
echo "Formatting libs..."
uv run --with ruff==0.8.1 ruff check libs --fix
uv run --with ruff==0.8.1  ruff format libs

#Auth service
echo "Formatting auth service..."
uv run --with ruff==0.8.1 ruff check services/auth/app services/auth/scripts --config services/auth/pyproject.toml --fix
uv run --with ruff ruff format services/auth/app services/auth/scripts --config services/auth/pyproject.toml

#Users service
echo "Formatting users service..."
uv run --with ruff==0.8.1 ruff check services/users/app services/users/scripts --fix --config services/users/pyproject.toml
uv run --with ruff==0.8.1  ruff format services/users/app services/users/scripts --config services/users/pyproject.toml

#Pre-commit
echo "Running pre-commit..."
uv run --with pre-commit pre-commit run --all-files --verbose
