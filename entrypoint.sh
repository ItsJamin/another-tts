#!/bin/sh
# entrypoint.sh
# Ensure /app/.env exists before starting the app

if [ ! -f /app/.env ]; then
    echo "Creating default .env from .env.example"
    cp /app/.env.example /app/.env
fi

# Execute the container's CMD
exec "$@"
