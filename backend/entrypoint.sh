#!/bin/sh
# Apply pending Alembic migrations, then start the API.
# Running migrations here keeps the schema in step with the image that is deployed.
set -eu

echo "[entrypoint] applying database migrations"
alembic upgrade head

echo "[entrypoint] starting uvicorn on :${PORT:-8000}"
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers "${WEB_CONCURRENCY:-2}"
