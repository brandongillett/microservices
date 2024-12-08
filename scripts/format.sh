#!/usr/bin/env bash

set -e

#Auth service
echo "Formatting auth service..."
uv run --with ruff==0.8.1 ruff check services/auth/app --config services/auth/pyproject.toml --fix
uv run --with ruff ruff format services/auth/app --config services/auth/pyproject.toml

#Users service
echo "Formatting users service..."
uv run --with ruff==0.8.1 ruff check services/users/app --fix --config services/users/pyproject.toml
uv run --with ruff ruff format services/users/app --config services/users/pyproject.toml

#Pre-commit
echo "Running pre-commit..."
uv run --with pre-commit pre-commit run --all-files --verbose
