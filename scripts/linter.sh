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

# Run linter for auth-service
echo -e "${CYAN}Running linter for auth-service...${NC}"
docker compose exec -t auth-service bash scripts/lint.sh "$@"

# Run linter for users-service
echo -e "${CYAN}Running linter for users-service...${NC}"
docker compose exec -t users-service bash scripts/lint.sh "$@"

# Tear down the containers after the linting
echo -e "${RED}Tearing down containers...${NC}"
docker compose down > /dev/null 2>&1

# Successful linter message
echo ""
echo -e "${GREEN}--------------------------------${NC}"
echo -e "${GREEN}Linter completed successfully!${NC}"
echo -e "${GREEN}--------------------------------${NC}"
