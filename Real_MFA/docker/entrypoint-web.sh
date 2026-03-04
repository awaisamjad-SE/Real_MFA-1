#!/bin/sh
set -e

echo "Waiting for database and redis..."
python - << 'PY'
import os
import socket
import time


def wait_for_service(name: str, host: str, port: int, timeout: int = 90) -> None:
  start = time.time()
  while True:
    try:
      with socket.create_connection((host, port), timeout=2):
        print(f"{name} is ready at {host}:{port}")
        return
    except OSError:
      if time.time() - start > timeout:
        raise RuntimeError(f"Timeout waiting for {name} at {host}:{port}")
      time.sleep(2)


db_host = os.getenv("DB_HOST", "db")
db_port = int(os.getenv("DB_PORT", "5432"))
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = int(os.getenv("REDIS_PORT", "6379"))

wait_for_service("postgres", db_host, db_port)
wait_for_service("redis", redis_host, redis_port)
PY

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application process..."
exec "$@"
