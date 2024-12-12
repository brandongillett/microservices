#!/usr/bin/env sh

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
CYAN='\033[0;36m'
RED='\033[0;31m'
NC='\033[0m' # No color (reset)

# Building Docker images
echo -e "${CYAN}Building Docker images...${NC}"
docker compose build > /dev/null 2>&1

# Start the containers
echo -e "${GREEN}Starting Docker containers...${NC}"
docker compose up -d > /dev/null 2>&1

# Function to run linter for services
run_linter() {
    local service_name="$1"
    echo -e "${CYAN}Running linter for $service_name...${NC}"
    docker compose exec -t "$service_name" bash scripts/lint.sh "$@"
}

# Identify and lint all services
for service_dir in services/*/; do
    service_name=$(basename "$service_dir")-service
    if [ -f "$service_dir/scripts/lint.sh" ]; then
        run_linter "$service_name"
    else
        echo -e "${YELLOW}Skipping $service_name: lint.sh not found${NC}"
    fi
done

# Tear down the containers after the linting
echo -e "${RED}Tearing down containers...${NC}"
docker compose down > /dev/null 2>&1

# Successful linter message
echo ""
echo -e "${GREEN}--------------------------------${NC}"
echo -e "${GREEN}Linter completed successfully!${NC}"
echo -e "${GREEN}--------------------------------${NC}"
