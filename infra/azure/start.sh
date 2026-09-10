#!/usr/bin/env bash
set -euo pipefail
python -m flask --app backend init-db
exec gunicorn wsgi:app --bind 0.0.0.0:8000 --workers 1 --threads 4 --timeout 120 --access-logfile - --error-logfile -
