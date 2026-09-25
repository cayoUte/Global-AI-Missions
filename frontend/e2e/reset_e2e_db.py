"""Recreate the E2E database from scratch (run by serve.sh with the backend's uv environment).

The E2E suite never touches the demo database `gam`: it drops and recreates the database named
in DATABASE_URL (it must end in `_e2e`), then serve.sh migrates and seeds it.
"""

import os
import sys

import psycopg

url = os.environ["DATABASE_URL"].replace("postgresql+psycopg://", "postgresql://")
base, name = url.rsplit("/", 1)
if not name.endswith("_e2e"):
    sys.exit(f"refusing to reset {name!r}: the E2E database name must end in _e2e")

with psycopg.connect(f"{base}/postgres", autocommit=True, connect_timeout=5) as conn:
    conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')
    conn.execute(f'CREATE DATABASE "{name}"')
print(f"e2e: recreated database {name}")
