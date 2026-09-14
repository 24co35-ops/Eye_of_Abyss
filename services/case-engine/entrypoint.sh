#!/bin/sh
# Run Alembic migrations then start uvicorn.
# Used as Docker entrypoint for case-engine.
set -e
cd /app
alembic -c alembic.ini upgrade head
exec uvicorn main:app --host 0.0.0.0 --port 8000
