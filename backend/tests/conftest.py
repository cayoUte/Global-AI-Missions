"""Shared test configuration. Test-only environment defaults; never real secrets."""

import os

os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://gam:gam@127.0.0.1:5433/gam_test")
os.environ.setdefault("JWT_SECRET", "test-only-secret-not-for-production-0123456789")
os.environ.setdefault("COACH_PROVIDER", "mock")
os.environ.setdefault("DEMO_MODE", "true")
