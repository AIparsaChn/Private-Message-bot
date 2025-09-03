import asyncio

from typing import Union
from redis.asyncio import Redis


class RedisDatabase():
    GROUP_CHAT_ID_KEY = "groups:chat_id"
    _pool = None

    @classmethod
    async def _connect(cls):
        if cls._pool is None:
            cls._pool = await Redis.from_url(
                url="redis://localhost:6379/0",
                decode_responses=True
            )
        return cls._pool

    @classmethod
    async def add_chat_id(cls, chat_id: Union[str, int]):
        connection: Redis = await cls._connect()
        if isinstance(chat_id, int):
            chat_id = str(chat_id)
        await connection.sadd(cls.GROUP_CHAT_ID_KEY, chat_id)
        return None






