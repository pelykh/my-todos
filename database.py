from sqlalchemy import create_engine, make_url
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from config import get_settings

settings = get_settings()

_dialect = make_url(settings.database_url).get_dialect().name
connect_args = {"check_same_thread": False} if _dialect == "sqlite" else {}
engine = create_engine(settings.database_url, connect_args=connect_args)
SessionLocal = sessionmaker(engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_db():
    db: Session = SessionLocal()
    try:
        yield db
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
