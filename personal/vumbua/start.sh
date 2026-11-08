#!/bin/sh
set -eu

exec gunicorn --bind "0.0.0.0:${PORT:-8000}" --config gunicorn.conf.py wsgi:app
