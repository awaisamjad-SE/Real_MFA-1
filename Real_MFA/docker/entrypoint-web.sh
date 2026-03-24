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


def parse_port(env_name: str, default: str) -> int:
  value = os.getenv(env_name, default)
  try:
    return int(value)
  except (TypeError, ValueError):
    raise RuntimeError(
      f"Invalid {env_name}={value!r}. Set a numeric port (example: 5432 or 25060)."
    )


db_host = os.getenv("DB_HOST", "db")
db_port = parse_port("DB_PORT", "5432")
redis_host = os.getenv("REDIS_HOST", "redis")
redis_port = parse_port("REDIS_PORT", "6379")

if not db_host or db_host.startswith("<"):
  raise RuntimeError(
    f"Invalid DB_HOST={db_host!r}. For Docker Compose use 'db'. For managed DB use the provider hostname."
  )

if not redis_host or redis_host.startswith("<"):
  raise RuntimeError(
    f"Invalid REDIS_HOST={redis_host!r}. For Docker Compose use 'redis'. For managed Redis use the provider hostname."
  )

print(f"Using DB endpoint: {db_host}:{db_port}")
print(f"Using Redis endpoint: {redis_host}:{redis_port}")

wait_for_service("postgres", db_host, db_port)
wait_for_service("redis", redis_host, redis_port)
PY

echo "Applying migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

echo "Starting application process..."
exec "$@"
