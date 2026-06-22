#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

cd /app/projects/phiphi/

# Run alembic migrations
alembic upgrade heads

# Seed the database
python phiphi/seed/main.py

# Important to move back to working directory
cd -

exec $@
