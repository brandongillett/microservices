#!/usr/bin/env bash

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No color (reset)

#Libs
echo -e "${CYAN}Formatting libs...${NC}"
uv run --with ruff==0.7.1 ruff check libs --config services/auth/pyproject.toml --fix
uv run --with ruff==0.7.1  ruff format libs --config services/auth/pyproject.toml

#Auth service
echo -e "${CYAN}Formatting auth service...${NC}"
uv run --with ruff==0.7.1 ruff check services/auth/app services/auth/scripts --config services/auth/pyproject.toml --fix
uv run --with ruff ruff format services/auth/app services/auth/scripts --config services/auth/pyproject.toml

#Users service
echo -e "${CYAN}Formatting users service...${NC}"
uv run --with ruff==0.7.1 ruff check services/users/app services/users/scripts --fix --config services/users/pyproject.toml
uv run --with ruff==0.7.1  ruff format services/users/app services/users/scripts --config services/users/pyproject.toml

#Pre-commit
echo -e "${YELLOW}Running pre-commit...${NC}"
uv run --with pre-commit pre-commit run --all-files --verbose

# Successful format message
echo ""
echo -e "${GREEN}--------------------------------${NC}"
echo -e "${GREEN}Formatting completed successfully!${NC}"
echo -e "${GREEN}--------------------------------${NC}"
