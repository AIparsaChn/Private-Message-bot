import os
from typing import Optional

from telebot.async_telebot import logger
from sqlalchemy import create_engine, URL, INTEGER
from sqlalchemy.orm import DeclarativeBase, mapped_column, Mapped, sessionmaker
from sqlalchemy.orm.session import Session as Se

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
    is_forum: Mapped[Optional[bool]]
    bio: Mapped[Optional[str]]
    date_membership: Mapped[str]
    json_photos: Mapped[Optional[str]]

DATABASE_NAME = "bot_database.db"
url = URL.create(drivername="sqlite", database=DATABASE_NAME)
engine = create_engine(url)
Session = sessionmaker(bind=engine)


def create_database_and_table() -> None:
    """Create a database and the tables from Base class."""
    try:
        database_exists = os.path.exists(DATABASE_NAME)
        Base.metadata.create_all(engine)

        if database_exists:
            logger.info(f"Database {DATABASE_NAME} already exists.")
        else:
            logger.info(f"New database {DATABASE_NAME} and tables created.")

        return None
    except Exception as ex:
        logger.error("An error occured.", exc_info=True)


def store_group_info(chat_id: int, username: str, chat_type: str,
        title: str, description: str, is_forum: bool,
        bio: str, date_membership: str, json_photos: str) -> None:
    try:
        session: Se
        with Session() as session:
            row = GroupInformation(
                chat_id=chat_id,
                username=username,
                chat_type=chat_type,
                title=title,
                description=description,
                is_forum=is_forum,
                bio=bio,
                date_membership=date_membership,
                json_photos=json_photos,
            )
            session.add(row)
            session.commit()
    except Exception as ex:
        logger.error("An error occured.", exc_info=True)


def get_group_title(group_chat_id: str) -> str:
    session: Se
    with Session() as session:
        group_info = session.query(GroupInformation)
        group_title = group_info.filter(GroupInformation.chat_id == group_chat_id).first().title
    return group_title


def get_group_username(group_chat_id: str) -> str:
    session: Se
    with Session() as session:
        group_info = session.query(GroupInformation)
        group_username = group_info.filter(GroupInformation.chat_id == group_chat_id).first().username
    return group_username

