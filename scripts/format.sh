#!/usr/bin/env bash

set -e

#Auth service
echo "Formatting auth service..."
uv run --with ruff ruff check services/auth/app --fix
uv run --with ruff ruff format services/auth/app

#Users service
echo "Formatting users service..."
uv run --with ruff ruff check services/users/app --fix
uv run --with ruff ruff format services/users/app

#Pre-commit
echo "Running pre-commit..."
uv run --with pre-commit pre-commit run --all-files --verbose
