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

# Shut down any existing containers and remove orphaned containers/volumes
echo -e "${YELLOW}Shutting down existing containers and removing orphaned volumes...${NC}"
docker compose down -v --remove-orphans > /dev/null 2>&1

# Start the containers
echo -e "${GREEN}Starting Docker containers...${NC}"
docker compose up -d > /dev/null 2>&1

# Function to run tests for services
run_tests() {
    local service_name="$1"
    echo -e "${CYAN}Running tests for $service_name...${NC}"
    docker compose exec -t "$service_name" bash scripts/run-tests.sh "$@"
}

# Identify and test all services
for service_dir in services/*/; do
    service_name=$(basename "$service_dir")
    if [ -f "$service_dir/scripts/run-tests.sh" ]; then
        run_tests "$service_name"
    else
        echo -e "${YELLOW}Skipping $service_name: run-tests.sh not found${NC}"
    fi
done

# Tear down the containers after the tests
echo -e "${RED}Tearing down containers...${NC}"
docker compose down -v --remove-orphans > /dev/null 2>&1

# Successful tests message
echo -e ""
echo -e "${GREEN}--------------------------------${NC}"
echo -e "${GREEN}All tests passed successfully!${NC}"
echo -e "${GREEN}--------------------------------${NC}"
