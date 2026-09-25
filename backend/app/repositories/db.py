"""Engine and session factory. The API's get_session dependency and the seed both use these."""

from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings


@lru_cache
def get_engine() -> Engine:
    # pool_pre_ping: survive a database restart without a 500 on the first request.
    return create_engine(get_settings().database_url, pool_pre_ping=True)


@lru_cache
def get_sessionmaker() -> sessionmaker[Session]:
    # expire_on_commit=False: services read attributes after the commit (two-phase submit).
    return sessionmaker(bind=get_engine(), expire_on_commit=False)
