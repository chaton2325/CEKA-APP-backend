from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

from config import Config
from models import Base, load_models
from database.schema_upgrades import apply_schema_upgrades


engine = create_engine(Config.DATABASE_URL, echo=False, future=True)
SessionLocal = scoped_session(
    sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
)


def init_database() -> None:
    load_models()
    Base.metadata.create_all(bind=engine)
    apply_schema_upgrades(engine)


def get_db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
