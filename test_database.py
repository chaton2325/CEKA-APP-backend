from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError

from config import Config
from database.session import engine
from models import Base, load_models


def main() -> int:
    print("Testing database connection from .env")
    print(f"DATABASE_URL={_hide_password(Config.DATABASE_URL)}")

    try:
        load_models()

        with engine.begin() as connection:
            Base.metadata.create_all(bind=connection)
            tables = inspect(connection).get_table_names()

        print("Database connection: OK")
        print("Models synchronization: OK")
        print(f"Detected tables: {', '.join(tables) if tables else 'none'}")
        return 0
    except SQLAlchemyError as exc:
        print("Database test failed")
        print(f"{exc.__class__.__name__}: {exc}")
        return 1


def _hide_password(database_url: str) -> str:
    if "://" not in database_url or "@" not in database_url:
        return database_url

    scheme, rest = database_url.split("://", 1)
    credentials, host = rest.split("@", 1)
    if ":" not in credentials:
        return database_url

    username, _password = credentials.split(":", 1)
    return f"{scheme}://{username}:***@{host}"


if __name__ == "__main__":
    raise SystemExit(main())
