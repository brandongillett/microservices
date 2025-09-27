#!/usr/bin/env bash

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No color (reset)

# Format libs
echo -e "${CYAN}Formatting libs...${NC}"
uv run --with ruff==0.7.1 ruff check libs --config services/auth/pyproject.toml --fix
uv run --with ruff==0.7.1 ruff format libs --config services/auth/pyproject.toml

# Function to format a service
format_service() {
    local service_path="$1"
    local service_name=$(basename "$service_path")

    echo -e "${CYAN}Formatting $service_name service...${NC}"

    # Check if required folders exist
    if [ -d "$service_path/src" ] && [ -d "$service_path/scripts" ]; then
        uv run --with ruff==0.7.1 ruff check "$service_path/src" "$service_path/scripts" --config "$service_path/pyproject.toml" --fix
        uv run --with ruff==0.7.1 ruff format "$service_path/src" "$service_path/scripts" --config "$service_path/pyproject.toml"
    else
        echo -e "${RED}Warning: Missing src or scripts folder in $service_name service. Skipping...${NC}"
    fi
}

# Iterate through services
for service_dir in services/*/; do
    if [ -f "$service_dir/pyproject.toml" ]; then
        format_service "$service_dir"
    else
        echo -e "${YELLOW}Skipping $service_dir: pyproject.toml not found${NC}"
    fi

done

# Pre-commit
echo -e "${YELLOW}Running pre-commit...${NC}"
if ! uv run --with pre-commit pre-commit run --all-files --verbose; then
    echo -e "${YELLOW}Running pre=commit once more...${NC}"
    uv run --with pre-commit pre-commit run --all-files --verbose
fi

# Successful format message
echo ""
echo -e "${GREEN}--------------------------------${NC}"
echo -e "${GREEN}Formatting completed successfully!${NC}"
echo -e "${GREEN}--------------------------------${NC}"
