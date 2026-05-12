from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine


def apply_schema_upgrades(engine: Engine) -> None:
    inspector = inspect(engine)
    if "comments" not in inspector.get_table_names():
        return

    comment_columns = {column["name"] for column in inspector.get_columns("comments")}
    if "parent_id" in comment_columns:
        return

    with engine.begin() as connection:
        connection.execute(text("ALTER TABLE comments ADD COLUMN parent_id INTEGER"))
