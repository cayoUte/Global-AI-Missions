"""Engine and session factory. The API's get_session dependency and the seed both use these."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings

CONNECT_TIMEOUT_SECONDS = 5


@lru_cache
def get_engine() -> Engine:
    # pool_pre_ping: survive a database restart without a 500 on the first request.
    # connect_timeout: never hang on an unreachable address (e.g. "localhost" resolving to an
    # IPv6 ::1 that stalls): fail over to the next address, or fail fast.
    return create_engine(
        get_settings().database_url,
        pool_pre_ping=True,
        connect_args={"connect_timeout": CONNECT_TIMEOUT_SECONDS},
    )


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    # expire_on_commit=False: services read attributes after the commit (two-phase submit).
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
