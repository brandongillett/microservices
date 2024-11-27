#!/usr/bin/env sh

set -e

# Building Docker images
echo "Building Docker images..."
docker compose build > /dev/null 2>&1

# Shut down any existing containers and remove orphaned containers/volumes
echo "Shutting down existing containers and removing orphaned volumes..."
docker compose down -v --remove-orphans > /dev/null 2>&1

# Start the containers
echo "Starting Docker containers..."
docker compose up -d > /dev/null 2>&1

# Run tests for auth-service
echo "Running tests for auth-service..."
docker compose exec -T auth-service bash scripts/tests-start.sh "$@"

# Run tests for users-service
echo "Running tests for users-service..."
docker compose exec -T users-service bash scripts/tests-start.sh "$@"

# Tear down the containers after the tests
echo "Tearing down containers..."
docker compose down -v --remove-orphans > /dev/null 2>&1

# Successful tests message
echo ""
echo "--------------------------------"
echo "All tests passed successfully!"
echo "--------------------------------"
