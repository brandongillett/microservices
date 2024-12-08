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

# Run tests for auth-service
echo -e "${CYAN}Running tests for auth-service...${NC}"
docker compose exec -t auth-service bash scripts/tests-start.sh "$@"

# Run tests for users-service
echo -e "${CYAN}Running tests for users-service...${NC}"
docker compose exec -t users-service bash scripts/tests-start.sh "$@"

# Tear down the containers after the tests
echo -e "${RED}Tearing down containers...${NC}"
docker compose exec -t users-service bash scripts/tests-start.sh "$@"
docker compose down -v --remove-orphans > /dev/null 2>&1

# Successful tests message
echo -e ""
echo -e "${GREEN}--------------------------------${NC}"
echo -e "${GREEN}All tests passed successfully!${NC}"
echo -e "${GREEN}--------------------------------${NC}"
