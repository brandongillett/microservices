#! /usr/bin/env bash

# Initialize and test connections
python src/prestart.py

# Run migrations
alembic upgrade head
