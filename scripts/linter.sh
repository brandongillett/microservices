#!/usr/bin/env sh

set -e

# Building Docker images
echo "Building Docker images..."
docker compose build > /dev/null 2>&1

# Start the containers
echo "Starting Docker containers..."
docker compose up -d > /dev/null 2>&1

# Run linter for auth-service
echo "Running linter for auth-service..."
docker compose exec -T auth-service bash scripts/lint.sh "$@"

# Run linter for users-service
echo "Running linter for users-service..."
docker compose exec -T users-service bash scripts/lint.sh "$@"

# Tear down the containers after the linting
echo "Tearing down containers..."
docker compose down > /dev/null 2>&1

# Successful linter message
echo ""
echo "--------------------------------"
echo "Linter completed successfully!"
echo "--------------------------------"
