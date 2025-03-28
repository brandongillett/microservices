#! /usr/bin/env bash

# Check if redis and mysql are up
python src/backend_pre_start.py

# Run migrations
alembic upgrade head
