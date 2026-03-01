#!/bin/sh
set -e

# Run database migrations if this is the API service
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    echo "[entrypoint] Running Alembic migrations..."
    python -m alembic upgrade head
    echo "[entrypoint] Migrations complete."
fi

# Execute the main command (uvicorn, celery, streamlit, etc.)
exec "$@"
