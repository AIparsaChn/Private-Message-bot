import os
from typing import Optional

from telebot.async_telebot import logger

from sqlalchemy import create_engine, URL, INTEGER
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped

class Base(DeclarativeBase):
    pass

class GroupInformation(Base):
    __tablename__ = "groups"

    chat_id: Mapped[int] = mapped_column(
        INTEGER, primary_key=True,
        nullable=False, unique=True)

    username: Mapped[Optional[str]]
    chat_type: Mapped[str]
    title: Mapped[Optional[str]]
    description: Mapped[Optional[str]]
    is_forum: Mapped[bool]
    bio: Mapped[Optional[str]]
    date_membership: Mapped[str]
    json_photos: Mapped[str]


def create_database_and_table() -> None:
    """Create a database and the tables from Base class."""

    database_name = "bot_database.db"
    database_exists = os.path.exists(database_name)

    url = URL.create(drivername="sqlite", database=database_name)
    engine = create_engine(url)
    Base.metadata.create_all(engine)

    if database_exists:
        logger.info(f"Database {database_name} already exists.")
    else:
        logger.info(f"New database {database_name} and tables created.")

    return None



