import os

from django.conf import settings
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


def get_database_url() -> str:
    return getattr(
        settings,
        "SQLALCHEMY_DATABASE_URI",
        os.environ.get("SQLALCHEMY_DATABASE_URI", ""),
    )


engine = create_engine(
    get_database_url(),
    echo=getattr(settings, "SQLALCHEMY_ECHO", False),
    future=True,
)

SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
